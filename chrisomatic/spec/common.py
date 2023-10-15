from typing import Optional

from serde import serde
from aiochris.types import Username, Password, ComputeResourceName, PfconUrl
from dataclasses import dataclass, astuple, asdict


@serde
@dataclass(frozen=True)
class User:
    username: Username
    password: Password
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
    innetwork: Optional[bool] = None

    def get_missing(self) -> list[str]:
        return [k for k, v in asdict(self).items() if v is None]


@serde
@dataclass(frozen=True)
class Pipeline:
    src: str
    owner: Username
    locked: bool = True
