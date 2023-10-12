import dataclasses
import enum
import json
from dataclasses import dataclass
from typing import Sequence, Optional, Collection, Self, Iterable

import aiodocker
import aiohttp
from aiochris import ChrisAdminClient, AnonChrisClient, acollect
from aiochris.client.base import BaseChrisClient
from aiochris.errors import BadRequestError, BaseClientError
from aiochris.models.logged_in import Plugin
from aiochris.models.public import PublicPlugin
from aiochris.types import PluginName, ImageTag, PluginUrl, ComputeResourceName
from rich.console import RenderableType

from chrisomatic.framework import ChrisomaticTask, Channel, Outcome
from chrisomatic.helpers.pldesc import try_obtain_json_description
from chrisomatic.helpers.retry import RetryWrapper, R
from chrisomatic.spec.given import GivenCubePlugin


@dataclass(frozen=True)
class InferredPluginInfo:
    """
    Information about a plugin relevant for plugin registration.
    """

    name: PluginName
    dock_image: ImageTag
    public_repo: str

    @classmethod
    def from_given(cls, p: GivenCubePlugin) -> Self:
        """
        Constructor of `InferredPluginInfo`.

        Information might be missing from `InferredPluginInfo`, in which case,
        an educated guess will be made.
        """
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

    def fill(self, json_representation: str) -> str:
        """
        If necessary, adds inferred values for `name`, `dock_image`, and `public_repo` to the given plugin JSON representation.

        These fields are typically missing from automatically self-generated plugin JSON representations due to
        historical reasons and technical debt.

        https://github.com/FNNDSC/CHRIS_docs/commit/5078aaf934bdbe313e85367f88aff7c14730a1d4

        This is necessary for Python-based _ChRIS_ plugins built on top of:

        - [`chris_plugin`](https://pypi.org/project/chris_plugin/) prior to [version 0.3.0](https://github.com/FNNDSC/chris_plugin/releases/tag/v0.3.0)
        - [`chrisapp`](https://github.com/FNNDSC/chrisapp)
        """
        obj = json.loads(json_representation)
        self.__set_if_missing(obj, "name", self.name)
        self.__set_if_missing(obj, "dock_image", self.dock_image)
        self.__set_if_missing(obj, "public_repo", self.public_repo)
        return obj

    @staticmethod
    def __set_if_missing(obj, key, value) -> None:
        if key not in obj:
            obj[key] = value


class PluginOrigin(enum.Enum):
    """
    Information about where a plugin comes from.
    """

    self = "self"
    local_store = "store.local"
    public_store = "store.public"
    docker_chris_plugin_info = "docker.chris_plugin_info"
    docker_old_chrisapp = "docker.chrisapp"


@dataclass(frozen=True)
class PluginRegistration:
    plugin: Optional[Plugin]
    """Plugin object from CUBE"""
    from_url: Optional[PluginUrl]
    """The peer CUBE URL which this plugin is from."""
    origin: Optional[PluginOrigin]
    """Where the plugin came from"""


