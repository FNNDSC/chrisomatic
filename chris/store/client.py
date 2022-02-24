import abc
from pathlib import Path
from chris.common.deserialization import Plugin
from chris.store.deserialization import (
    AnonymousCollectionLinks,
    StoreCollectionLinks
)
import aiohttp
from serde.json import from_json
from typing import TypeVar
from chris.common.client import AbstractClient, AnonymousClient, AuthenticatedClient


_L = TypeVar('_L', bound=AnonymousCollectionLinks)


class AbstractChrisStoreClient(AbstractClient[_L, Plugin], abc.ABC):
    pass


class AnonymousChrisStoreClient(AnonymousClient[AnonymousCollectionLinks, Plugin, 'AnonymousChrisStoreClient'],
                                AbstractChrisStoreClient[AnonymousCollectionLinks]):
    pass


class ChrisStoreClient(AuthenticatedClient[StoreCollectionLinks, Plugin, 'ChrisStoreClient'],
                       AbstractChrisStoreClient[StoreCollectionLinks]):
    async def upload_plugin(self, name: str, dock_image: str,
                            public_repo: str,
                            descriptor_file: Path) -> Plugin:
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
        return from_json(Plugin, await res.text())
