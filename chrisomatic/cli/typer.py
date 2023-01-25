import asyncio
import sys
from pathlib import Path

import typer
from rich.console import Console
from strictyaml import YAMLValidationError

from chrisomatic.cli import Gstr_title
from chrisomatic.cli.agenda import agenda as apply_from_config
from chrisomatic.framework.outcome import Outcome
from chrisomatic.spec.deserialize import deserialize_config
from chrisomatic.spec.given import ValidationError

app = typer.Typer(add_completion=False)


@app.command()
def apply(
    tty: bool = typer.Option(
        False, "-t", "--tty", help="Force rich TTY features (such as spinners)"
    ),
    file: Path = typer.Argument(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        allow_dash=True,
        default="chrisomatic.yml",
        help="configuration file.",
    ),
):
    """
    ChRIS backend provisioner.
    """
    if file == Path("-"):
        input_config = sys.stdin.read()
        filename = "<stdin>"
    else:
        input_config = file.read_text()
        filename = str(file)

    console = Console(force_terminal=(True if tty else None))

    try:
        config = deserialize_config(input_config, filename, console)
    except (ValidationError, YAMLValidationError) as e:
        print(e)
        raise typer.Abort()

    console.print(Gstr_title)
    final_result = asyncio.run(apply_from_config(config, console))
    if final_result.summary[Outcome.FAILED] > 0:
        raise typer.Exit(1)


# @app.command()
# def export():
#     """
#     Analyze a running ChRIS backend and save its state to a file.
#     """
#     typer.echo('not implemented.')
#     raise typer.Abort()
