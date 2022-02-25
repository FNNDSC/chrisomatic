from chris.common.client import generic_of
from chris.common.atypes import CommonCollectionLinks
from chris.common.client import AuthenticatedClient
from chris.store.client import AnonymousChrisStoreClient, ChrisStoreClient
from chris.store.deserialization import (
    AnonymousCollectionLinks,
    AuthenticatedCollectionLinks,
    StoreCollectionLinks,
)
from chris.cube.client import CubeClient
from chris.cube.deserialization import CubeCollectionLinks
from chrisomatic.core.create_users import CreateUsersTask


def test_generic_of():
    assert (
        generic_of(AnonymousChrisStoreClient, CommonCollectionLinks)
        is AnonymousCollectionLinks
    )
    assert generic_of(ChrisStoreClient, CommonCollectionLinks) is StoreCollectionLinks
    assert (
        generic_of(ChrisStoreClient, AuthenticatedCollectionLinks)
        is StoreCollectionLinks
    )
    assert generic_of(CubeClient, CommonCollectionLinks) is CubeCollectionLinks
    assert generic_of(CubeClient, AuthenticatedCollectionLinks) is CubeCollectionLinks
    assert (
        generic_of(CreateUsersTask[ChrisStoreClient], AuthenticatedClient)
        is ChrisStoreClient
    )
    assert generic_of(CreateUsersTask[CubeClient], AuthenticatedClient) is CubeClient
