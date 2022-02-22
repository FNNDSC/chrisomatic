import typer
import sys
from pathlib import Path
from typing import Optional
import chrisomatic
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
    Additively provision a running ChRIS backend.
    """
    input_config = sys.stdin.read() if file == Path('-') else file.read_text()

    try:
        apply_from_config(input_config)
    except InputError as e:
        typer.secho(f'Error parsing {file}: {e.args[0]}',
                    err=True, color=typer.colors.RED)
        raise typer.Abort()


@app.command()
def export():
    """
    Analyze a running ChRIS backend and save its state to a file.
    """
    typer.echo('not implemented.')
    raise typer.Abort()
