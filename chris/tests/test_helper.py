from chris.common.client import generic_of
from chris.common.atypes import CommonCollectionLinks
from chris.store.client import AnonymousChrisStoreClient, ChrisStoreClient
from chris.store.deserialization import AnonymousCollectionLinks, AuthenticatedCollectionLinks, StoreCollectionLinks
from chris.cube.client import CubeClient
from chris.cube.deserialization import CubeCollectionLinks


def test_generic_of():
    assert generic_of(AnonymousChrisStoreClient, CommonCollectionLinks) == AnonymousCollectionLinks
    assert generic_of(ChrisStoreClient, CommonCollectionLinks) == StoreCollectionLinks
    assert generic_of(ChrisStoreClient, AuthenticatedCollectionLinks) == StoreCollectionLinks
    assert generic_of(CubeClient, CommonCollectionLinks) == CubeCollectionLinks
    assert generic_of(CubeClient, AuthenticatedCollectionLinks) == CubeCollectionLinks
