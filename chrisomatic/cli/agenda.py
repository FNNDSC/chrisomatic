import asyncio
from typing import Sequence, Optional, Iterable

import typer
from aiodocker import Docker
from rich.console import Console
from rich.text import Text

from chrisomatic.cli.actions import PreActions
from chrisomatic.cli.final_result import FinalResult
from chrisomatic.core.expand import smart_expand_config
from chrisomatic.framework.outcome import Outcome
from chrisomatic.spec.common import User
from chrisomatic.spec.given import GivenConfig, ValidationError


async def agenda(given_config: GivenConfig, console: Console) -> FinalResult:
    docker = _maybe_docker(console)
    pre_actions = PreActions(console)
    closables = [docker]

    async def close_all():
        closings = (client.close() for client in closables)
        await asyncio.gather(*closings)

    # ------------------------------------------------------------
    # Wait for CUBE and friends to come online
    # ------------------------------------------------------------
    console.rule("[bold blue]Waiting for Backend Servers")
    all_good, _ = await pre_actions.wait_for_backends(given_config.on.cube_url)
    if not all_good:
        await close_all()
        raise typer.Abort()

    # ------------------------------------------------------------
    # Create superuser account if necessary, and then create HTTP sessions
    # ------------------------------------------------------------
    console.rule("[bold blue]Creating Superuser Account and HTTP Sessions")
    superuser_creation, actions = await pre_actions.create_super_client(
        given_config.on, docker
    )
    if superuser_creation == Outcome.FAILED:
        await close_all()
        raise typer.Abort()
    closables.append(actions.chris_admin)

    # ------------------------------------------------------------
    # Add compute resources
    # ------------------------------------------------------------
    console.rule("[bold blue]Compute Resources")
    existing_compute_resources = await actions.chris_admin.get_all_compute_resources()
    create_compute_resources_results = await actions.create_compute_resources(
        existing_compute_resources, given_config.cube.compute_resource
    )

    # ------------------------------------------------------------
    # Create users
    # ------------------------------------------------------------
    console.rule("[bold blue]Creating Users")
    user_creation = await actions.create_users(
        given_config.cube.users,
        "creating users in CUBE...",
    )

    # ------------------------------------------------------------
    # Register plugins to CUBE
    # ------------------------------------------------------------
    console.rule("[bold blue]Registering plugins to CUBE")
    try:
        config = await smart_expand_config(given_config, docker)
    except ValidationError as e:
        console.print(e)
        await close_all()
        raise typer.Abort()

    peer_clients = await actions.discover_peers(
        config.on.public_store, "Connecting to peers..."
    )
    plugin_registrations = await actions.register_plugins(
        docker, config.cube.plugins, peer_clients
    )

    # ------------------------------------------------------------
    # Finish up
    # ------------------------------------------------------------

    all_outcomes = _count_outcomes(
        (
            superuser_creation,
            *(o for o, _ in create_compute_resources_results),
            *(o for o, _ in user_creation),
            *(o for o, _ in plugin_registrations),
        )
    )
    console.rule(_to_summary(all_outcomes))
    await close_all()
    return FinalResult(summary=all_outcomes)


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
