from typing import Sequence, Optional, Iterable

import typer
from aiodocker import Docker
from rich.console import Console
from rich.text import Text

from chris.common.types import ChrisUsername
from chris.cube.client import CubeClient
from chris.store.client import ChrisStoreClient
from chrisomatic.cli.actions import PreActions
from chrisomatic.cli.final_result import FinalResult
from chrisomatic.core.expand import smart_expand_config
from chrisomatic.core.omniclient import A
from chrisomatic.framework.outcome import Outcome
from chrisomatic.spec.common import User
from chrisomatic.spec.given import GivenConfig


async def agenda(given_config: GivenConfig, console: Console) -> FinalResult:
    docker = _maybe_docker(console)
    pre_actions = PreActions(console)

    # ------------------------------------------------------------
    # Wait for CUBE and friends to come online
    # ------------------------------------------------------------
    console.rule("[bold blue]Waiting for Backend Servers")
    all_good, _ = await pre_actions.wait_for_backends(given_config.on)
    if not all_good:
        raise typer.Abort()

    # ------------------------------------------------------------
    # Create superuser account if necessary, and then create HTTP sessions
    # ------------------------------------------------------------
    console.rule("[bold blue]Creating Superuser Account and HTTP Sessions")
    superuser_creation, actions_cm = await pre_actions.create_super_client(
        given_config.on, docker
    )
    if superuser_creation == Outcome.FAILED:
        raise typer.Abort()

    async with actions_cm as actions:

        # ------------------------------------------------------------
        # Add compute resources
        # ------------------------------------------------------------
        console.rule("[bold blue]Compute Resources")
        existing_compute_resources = (
            await actions.omniclient.cube.get_all_compute_resources()
        )
        console.print(
            f"Existing compute resources: {[c.name for c in existing_compute_resources]}"
        )
        create_compute_resources_results = await actions.create_compute_resources(
            existing_compute_resources, given_config.cube.compute_resource
        )

        # ------------------------------------------------------------
        # Create users
        # ------------------------------------------------------------
        console.rule("[bold blue]Creating Users")
        if actions.omniclient.store_url:
            given_store_users = given_config.chris_store.users
            store_user_creation = await actions.create_users(
                actions.omniclient.store_url,
                given_store_users,
                ChrisStoreClient,
                "creating users in the ChRIS store...",
            )
        else:
            given_store_users = []
            store_user_creation = []

        cube_user_creation = await actions.create_users(
            actions.omniclient.cube.url,
            given_config.cube.users,
            CubeClient,
            "creating users in CUBE...",
        )

        store_clients = _created_users_mapping(given_store_users, store_user_creation)
        cube_clients = _created_users_mapping(
            given_config.cube.users, cube_user_creation
        )

        # ------------------------------------------------------------
        # Fully expand config
        # ------------------------------------------------------------
        config = await smart_expand_config(
            given_config, actions.omniclient.docker, _get_first_username(store_clients)
        )

        # ------------------------------------------------------------
        # Register plugins to CUBE
        # ------------------------------------------------------------
        console.rule("[bold blue]Registering plugins to CUBE")
        plugin_registrations = await actions.register_plugins(
            config.cube.plugins, store_clients
        )

    # ------------------------------------------------------------
    # Finish up
    # ------------------------------------------------------------

    all_outcomes = _count_outcomes(
        (
            superuser_creation,
            *(o for o, _ in create_compute_resources_results),
            *(o for o, _ in store_user_creation),
            *(o for o, _ in cube_user_creation),
            *(o for o, _ in plugin_registrations),
        )
    )
    console.rule(_to_summary(all_outcomes))
    return FinalResult(summary=all_outcomes)


def _created_users_mapping(
    user_infos: Sequence[User], user_creation: Sequence[tuple[Outcome, A]]
) -> dict[ChrisUsername, A]:
    mapping = dict()
    for user_info, r in zip(user_infos, user_creation):
        outcome, client = r
        if outcome != Outcome.FAILED:
            mapping[user_info.username] = client
    return mapping


def _get_first_username(mapping: dict[ChrisUsername, A]) -> Optional[ChrisUsername]:
    return next(iter(mapping.keys()), None)


def _count_outcomes(outcomes: Iterable[Outcome]) -> dict[Outcome, int]:
    return {
        outcome_type: sum(outcome == outcome_type for outcome in outcomes)
        for outcome_type in Outcome
    }


def _to_summary(outcomes: dict[Outcome, int]) -> Text:
    summary = Text()
    summary.append("Summary: ", style="bold")
    summary.append(str(outcomes[Outcome.NO_CHANGE]), style=Outcome.NO_CHANGE.style)
    summary.append(" present, ")
    summary.append(str(outcomes[Outcome.CHANGE]), style=Outcome.CHANGE.style)
    summary.append(" changed, ")
    summary.append(str(outcomes[Outcome.FAILED]), style=Outcome.FAILED.style)
    summary.append(" failures")
    return summary


def _maybe_docker(console: Console) -> Optional[Docker]:
    try:
        docker = Docker()
        console.print(
            "\t[dim]:whale: Connected to [italic]Docker[/italic] on "
            f"[underline]{docker.docker_host}[/underline][/dim]\n"
        )
        return docker
    except ValueError:
        console.print(f"\t[dim]No container engine available.[/dim]\n")
        return None
