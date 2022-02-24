import typer
from chrisomatic.cli import console
from chrisomatic.spec.given import GivenConfig
from chrisomatic.core.waitup import wait_up
from chrisomatic.core.create import create_super_client
from chrisomatic.core.expand import smart_expand_config
from chrisomatic.core.computeenvs import create_compute_resources
from chrisomatic.framework.outcome import Outcome


async def apply(given_config: GivenConfig):

    # ------------------------------------------------------------
    # wait for CUBE and friends to come online
    # ------------------------------------------------------------

    console.rule('[bold blue]Waiting for Backend Servers')
    user_urls = (given_config.on.cube_url + 'users/', given_config.on.chris_store_url + 'users/')
    all_good, elapseds = await wait_up(user_urls)
    if not all_good:
        raise typer.Abort()

    # ------------------------------------------------------------
    # create superuser account if necessary, and then create HTTP sessions
    # ------------------------------------------------------------

    console.rule('[bold blue]Creating Superuser Account and HTTP Sessions')
    superuser_creation, superclient_cm = await create_super_client(given_config.on)
    if superuser_creation == Outcome.FAILED:
        raise typer.Abort()

    async with superclient_cm as superclient:

        # ------------------------------------------------------------
        # fully expand config
        # ------------------------------------------------------------

        config = await smart_expand_config(given_config, superclient)

        # ------------------------------------------------------------
        # add compute resources
        # ------------------------------------------------------------

        console.rule('[bold blue]Compute Resources')
        existing_compute_resources = await superclient.cube.get_all_compute_resources()
        console.print(f'Existing compute resources: {[c.name for c in existing_compute_resources]}')
        create_compute_resources_results = await create_compute_resources(
            superclient, existing_compute_resources, config.cube.compute_resource
        )
