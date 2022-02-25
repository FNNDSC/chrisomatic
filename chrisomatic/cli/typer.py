import asyncio
import typer
import sys
from pathlib import Path
from typing import Optional
from strictyaml import YAMLValidationError
import chrisomatic
from chrisomatic.spec.deserialize import deserialize_config
from chrisomatic.cli import Gstr_title, console
from chrisomatic.cli.apply import apply as apply_from_config
from chrisomatic.cli.noop import wait_on_cube
from chrisomatic.spec.deserialize import InputError
from chrisomatic.framework.outcome import Outcome


def show_version(value: bool):
    """
    Print version.
    """
    if not value:
        return
    typer.echo(f"chrisomatic {chrisomatic.__version__}")
    raise typer.Exit()


app = typer.Typer(add_completion=False)


# noinspection PyUnusedLocal
@app.callback()
def entry(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=show_version,
        is_eager=True,
        help="Print version.",
    )
):
    """
    ChRIS backend management.
    """
    pass


@app.command(context_settings={"help_option_names": ["-h", "--help"]})
def apply(
    file: Path = typer.Argument(
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=False,
        readable=True,
        allow_dash=True,
        default="chrisomatic.yml",
        help="configuration file.",
    )
):
    """
    Apply a configuration additively to a running ChRIS backend.
    """
    if file == Path("-"):
        input_config = sys.stdin.read()
        filename = "<stdin>"
    else:
        input_config = file.read_text()
        filename = str(file)

    try:
        config = deserialize_config(input_config, filename)
    except YAMLValidationError as e:
        print(e)
        raise typer.Abort()

    console.print(Gstr_title)
    final_result = asyncio.run(apply_from_config(config))
    if final_result.summary[Outcome.FAILED] > 0:
        raise typer.Exit(1)


@app.command()
def noop():
    """
    Block by waiting on the CUBE container.
    """
    asyncio.run(wait_on_cube())


# @app.command()
# def export():
#     """
#     Analyze a running ChRIS backend and save its state to a file.
#     """
#     typer.echo('not implemented.')
#     raise typer.Abort()
