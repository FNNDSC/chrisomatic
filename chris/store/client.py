from pathlib import Path
from chris.store.deserialization import (
    AnonymousCollectionLinks,
    StoreCollectionLinks,
    PluginUpload
)
import aiohttp
from serde.json import from_json
from typing import TypeVar, Generic
from chris.common.client import AbstractClient, AnonymousClient, AuthenticatedClient


_L = TypeVar('_L', bound=AnonymousCollectionLinks)


class _AnonymousChrisStoreClient(AbstractClient[_L], Generic[_L]):
    pass


class AnonymousChrisStoreClient(AnonymousClient['AnonymousChrisStoreClient', AnonymousCollectionLinks],
                                _AnonymousChrisStoreClient[AnonymousCollectionLinks]):
    pass


class ChrisStoreClient(AuthenticatedClient['ChrisStoreClient', StoreCollectionLinks],
                       _AnonymousChrisStoreClient[StoreCollectionLinks]):
    async def upload_plugin(self, name: str, dock_image: str,
                            public_repo: str,
                            descriptor_file: Path) -> PluginUpload:
        form = aiohttp.FormData()
        form.add_field('name', name)
        form.add_field('dock_image', dock_image)
        form.add_field('public_repo', public_repo)

        form.add_field('descriptor_file', descriptor_file.open('rb'),
                       filename=descriptor_file.name, content_type='application/json')
        res = await self.s.post(
            self.collection_links.plugins,
            data=form
        )
        return from_json(PluginUpload, await res.text())
