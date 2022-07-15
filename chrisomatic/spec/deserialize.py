from chrisomatic.spec.schema import schema
from chrisomatic.spec.given import GivenConfig
from serde import from_dict
from strictyaml import load


def deserialize_config(input_config: str, filename: str):
    return _load_from_yaml(input_config, filename)


def _load_from_yaml(input_config: str, filename: str) -> GivenConfig:
    parsed_yaml = load(input_config, schema=schema, label=filename)
    return from_dict(GivenConfig, parsed_yaml.data)
