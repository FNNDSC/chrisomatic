import typer
import sys
from pathlib import Path
from typing import Optional
from strictyaml import YAMLValidationError
import chrisomatic
from chrisomatic.spec.deserialize import deserialize_config
from chrisomatic.cli.apply import apply as apply_from_config
from chrisomatic.spec.deserialize import InputError

app = typer.Typer()


def show_version(value: bool):
    """
    Print version.
    """
    if not value:
        return
    typer.echo(f'chrisomatic {chrisomatic.__version__}')
    raise typer.Exit()


# noinspection PyUnusedLocal
@app.callback()
def entry(
        version: Optional[bool] = typer.Option(
            None, '--version', '-V', callback=show_version,
            is_eager=True, help='Print version.')
):
    """
    ChRIS backend management.
    """
    pass


@app.command()
def apply(
        file: Path = typer.Argument(
            exists=True,
            file_okay=True,
            dir_okay=False,
            writable=False,
            readable=True,
            allow_dash=True,
            default='chrisomatic.yml',
            help='configuration file.'
        )
):
    """
    Apply a configuration additively to a running ChRIS backend.
    """
    if file == Path('-'):
        input_config = sys.stdin.read()
        filename = '<stdin>'
    else:
        input_config = file.read_text()
        filename = str(file)

    try:
        config = deserialize_config(input_config, filename)
    except YAMLValidationError as e:
        print(e)
        raise typer.Abort()

    typer.echo(config)
    # try:
    #     apply_from_config(input_config)
    # except InputError as e:
    #     typer.secho(f'Error parsing {file}: {e.args[0]}',
    #                 err=True, color=typer.colors.RED)
    #     raise typer.Abort()


@app.command()
def export():
    """
    Analyze a running ChRIS backend and save its state to a file.
    """
    typer.echo('not implemented.')
    raise typer.Abort()
