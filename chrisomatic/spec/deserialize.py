import serde
import strictyaml
from rich.console import Console
from rich.status import Status

from chrisomatic.spec.given import GivenConfig
from chrisomatic.spec.schema import schema


def deserialize_config(
    input_config: str, filename: str, console: Console
) -> GivenConfig:
    if input_config.count("\n") < 100:
        return _load_from_yaml(input_config, filename, console)
    text = (
        f'Loading [green]"{filename}"[/green] using '
        "[italic]StrictYAML[/italic], might take a while..."
    )
    with Status(status=text, spinner="dots10", console=console):
        return _load_from_yaml(input_config, filename, console)


def _load_from_yaml(input_config: str, filename: str, console: Console) -> GivenConfig:
    parsed_yaml = strictyaml.load(input_config, schema=schema, label=filename)
    if "chris_store" in parsed_yaml.data:
        console.print(
            f"[yellow]WARNING[/yellow]: chris_store section in {filename} is deprecated."
        )
    if "chris_store_url" in parsed_yaml.data["on"]:
        console.print(
            f"[yellow]WARNING[/yellow]: on.chris_store_url in {filename} is deprecated."
        )
    return serde.from_dict(GivenConfig, parsed_yaml.data)
