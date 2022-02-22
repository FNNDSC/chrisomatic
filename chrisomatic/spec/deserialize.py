from chrisomatic.spec.given import GivenConfig
from serde.yaml import from_yaml
from serde import SerdeError


class InputError(Exception):
    pass


def deserialize_config(input_config: str) -> GivenConfig:
    try:
        return from_yaml(GivenConfig, input_config)
    except SerdeError as e:
        raise InputError(f'Bad (or missing) value for: {e}')
