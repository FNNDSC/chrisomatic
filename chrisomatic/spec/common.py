from typing import Optional

from serde import serde
from chris.common.types import ChrisUsername, ChrisPassword
from chris.cube.types import ComputeResourceName, PfconUrl
from dataclasses import dataclass, astuple


@serde
@dataclass(frozen=True)
class User:
    username: ChrisUsername
    password: ChrisPassword
    email: str = None

    def __post_init__(self):
        if self.email is None:
            object.__setattr__(
                self, "email", f"chrisomatic.{self.username}@example.com"
            )


@serde
@dataclass(frozen=True)
class ComputeResource:
    name: ComputeResourceName
    url: Optional[PfconUrl] = None
    username: Optional[str] = None
    password: Optional[str] = None
    description: Optional[str] = None

    def is_some(self) -> bool:
        return all(f is not None for f in astuple(self))


@serde
@dataclass(frozen=True)
class Pipeline:
    src: str
    owner: ChrisUsername
    locked: bool = True
