import io
from pathlib import Path
import chris.common.errors as errors

from chris.store.deserialization import (
    NewStoreUser,
    AnonymousCollectionLinks,
    StoreCollectionLinks,
    PluginUpload,
    PluginSearch,
    Plugin
)
import aiohttp
from serde.json import from_json
from typing import TypeVar, Generic
from chris.common.client import AbstractClient, AnonymousClient, AuthenticatedClient
from chris.store.types import StorePluginSearchUrl


_L = TypeVar('_L', bound=AnonymousCollectionLinks)


class _AnonymousChrisStoreClient(AbstractClient[_L], Generic[_L]):

    @property
    def plugins_search_url(self) -> StorePluginSearchUrl:
        return StorePluginSearchUrl(self.collection_links.plugins + 'search/')

    async def get_first_plugin(self, **query):
        # no upstream docs so why should I?
        # https://github.com/FNNDSC/ChRIS_store/blob/8f4fc98b3d87dc9aa3f7fbb314684021680a5945/store_backend/plugins/models.py#L203-L261
        search = await self.__search_plugins(**query)
        if search.count == 0:
            raise errors.EmptySearchError(f'No results on {self.url} for: {query}')
        # if search.count > 1:
        #     raise errors.PluralResultsError(
        #         f'Multiple search results from {self.url} for: {query}\n'
        #         + str(search)
        #     )
        return search.results[0]

    async def __search_plugins(self, **query) -> PluginSearch:
        # pagination not implemented
        res = await self.s.get(self.plugins_search_url, params=query)
        return from_json(PluginSearch, await res.text())


class AnonymousChrisStoreClient(_AnonymousChrisStoreClient[AnonymousCollectionLinks],
                                AnonymousClient['AnonymousChrisStoreClient', AnonymousCollectionLinks]):
    pass


class ChrisStoreClient(_AnonymousChrisStoreClient[StoreCollectionLinks],
                       AuthenticatedClient['ChrisStoreClient', StoreCollectionLinks, NewStoreUser]):
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
