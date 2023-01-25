import serde
import strictyaml
from rich.console import Console
from rich.status import Status

from chrisomatic.spec.given import GivenConfig
from chrisomatic.spec.schema import schema


def deserialize_config(input_config: str, filename: str, console: Console) -> GivenConfig:
    if input_config.count('\n') < 100:
        return _load_from_yaml(input_config, filename)
    text = f"Loading [green]\"{filename}\"[/green] using " \
           "[italic]StrictYAML[/italic], might take a while..."
    with Status(status=text, spinner='dots10', console=console):
        return _load_from_yaml(input_config, filename)


def _load_from_yaml(input_config: str, filename: str) -> GivenConfig:
    parsed_yaml = strictyaml.load(input_config, schema=schema, label=filename)
    return serde.from_dict(GivenConfig, parsed_yaml.data)
