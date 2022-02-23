import typer
from chrisomatic.cli import console
from chrisomatic.spec.given import GivenConfig
from chrisomatic.core.create import create_super_client
from chrisomatic.framework.outcome import Outcome
from chrisomatic.framework.taskset import TableTaskSet


async def apply(config: GivenConfig):
    superuser_creation, superclient_cm = await create_super_client(config.on)
    if superuser_creation == Outcome.FAILED:
        raise typer.Abort()
    async with superclient_cm as superclient:
        console.print(await superclient.cube.get_all_compute_resources())
