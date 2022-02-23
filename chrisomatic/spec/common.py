from serde import serde
from chris.common.types import ChrisUsername, ChrisPassword
from chris.cube.types import ComputeResourceName
from dataclasses import dataclass, field


@serde
@dataclass(frozen=True)
class User:
    username: ChrisUsername
    password: ChrisPassword
    email: str = None

    def __post_init__(self):
        if self.email is None:
            object.__setattr__(self, 'email', f'chrisomatic.{self.username}@example.com')


@serde
@dataclass(frozen=True)
class ComputeResource:
    name: ComputeResourceName
    url: str
    username: str = 'pfcon'
    password: str = 'pfcon1234'
    description: str = ''


@serde
@dataclass(frozen=True)
class Pipeline:
    src: str
    owner: ChrisUsername
    locked: bool = True
