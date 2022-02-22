import abc
from serde import deserialize
from chris.common.types import ApiUrl


@deserialize
class AbstractCollectionLinks(abc.ABC):
    plugins: ApiUrl
