from serde import serde
from chris.common.types import ChrisUsername, ChrisPassword
from chris.cube.types import ComputeResourceName


@serde
class User:
    username: ChrisUsername
    password: ChrisPassword


@serde
class ComputeResource:
    name: ComputeResourceName
    url: str
    username: str = 'pfcon'
    password: str = 'pfcon1234'
    description: str = ''


@serde
class Pipeline:
    src: str
    owner: ChrisUsername
    locked: bool = True