@dataclass(frozen=True)
class RegisterPluginTask(ChrisomaticTask[PluginRegistration]):
    """
    1. Check if plugin already exists in CUBE.
    2. If plugin already exists, register plugin to other compute resources as needed.
    3. Search for plugin in peer CUBE instances.
    4. If plugin found in a peer instance, add from peer.
    5. Try running plugin container to obtain JSON representation and register that.
    """

    plugin: GivenCubePlugin
    other_stores: Sequence[AnonChrisClient]
    docker: Optional[aiodocker.Docker]
    cube: ChrisAdminClient

    def first_status(self) -> tuple[str, RenderableType]:
        return self.plugin.title, "checking compute resources..."

    async def run(
        self, status: Channel
    ) -> tuple[Outcome, Optional[PluginRegistration]]:
        if conclusion := await self.check_then_maybe_register_existing_plugin(status):
            return conclusion
        if conclusion := await self.find_then_maybe_register_from_peer(status):
            return conclusion
        return await self.run_and_register(status)

    async def check_then_maybe_register_existing_plugin(
        self, status: Channel
    ) -> Optional[tuple[Outcome, PluginRegistration]]:
        existing_plugin = await self.get_plugin(status)
        if existing_plugin is None:
            status.replace("To be registered.")
            return None
        return await self.register_from_self_to_others(existing_plugin, status)

    async def get_plugin(self, status: Channel) -> Optional[Plugin]:
        """Get the requested plugin from CUBE (check whether it already exists or not)."""
        q = self.plugin.to_store_search()
        status.replace(f"Searching...")
        return await self.cube.search_plugins(**q).first()

    async def register_from_self_to_others(
        self, p: Plugin, status: Channel
    ) -> tuple[Outcome, Optional[PluginRegistration]]:
        """
        Register an existing plugin to all the compute resources requested.
        """
        cr_names = await self._get_needed_compute_resources_for(p)
        if not cr_names:
            status.replace(p.url)
            return Outcome.NO_CHANGE, PluginRegistration(p, None, None)

        if (
            rp := await self._update_plugin_with_compute_resources(
                p.url, cr_names, status
            )
        ) is not None:
            status.replace(rp.url)
            return Outcome.CHANGE, PluginRegistration(rp, rp.url, None)
        return Outcome.FAILED, None

    async def _update_plugin_with_compute_resources(
        self,
        plugin_url: PluginUrl,
        cr_names: Iterable[ComputeResourceName],
        status: Channel,
    ) -> Optional[Plugin]:
        try:
            return await self.cube.register_plugin_from_store(plugin_url, cr_names)
        except BadRequestError as e:
            if (
                len(e.args) == 4
                and "Enter a valid URL." in e.args[2].get("plugin_store_url", None)
                and "localhost" not in plugin_url
                and (
                    localhost_url := self._workaround_with_localhost_as_url(plugin_url)
                )
                is not None
            ):
                return await self._update_plugin_with_compute_resources(
                    localhost_url, cr_names, status
                )
            status.replace(f"Error: {e}")
            return None

    def _workaround_with_localhost_as_url(
        self, plugin_url: PluginUrl
    ) -> Optional[PluginUrl]:
        """
        workaround: `/chris-admin/api/v1/` does not have an easy way to change the compute resources
        of an existing plugin. In this case, we use the plugin's own URL. This can fail because
        of a pointless limitation described in https://github.com/FNNDSC/ChRIS_ultron_backEnd/issues/505
        """
        front, end = plugin_url.split("api/v1/", maxsplit=1)
        if not self.cube.url.startswith(front + "api/v1/"):
            return None
        return PluginUrl("http://localhost:8000/api/v1/" + end)

    async def _get_needed_compute_resources_for(
        self, p: Plugin
    ) -> Collection[ComputeResourceName]:
        wanted = frozenset(self.plugin.compute_resource)
        current = await self._get_compute_resources_of(p)
        if wanted == current:
            return frozenset()
        return wanted

    @staticmethod
    async def _get_compute_resources_of(p: Plugin) -> frozenset[ComputeResourceName]:
        compute_resources = await acollect(p.get_compute_resources())
        return frozenset(c.name for c in compute_resources)

    async def find_then_maybe_register_from_peer(
        self, status: Channel
    ) -> Optional[tuple[Outcome, PluginRegistration]]:
        for peer in self.other_stores:
            if peer_plugin_url := await self._get_plugin_url_from(peer, status):
                return await self.register_from_peer_url(peer_plugin_url, status)
        return None

    async def _get_plugin_url_from(
        self, peer: BaseChrisClient, status: Channel
    ) -> Optional[PluginUrl]:
        status.replace(f"Searching in {peer.url}...")
        query = self.plugin.to_store_search()
        if peer_plugin := await self._get_first_plugin(peer, query, status):
            status.replace(f"Found {peer_plugin.url}")
            return peer_plugin.url
        return None

    async def register_from_peer_url(
        self, plugin_url: PluginUrl, status: Channel
    ) -> tuple[Outcome, Optional[PluginRegistration]]:
        try:
            registered_plugin = await self.cube.register_plugin_from_store(
                plugin_url, self.plugin.compute_resource
            )
            status.replace(registered_plugin.url)
            return Outcome.CHANGE, PluginRegistration(
                registered_plugin, plugin_url, PluginOrigin.public_store
            )
        except BaseClientError as e:
            status.replace(f"Error: {e}")
            return Outcome.FAILED, None

    async def run_and_register(
        self, status: Channel
    ) -> tuple[Outcome, Optional[PluginRegistration]]:
        status.replace("Trying to run something...")
        json_str = await self._get_json_representation(status)
        if json_str is None:
            return Outcome.FAILED, None
        inferred = InferredPluginInfo.from_given(self.plugin)
        plugin_dict = inferred.fill(json_str)
        try:
            registered_plugin = await self.cube.add_plugin(
                plugin_dict, self.plugin.compute_resource
            )
            status.replace(registered_plugin.url)
            return Outcome.CHANGE, PluginRegistration(
                registered_plugin, None, PluginOrigin.docker_chris_plugin_info
            )
        except BaseClientError as e:
            status.replace(f"Error: {e}")
            return Outcome.FAILED, None

    @staticmethod
    async def _get_first_plugin(
        chris: BaseChrisClient, query: dict[str, str], status: Channel
    ) -> PublicPlugin:
        """
        Wraps `client.get_first_plugin` with `_RetryOnDisconnect`.
        """

        async def get_first_plugin():
            return await chris.search_plugins(**query).first()

        return await _RetryOnDisconnect[PublicPlugin](get_first_plugin).call(status)

    async def _upload_to_store(self, status: Channel) -> Optional[Plugin]:
        ...

    async def _get_json_representation(self, status: Channel) -> Optional[str]:
        return await try_obtain_json_description(self.docker, self.plugin, status)


class _RetryOnDisconnect(RetryWrapper[R]):
    """
    IDK why these things happen:

        aiohttp.client_exceptions.ClientOSError: [Errno 1] [SSL: APPLICATION_DATA_AFTER_CLOSE_NOTIFY]
        application data after close notify (_ssl.c:2660)

        aiohttp.client_exceptions.ServerDisconnectedError: Server disconnected

    """

    def check_exception(self, e: BaseException) -> bool:
        return isinstance(e, (aiohttp.ServerDisconnectedError, aiohttp.ClientOSError))


class _RetryOnPluginUpload(_RetryOnDisconnect[PublicPlugin]):
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
