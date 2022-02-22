from functools import cached_property
from serde.json import from_json
from chris.common.types import PluginUrl
from chris.common.client import AuthenticatedClient
from chris.cube.types import ComputeResourceName
from chris.cube.deserialization import CubeCollectionLinks, CubePlugin


class CubeClient(AuthenticatedClient['CubeClient', CubeCollectionLinks], type):

    async def register_plugin(self, plugin_store_url: PluginUrl, compute_name: ComputeResourceName
                              ) -> CubePlugin:
        # links = self.collection_links
        # res = await self.s.post(self.collection_links.)
        ...
