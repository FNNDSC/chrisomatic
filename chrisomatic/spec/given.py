from serde import deserialize, field
from chris.common.types import PluginName, PluginVersion, ImageTag, ChrisURL
from chris.store.types import StorePluginUrl
from typing import Union, Optional

from chrisomatic.spec.common import User, ComputeResource, Pipeline


@deserialize
class On:
    cube_url: ChrisURL
    chris_store_url: ChrisURL
    chris_superuser: User
    public_store: list[ChrisURL] = field(default_factory=lambda: ['https://chrisstore.co/api/v1/'])


@deserialize
class GivenBackend:
    users: list[User] = field(default_factory=list)
    pipelines: Union[str, list[Pipeline]] = field(default_factory=list)


@deserialize
class GivenChrisStore(GivenBackend):
    pass


@deserialize
class GivenCubePlugin:
    url: Optional[StorePluginUrl] = None
    name: Optional[PluginName] = None
    version: Optional[PluginVersion] = None
    dock_image: Optional[ImageTag] = None
    public_repo: Optional[str] = None
    computeresource: Optional[list[ComputeResource]] = field(default_factory=list)


@deserialize
class GivenCube(GivenBackend):
    computeresource: list[ComputeResource] = field(default_factory=list)
    plugins: list[GivenCubePlugin] = field(default_factory=list)


@deserialize
class GivenConfig:
    version: str
    to: dict
    cube: GivenCube
    chris_store: GivenChrisStore
