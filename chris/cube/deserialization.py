from dataclasses import dataclass
from serde import deserialize
from chris.common.types import ApiUrl, UserUrl
from chris.common.atypes import CommonCollectionLinks
from chris.cube.types import AdminUrl, ComputeResourceName


@deserialize
@dataclass(frozen=True)
class CubeCollectionLinks(CommonCollectionLinks):
    chrisinstance: ApiUrl
    admin: AdminUrl
    files: ApiUrl
    compute_resources: ApiUrl
    uploadedfiles: ApiUrl
    pacsfiles: ApiUrl
    servicefiles: ApiUrl
    filebrowser: ApiUrl
    user: UserUrl


@deserialize
class ChrisAdminCollectionLinks:
    compute_resources: ApiUrl
