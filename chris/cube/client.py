from typing import TypeVar, AsyncIterator, Sequence, Iterable
from chris.common.types import PluginUrl
from chris.common.client import AuthenticatedClient
from chris.common.search import get_paginated, to_sequence
import chris.common.decorator as http
from chris.cube.types import ComputeResourceName, PfconUrl, Feed
from chris.cube.models import CubeCollectionLinks, CubePlugin, ComputeResource

_T = TypeVar("_T")


class CubeClient(AuthenticatedClient[CubeCollectionLinks, CubePlugin, "CubeClient"]):
    @http.post("/chris-admin/api/v1/")
    async def _register_plugin_from_store_raw(
        self, plugin_store_url: PluginUrl, compute_names: str
    ) -> CubePlugin:
        ...

    async def register_plugin_from_store(
            self, plugin_store_url: PluginUrl, compute_names: Iterable[ComputeResourceName]
    ) -> CubePlugin:
        return await self._register_plugin_from_store_raw(plugin_store_url=plugin_store_url, compute_names=','.join(compute_names))

    @http.post("/chris-admin/api/v1/computeresources/")
    async def create_compute_resource(
        self,
        name: ComputeResourceName,
        compute_url: PfconUrl,
        compute_user: str,
        compute_password: str,
        description: str = "",
    ) -> ComputeResource:
        ...

    def get_feeds(self) -> AsyncIterator[Feed]:
        return get_paginated(session=self.s, url=self.url, element_type=Feed)

    def get_compute_resources_of(
        self, plugin: CubePlugin
    ) -> AsyncIterator[ComputeResource]:
        return get_paginated(
            session=self.s, url=plugin.compute_resources, element_type=ComputeResource
        )

    def search_compute_resources(
        self, max_requests=100, **query
    ) -> AsyncIterator[ComputeResource]:
        return self.search(
            url=self.collection_links.compute_resources,
            query=query,
            element_type=ComputeResource,
            max_requests=max_requests,
        )

    async def get_all_compute_resources(self) -> Sequence[ComputeResource]:
        return await to_sequence(self.search_compute_resources())
