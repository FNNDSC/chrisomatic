from serde import deserialize
from chris.common.types import (
    UserUrl, UserId, ChrisUsername,
    PluginName, ImageTag, PluginVersion,
    PluginUrl, PluginId,
)


@deserialize
class Plugin:
    url: PluginUrl
    id: PluginId
    name: PluginName
    version: PluginVersion
    dock_image: ImageTag
    public_repo: str


@deserialize
class CreatedUser:
    url: UserUrl
    id: UserId
    username: ChrisUsername
    email: str
