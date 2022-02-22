from chris.common.client import AuthenticatedClient
from chris.cube.deserialization import ChrisAdminCollectionLinks, CubeCollectionLinks


class CubeClient(AuthenticatedClient['CubeClient', CubeCollectionLinks]):
    pass

