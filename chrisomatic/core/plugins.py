import asyncio
import enum
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Sequence, Optional, Collection, Callable, Awaitable

import aiodocker

from rich.text import Text
from chris.common.deserialization import Plugin
from chris.common.search import to_sequence
from chris.common.types import PluginUrl, PluginName, ImageTag, ChrisUsername
from chris.common.errors import ResponseError
from chris.cube.client import CubeClient
from chris.cube.deserialization import CubePlugin
from chris.cube.types import ComputeResourceName
from chris.store.client import AbstractChrisStoreClient, ChrisStoreClient
from chrisomatic.core.docker import check_output, get_cmd
from chrisomatic.core.superclient import SuperClient
from chrisomatic.framework.task import ChrisomaticTask, State, Outcome
from chrisomatic.framework.taskrunner import TableTaskRunner
from chrisomatic.spec.given import GivenCubePlugin


@dataclass(frozen=True)
class InferredPluginInfo:
    name: PluginName
    dock_image: ImageTag
    public_repo: str

    @classmethod
    def from_given(cls, p: GivenCubePlugin) -> "InferredPluginInfo":
        if not p.dock_image:
            raise ValueError(p, "dock_image cannot be empty")
        base_repo = p.dock_image
        colon = base_repo.rfind(":")
        if colon != -1:
            base_repo = base_repo[:colon]
        name = base_repo
        slash = base_repo.rfind("/")
        if slash:
            name = base_repo[slash + 1 :]
            another_slash = base_repo[: slash - 1].rfind("/")
            if another_slash != -1:
                base_repo = base_repo[another_slash + 1 :]
        return cls(
            name=p.name if p.name else PluginName(name),
            dock_image=p.dock_image,
            public_repo=p.public_repo
            if p.public_repo
            else f"https://github.com/{base_repo}",
        )


class PluginOrigin(enum.Enum):
    local_store = "store.local"
    public_store = "store.public"
    docker_chris_plugin_info = "docker.chris_plugin_info"
    docker_old_chrisapp = "docker.chrisapp"


@dataclass(frozen=True)
class PluginRegistration:
    plugin: CubePlugin
    """Plugin object from CUBE"""
    from_url: Optional[PluginUrl]
    """The ChRIS store URL which this plugin is from."""
    origin: Optional[PluginOrigin]
    """Where the plugin came from"""


