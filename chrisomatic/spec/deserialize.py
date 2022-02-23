from chrisomatic.spec.schema import schema
from chrisomatic.spec.given import GivenConfig
from serde import from_dict
from strictyaml import load


class InputError(Exception):
    pass


def deserialize_config(input_config: str, filename: str) -> dict:
    parsed_yaml = load(input_config, schema=schema, label=filename)
    return parsed_yaml.data
