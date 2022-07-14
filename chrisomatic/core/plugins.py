import enum
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Sequence, Optional, Collection, Callable, Awaitable, Type

import aiodocker
import aiohttp

from rich.text import Text
from chris.common.deserialization import Plugin
from chris.common.search import to_sequence
from chris.common.types import PluginUrl, PluginName, ImageTag, ChrisUsername
from chris.common.errors import ResponseError, BadRequestError
from chris.common.client import AbstractClient, P
from chris.cube.client import CubeClient
from chris.cube.deserialization import CubePlugin
from chris.cube.types import ComputeResourceName
from chris.store.client import AbstractChrisStoreClient, ChrisStoreClient
from chrisomatic.core.docker import (
    check_output,
    get_cmd,
    rich_pull_if_missing,
    PullResult,
    NonZeroExitCodeError,
)
from chrisomatic.core.omniclient import OmniClient
from chrisomatic.framework.task import ChrisomaticTask, State, Outcome
from chrisomatic.framework.taskrunner import TableTaskRunner
from chrisomatic.spec.given import GivenCubePlugin
from chrisomatic.core.helpers import RetryWrapper, R


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
    plugin: Optional[CubePlugin]
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
        errors, registrations = await self.__register_to(
            plugin_in_store, compute_envs, emit
        )
        result = PluginRegistration(
            plugin=registrations[0] if registrations else None,
            from_url=plugin_in_store.url,
            origin=origin,
        )
        outcome = Outcome.NO_CHANGE
        if result.plugin is not None:
            emit.status = result.plugin.url
            outcome = Outcome.CHANGE
        if len(errors) > 0:
            emit.status = str(errors)
            outcome = Outcome.FAILED

        return outcome, result

    # async def __register_to_parallel(self,
    #                                  plugin_in_store: Plugin,
    #                                  compute_envs: Collection[ComputeResourceName],
    #                                  emit: State
    #                                  ) -> tuple[list[ResponseError], list[CubePlugin]]:
    #     """
    #     NB: do not register same plugin to different compute resources in parallel
    #     https://github.com/FNNDSC/ChRIS_ultron_backEnd/issues/366
    #     """
    #     registration_attempts: tuple[BaseException | CubePlugin, ...] = await asyncio.gather(*(
    #         # self.cube.register_plugin(plugin_store_url=plugin_in_store.url,
    #         #                           compute_name=compute_resource_name)
    #         self.__register_plugin(plugin_in_store.url, compute_resource_name, emit)
    #         for compute_resource_name in compute_envs
    #     ), return_exceptions=True)
    #     errors = [e for e in registration_attempts if isinstance(e, ResponseError)]
    #     registrations = [e for e in registration_attempts if isinstance(e, CubePlugin)]
    #     return errors, registrations

    async def __register_to(
        self,
        plugin_in_store: Plugin,
        compute_envs: Collection[ComputeResourceName],
        emit: State,
    ) -> tuple[list[BaseException], list[CubePlugin]]:
        """
        Register a plugin from a *ChRIS* store to some compute environments by name.

        `compute_envs` is assumed to have at least one member.
        """
        registrations: list[CubePlugin] = []
        errors: list[BaseException] = []
        for compute_resource_name in compute_envs:
            emit.status = f'--> "{compute_resource_name}"'
            try:
                registered = await self.__register_plugin(
                    plugin_in_store.url, compute_resource_name, emit
                )
                registrations.append(registered)
            except BaseException as e:
                errors.append(e)
        return errors, registrations

    async def __register_plugin(
        self,
        plugin_store_url: PluginUrl,
        compute_name: ComputeResourceName,
        emit: State,
    ) -> CubePlugin:
        """
        Register a plugin to CUBE, retrying if a `ServerDisconnectedError` or `BadRequestError` occurs.
        """

        async def register_plugin() -> CubePlugin:
            return await self.cube.register_plugin(
                plugin_store_url=plugin_store_url, compute_name=compute_name
            )

        return await _RetryOnPluginUpload(register_plugin).call(emit)

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
        existing_plugin: CubePlugin = await self.__get_first_plugin(
            self.cube, query, emit
        )
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
        try:
            found_in_store, origin = await self._find_in_store(emit)
            if found_in_store:
                emit.status = f"found --> {found_in_store.url}"
                return found_in_store, origin
            emit.status = Text("not found", style="bold red")
            uploaded_plugin = await self._upload_to_store(emit)
            return uploaded_plugin, PluginOrigin.local_store
        except aiohttp.ClientError as e:
            emit.status = Text(str(e), style="red")
            return None, None

    async def _find_in_store(
        self, emit: State
    ) -> tuple[Optional[Plugin], Optional[PluginOrigin]]:
        query = self.plugin.to_store_search()
        emit.status = f"searching in {self.linked_store.url}..."
        result = await self.__get_first_plugin(self.linked_store, query, emit)
        if result is not None:
            return result, PluginOrigin.local_store

        for client in self.other_stores:
            emit.status = f"searching in {client.url}..."
            result = await self.__get_first_plugin(client, query, emit)
            if result is not None:
                return result, PluginOrigin.public_store
        return None, None

    @staticmethod
    async def __get_first_plugin(
        client: AbstractClient[Type, P], query: dict[str, str], emit: State
    ) -> P:
        """
        Wraps `client.get_first_plugin` with `_RetryOnDisconnect`.
        """

        async def get_first_plugin():
            return await client.get_first_plugin(**query)

        return await _RetryOnDisconnect[P](get_first_plugin).call(emit)

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
        pull_result = await rich_pull_if_missing(
            self.docker, self.plugin.dock_image, emit
        )
        if pull_result == PullResult.error:
            return None
        if pull_result == PullResult.pulled:
            emit.append = True
        guessing_methods: list[Callable[[State], Awaitable[Optional[str]]]] = [
            self._json_from_chris_plugin_info,
            self._json_from_old_chrisapp,
        ]
        for guess_method in guessing_methods:
            json_representation = await guess_method(emit)
            emit.append = False
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
        msg = Text("Running ")
        msg.append(" ".join(command), style="yellow")
        emit.status = msg
        try:
            return await check_output(self.docker, self.plugin.dock_image, command)
        except aiodocker.DockerContainerError:
            return None
        except NonZeroExitCodeError:
            return None

    @property
    def _all_stores(self) -> list[AbstractChrisStoreClient]:
        return [self.linked_store, *self.other_stores]


class _RetryOnDisconnect(RetryWrapper[R]):
    """
    IDK why these things happen:

        aiohttp.client_exceptions.ClientOSError: [Errno 1] [SSL: APPLICATION_DATA_AFTER_CLOSE_NOTIFY]
        application data after close notify (_ssl.c:2660)

        aiohttp.client_exceptions.ServerDisconnectedError: Server disconnected

    """

    def check_exception(self, e: BaseException) -> bool:
        return isinstance(e, (aiohttp.ServerDisconnectedError, aiohttp.ClientOSError))


class _RetryOnPluginUpload(_RetryOnDisconnect[CubePlugin]):
    def check_exception(self, e: BaseException) -> bool:
        if super().check_exception(e):
            return True
        if not isinstance(e, BadRequestError):
            return False
        return e.args[0] == 400

    @property
    def explanation(self) -> str:
        return (
            "This error might be expected. See "
            "https://github.com/FNNDSC/ChRIS_ultron_backEnd/issues/366"
        )


async def register_plugins(
    omniclient: OmniClient,
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
                other_stores=omniclient.public_stores,
                docker=omniclient.docker,
                cube=omniclient.cube,
            )
            for p in plugins
        ]
    )
    return await runner.apply()