@dataclass(frozen=True)
class RegisterPluginTask(ChrisomaticTask[PluginRegistration]):
    """
    Try to find the given plugin in a *ChRIS* store. If that doesn't work,
    then attempt to produce the JSON representation and upload it to the
    ChRIS store first.
    """

    plugin: GivenCubePlugin
    linked_store: Optional[ChrisStoreClient]
    other_stores: Sequence[AbstractChrisStoreClient]
    docker: aiodocker.Docker
    cube: CubeClient

    def initial_state(self) -> State:
        return State(title=self.plugin.title, status="checking compute resources...")

    async def run(self, emit: State) -> tuple[Outcome, Optional[PluginRegistration]]:

        # check where the plugin was already registered
        existing_plugin, compute_envs = await self._already_present(emit)
        if existing_plugin is not None:
            emit.title = existing_plugin.name
        if len(compute_envs) == 0:
            emit.status = existing_plugin.url
            return Outcome.NO_CHANGE, PluginRegistration(
                plugin=existing_plugin, from_url=None, origin=None
            )

        # find the plugin in a ChRIS store, or attempt to upload it
        plugin_in_store, origin = await self._find_in_stores_else_upload(emit)
        if plugin_in_store is None:
            return Outcome.FAILED, None
        emit.title = plugin_in_store.name

        # register to all
        # NB: do not register same plugin to different compute resources in parallel
        # https://github.com/FNNDSC/ChRIS_ultron_backEnd/issues/366
        # registrations: tuple[CubePlugin, ...] = await asyncio.gather(*(
        #     self.cube.register_plugin(plugin_store_url=plugin_in_store.url,
        #                               compute_name=compute_resource_name)
        #     for compute_resource_name in compute_envs
        # ), return_exceptions=True)
        # exceptions = [e for e in registrations if isinstance(e, BaseException)]
        # if len(exceptions) != 0:
        #     emit.status = f'failures: {exceptions}'
        #     return Outcome.FAILED, None
        #
        # emit.status = registrations[0].url
        # return Outcome.CHANGE, PluginRegistration(
        #     plugin=registrations[0],
        #     from_url=plugin_in_store.url,
        #     origin=origin
        # )
        registrations: list[CubePlugin] = []
        errors: list[ResponseError] = []
        for compute_resource_name in compute_envs:
            emit.status = f'--> "{compute_resource_name}"'
            try:
                registered = await self.cube.register_plugin(
                    plugin_store_url=plugin_in_store.url,
                    compute_name=compute_resource_name,
                )
                registrations.append(registered)
            except ResponseError as e:
                errors.append(e)
        if len(errors) > 0:
            emit.status = str(errors)
            return Outcome.FAILED, None
        emit.status = registrations[0].url
        return Outcome.CHANGE, PluginRegistration(
            plugin=registrations[0], from_url=plugin_in_store.url, origin=origin
        )

    async def _already_present(
        self, emit: State
    ) -> tuple[Optional[CubePlugin], Collection[ComputeResourceName]]:
        """
        If the plugin is already registered to CUBE, return its representation in CUBE and the
        compute resources which are requested for the plugin to be registered to but _not_ yet
        registered to. For example, if `self.plugin` describes `pl-simpledsapp` and asks that
        it be registered to three compute environments `host`, `moc`, and `hpc`, and
        `pl-simpledsapp` already exists in CUBE but is only registered to `moc`, return the
        `CubePlugin` representing `pl-simpledsapp` and a `set[ComputeResourceName]` containing
        `{'host', 'hpc'}`.

        In the more typical case where the plugin does not already exist in CUBE, `None` and the
        list of requested compute resources from `self.plugin` are returned.
        """
        query = self.plugin.to_search_params()
        existing_plugin = await self.cube.get_first_plugin(**query)
        if existing_plugin is None:
            # plugin not registered, so need to register to all compute envs
            return None, self.plugin.compute_resource
        current_computes = set(
            c.name
            for c in await to_sequence(
                self.cube.get_compute_resources_of(existing_plugin)
            )
        )
        wanted_computes = set(self.plugin.compute_resource)
        remaining_computes = wanted_computes - current_computes
        # emit.status = f'already registered to {current_computes}, missing from {remaining_computes}'
        return existing_plugin, remaining_computes

    async def _find_in_stores_else_upload(
        self, emit: State
    ) -> tuple[Optional[Plugin], Optional[PluginOrigin]]:
        found_in_store, origin = await self._find_in_store(emit)
        if found_in_store:
            emit.status = f"found --> {found_in_store.url}"
            return found_in_store, origin
        emit.status = Text("not found", style="bold red")
        uploaded_plugin = await self._upload_to_store(emit)
        return uploaded_plugin, PluginOrigin.local_store

    async def _find_in_store(
        self, emit: State
    ) -> tuple[Optional[Plugin], Optional[PluginOrigin]]:
        query = self.plugin.to_store_search()
        emit.status = f"searching in {self.linked_store.url}..."
        result = await self.linked_store.get_first_plugin(**query)
        if result is not None:
            return result, PluginOrigin.local_store

        for client in self.other_stores:
            emit.status = f"searching in {client.url}..."
            result = await client.get_first_plugin(**query)
            if result is not None:
                return result, PluginOrigin.public_store
        return None, None

    async def _upload_to_store(self, emit: State) -> Optional[Plugin]:
        if self.linked_store is None:
            emit.status = Text(
                f'No client for owner "{self.plugin.owner}"', style="bold red"
            )
            return None
        json_representation = await self._get_json_representation(emit)
        if json_representation is None:
            return None
        inferred = InferredPluginInfo.from_given(self.plugin)
        with NamedTemporaryFile("w", suffix=".json") as temp:
            temp.write(json_representation)
            temp.flush()
            try:
                uploaded_plugin = await self.linked_store.upload_plugin(
                    name=inferred.name,
                    dock_image=inferred.dock_image,
                    public_repo=inferred.public_repo,
                    descriptor_file=Path(temp.name),
                )
            except ResponseError as e:
                emit.status = str(e)
                return None
        return uploaded_plugin

    async def _get_json_representation(self, emit: State) -> Optional[str]:
        if self.plugin.dock_image is None:
            return None
        emit.status = "attempting to produce JSON representation..."
        guessing_methods: list[Callable[[State], Awaitable[Optional[str]]]] = [
            self._json_from_chris_plugin_info,
            self._json_from_old_chrisapp,
        ]
        for guess_method in guessing_methods:
            json_representation = await guess_method(emit)
            if json_representation is not None:
                return json_representation
        return None

    async def _json_from_chris_plugin_info(self, emit: State) -> Optional[str]:
        return await self._try_run(emit, ("chris_plugin_info",))

    async def _json_from_old_chrisapp(self, emit: State) -> Optional[str]:
        cmd = await get_cmd(self.docker, self.plugin.dock_image)
        if len(cmd) == 0:
            return None
        return await self._try_run(emit, (cmd[0], "--json"))

    async def _try_run(self, emit: State, command: Sequence[str]) -> Optional[str]:
        emit.status = f"Running {command}"
        try:
            return await check_output(self.docker, self.plugin.dock_image, command)
        except aiodocker.DockerContainerError:
            return None

    @property
    def _all_clients(self):
        return [self.linked_store, *self.other_stores]


async def register_plugins(
    superclient: SuperClient,
    plugins: Sequence[GivenCubePlugin],
    store_clients: dict[ChrisUsername, ChrisStoreClient],
) -> Sequence[tuple[Outcome, PluginRegistration]]:
    runner = TableTaskRunner(
        tasks=[
            RegisterPluginTask(
                plugin=p,
                linked_store=(
                    store_clients[p.owner] if p.owner in store_clients else None
                ),
                other_stores=superclient.public_stores,
                docker=superclient.docker,
                cube=superclient.cube,
            )
            for p in plugins
        ]
    )
    return await runner.apply()
