from serde.json import from_json
from typing import Type, TypeVar, AsyncIterable
from chris.common.types import PluginUrl
from chris.common.client import AuthenticatedClient
from chris.common.search import get_paginated
import chris.common.decorator as http
from chris.cube.types import ComputeResourceName
from chris.cube.deserialization import CubeCollectionLinks, CubePlugin, ComputeResource

_T = TypeVar('_T')


class CubeClient(AuthenticatedClient[CubeCollectionLinks, 'CubeClient']):
    @http.post('/chris-admin/api/v1/')
    async def register_plugin(self, plugin_store_url: PluginUrl, compute_name: ComputeResourceName
                              ) -> CubePlugin:
        ...

    @http.post('/chris-admin/api/v1/computeresources/')
    async def create_compute_resource(self,
                                      name: ComputeResourceName,
                                      compute_url: str,
                                      compute_user: str,
                                      compute_password: str,
                                      description: str = '',
                                      ) -> ComputeResource:
        ...

    def get_compute_resources_of(self, plugin: CubePlugin) -> AsyncIterable[ComputeResource]:
        return get_paginated(
            session=self.s,
            url=plugin.compute_resources,
            element_type=ComputeResource
        )
