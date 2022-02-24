import typer
import dataclasses
from chrisomatic.cli import console
from chrisomatic.spec.given import GivenConfig
from chrisomatic.core.waitup import wait_up
from chrisomatic.core.create import create_super_client
from chrisomatic.core.expand import smart_expand_config
from chrisomatic.framework.outcome import Outcome


async def apply(given_config: GivenConfig):

    # wait for CUBE and friends to come online
    user_urls = (given_config.on.cube_url + 'users/', given_config.on.chris_store_url + 'users/')
    all_good, elapseds = await wait_up(user_urls)
    if not all_good:
        raise typer.Abort()

    # create superuser account if necessary, and then create HTTP sessions
    superuser_creation, superclient_cm = await create_super_client(given_config.on)
    if superuser_creation == Outcome.FAILED:
        raise typer.Abort()

    async with superclient_cm as superclient:
        config = await smart_expand_config(given_config, superclient)
        existing_compute_resources = await superclient.cube.get_all_compute_resources()
        console.print(f'Pre-existing compute resources: {[c.name for c in existing_compute_resources]}')
