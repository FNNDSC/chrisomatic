import typer
from typing import Sequence, Optional, Iterable
from chris.common.types import ChrisUsername
from chrisomatic.spec.common import User
from chrisomatic.cli import console
from chris.store.client import ChrisStoreClient
from chris.cube.client import CubeClient
from chrisomatic.spec.given import GivenConfig
from chrisomatic.core.omniclient import A
from chrisomatic.core.waitup import wait_up
from chrisomatic.core.create_omniclient import create_super_client
from chrisomatic.core.expand import smart_expand_config
from chrisomatic.core.computeenvs import create_compute_resources
from chrisomatic.core.create_users import create_users
from chrisomatic.core.plugins import register_plugins
from chrisomatic.framework.outcome import Outcome
from rich.text import Text
from chrisomatic.cli.final_result import FinalResult


async def apply(given_config: GivenConfig) -> FinalResult:

    # ------------------------------------------------------------
    # Wait for CUBE and friends to come online
    # ------------------------------------------------------------

    console.rule("[bold blue]Waiting for Backend Servers")
    user_urls = [
        url + "users/"
        for url in (given_config.on.cube_url, given_config.on.chris_store_url)
        if url
    ]
    all_good, elapseds = await wait_up(user_urls)
    if not all_good:
        raise typer.Abort()

    # ------------------------------------------------------------
    # Create superuser account if necessary, and then create HTTP sessions
    # ------------------------------------------------------------

    console.rule("[bold blue]Creating Superuser Account and HTTP Sessions")
    superuser_creation, omni_cm = await create_super_client(given_config.on)
    if superuser_creation == Outcome.FAILED:
        raise typer.Abort()

    async with omni_cm as omniclient:

        # ------------------------------------------------------------
        # Add compute resources
        # ------------------------------------------------------------

        console.rule("[bold blue]Compute Resources")
        existing_compute_resources = await omniclient.cube.get_all_compute_resources()
        console.print(
            f"Existing compute resources: {[c.name for c in existing_compute_resources]}"
        )
        create_compute_resources_results = await create_compute_resources(
            omniclient, existing_compute_resources, given_config.cube.compute_resource
        )

        # ------------------------------------------------------------
        # Create users
        # ------------------------------------------------------------
        console.rule("[bold blue]Creating Users")
        if omniclient.store_url:
            given_store_users = given_config.chris_store.users
            store_user_creation = await create_users(
                omniclient,
                omniclient.store_url,
                given_store_users,
                ChrisStoreClient,
                "creating users in the ChRIS store...",
            )
        else:
            given_store_users = []
            store_user_creation = []

        cube_user_creation = await create_users(
            omniclient,
            omniclient.cube.url,
            given_config.cube.users,
            CubeClient,
            "creating users in CUBE...",
        )

        store_clients = created_users_mapping(given_store_users, store_user_creation)
        cube_clients = created_users_mapping(
            given_config.cube.users, cube_user_creation
        )

        # ------------------------------------------------------------
        # Fully expand config
        # ------------------------------------------------------------
        config = await smart_expand_config(
            given_config, omniclient, get_first_username(store_clients)
        )

        # ------------------------------------------------------------
        # Register plugins to CUBE
        # ------------------------------------------------------------
        console.rule("[bold blue]Registering plugins to CUBE")
        plugin_registrations = await register_plugins(
            omniclient, config.cube.plugins, store_clients
        )

    # ------------------------------------------------------------
    # Finish up
    # ------------------------------------------------------------

    all_outcomes = count_outcomes(
        (
            superuser_creation,
            *(o for o, _ in create_compute_resources_results),
            *(o for o, _ in store_user_creation),
            *(o for o, _ in cube_user_creation),
            *(o for o, _ in plugin_registrations),
        )
    )
    console.rule(to_summary(all_outcomes))
    return FinalResult(summary=all_outcomes)


def created_users_mapping(
    user_infos: Sequence[User], user_creation: Sequence[tuple[Outcome, A]]
) -> dict[ChrisUsername, A]:
    mapping = dict()
    for user_info, r in zip(user_infos, user_creation):
        outcome, client = r
        if outcome != Outcome.FAILED:
            mapping[user_info.username] = client
    return mapping


def get_first_username(mapping: dict[ChrisUsername, A]) -> Optional[ChrisUsername]:
    return next(iter(mapping.keys()), None)


def count_outcomes(outcomes: Iterable[Outcome]) -> dict[Outcome, int]:
    return {
        outcome_type: sum(outcome == outcome_type for outcome in outcomes)
        for outcome_type in Outcome
    }


def to_summary(outcomes: dict[Outcome, int]) -> Text:
    summary = Text()
    summary.append("Summary: ", style="bold")
    summary.append(str(outcomes[Outcome.NO_CHANGE]), style=Outcome.NO_CHANGE.style)
    summary.append(" present, ")
    summary.append(str(outcomes[Outcome.CHANGE]), style=Outcome.CHANGE.style)
    summary.append(" changed, ")
    summary.append(str(outcomes[Outcome.FAILED]), style=Outcome.FAILED.style)
    summary.append(" failures")
    return summary
