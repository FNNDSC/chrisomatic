from chrisomatic.spec.given import GivenConfig
from serde import from_dict


class InputError(Exception):
    pass


def deserialize_config(input_config: str) -> GivenConfig:
    ...  # TODO strict yaml
