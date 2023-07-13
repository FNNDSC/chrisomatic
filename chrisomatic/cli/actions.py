"""
Configures runner objects from `chrisomatic.framework.runner` for the tasks
performed by chrisomatic.
"""

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Sequence, Collection, Type, Optional

from aiochris import ChrisAdminClient, AnonChrisClient
from aiochris.models.data import UserData
from aiochris.models.public import ComputeResource
from aiochris.types import ChrisURL
from aiodocker import Docker
from rich.console import Console
from rich.spinner import Spinner

from chrisomatic.core.computeenvs import ComputeResourceTask
from chrisomatic.core.connect_peers import PeerConnectionTask
from chrisomatic.core.create_superuser import SuperUserTask
from chrisomatic.core.create_users import CreateUsersTask
from chrisomatic.core.plugins import RegisterPluginTask, PluginRegistration
from chrisomatic.framework.outcome import Outcome
from chrisomatic.framework.runner import (
    TableTaskRunner,
    TableDisplayConfig,
    ProgressTaskRunner,
)
from chrisomatic.helpers.waitup import WaitUp
from chrisomatic.spec.common import ComputeResource as GivenComputeResource, User
from chrisomatic.spec.given import On, GivenCubePlugin


@dataclass(frozen=True)
class Actions:
    console: Console
    chris_admin: ChrisAdminClient

    async def create_compute_resources(
        self,
        existing: Collection[ComputeResource],
        givens: Sequence[GivenComputeResource],
    ) -> Sequence[tuple[Outcome, Optional[ComputeResource]]]:
        runner = ProgressTaskRunner(
            title="Adding compute resources",
            tasks=[
                ComputeResourceTask(self.chris_admin, given, existing)
                for given in givens
            ],
            console=self.console,
        )
        return await runner.apply()

    async def create_users(
        self,
        users: Sequence[User],
        progress_title: str,
    ) -> Sequence[tuple[Outcome, UserData]]:
        runner = ProgressTaskRunner(
            tasks=[
                CreateUsersTask(self.chris_admin.url, user, self.connector)
                for user in users
            ],
            title=progress_title,
            console=self.console,
        )
        return await runner.apply()

    async def discover_peers(
        self, peer_urls: Collection[ChrisURL], progress_title: str
    ) -> Sequence[AnonChrisClient]:
        runner = ProgressTaskRunner(
            tasks=[
                PeerConnectionTask(url, connector=self.connector, connector_owner=False)
                for url in peer_urls
            ],
            title=progress_title,
            console=self.console,
            noisy=False,
            transient=True,
        )
        results = await runner.apply()

        good = [client for outcome, client in results if outcome is not Outcome.FAILED]
        bad = frozenset(peer_urls) - frozenset(client.url for client in good)
        if bad:
            self.console.print(f"[yellow]WARNING[/yellow]: broken peer {bad}")
        return good

    async def register_plugins(
        self,
        docker: Docker,
        plugins: Sequence[GivenCubePlugin],
        peers: Sequence[AnonChrisClient],
    ) -> Sequence[tuple[Outcome, PluginRegistration]]:
        runner = TableTaskRunner(
            tasks=[
                RegisterPluginTask(
                    plugin=p,
                    other_stores=peers,
                    docker=docker,
                    cube=self.chris_admin,
                )
                for p in plugins
            ],
            console=self.console,
        )
        return await runner.apply()

    @property
    def connector(self):
        return self.chris_admin.s.connector


@dataclass(frozen=True)
class PreActions:
    console: Console

    async def wait_for_backends(self, cube_url: ChrisURL):
        all_urls = [cube_url]
        user_urls = [url + "users/" for url in all_urls]
        return await self._wait_up(user_urls)

    async def _wait_up(
        self,
        urls: Sequence[str],
        good_status: int = 200,
        interval: float = 2.0,
        timeout: float = 300.0,
    ) -> tuple[bool, Sequence[float]]:
        runner = TableTaskRunner(
            config=TableDisplayConfig(
                spinner=Spinner("aesthetic"),
                spinner_width=12,
                polling_interval=interval / 4,
            ),
            tasks=[WaitUp(url, good_status, interval, timeout) for url in urls],
            console=self.console,
        )
        results = await runner.apply()
        all_good = all(outcome != Outcome.FAILED for outcome, _ in results)
        elapseds = [elapsed for _, elapsed in results]
        return all_good, elapseds

    async def create_super_client(
        self, on: On, docker: Docker
    ) -> tuple[Outcome, Optional[Actions]]:
        task = SuperUserTask(on=on, docker=docker)
        runner = TableTaskRunner(tasks=[task], console=self.console)
        (result,) = await runner.apply()
        outcome, superuser_client = result
        if outcome is Outcome.FAILED:
            return outcome, None
        return outcome, Actions(console=self.console, chris_admin=superuser_client)
