import typer
import dataclasses
from chrisomatic.cli import console
from chrisomatic.spec.given import GivenConfig
from chrisomatic.core.create import create_super_client
from chrisomatic.core.expand import smart_expand_config
from chrisomatic.framework.outcome import Outcome


async def apply(given_config: GivenConfig):

    superuser_creation, superclient_cm = await create_super_client(given_config.on)
    if superuser_creation == Outcome.FAILED:
        raise typer.Abort()

    async with superclient_cm as superclient:
        config = await smart_expand_config(given_config, superclient)
        existing_compute_resources = await superclient.cube.get_all_compute_resources()
        console.print(f'Pre-existing compute resources: {[c.name for c in existing_compute_resources]}')


