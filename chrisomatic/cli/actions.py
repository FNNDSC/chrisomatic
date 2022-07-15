"""
Configures runner objects from `chrisomatic.framework.runner` for the tasks
performed by chrisomatic.
"""

from dataclasses import dataclass
from typing import Sequence, AsyncContextManager, Collection, Type
from contextlib import asynccontextmanager

from aiodocker import Docker
from rich.console import Console
from rich.spinner import Spinner

from chris.common.types import ChrisURL, ChrisUsername
from chris.store.client import ChrisStoreClient
from chrisomatic.core.computeenvs import ComputeResourceTask
from chrisomatic.core.create_omniclient import OmniClientFactory
from chrisomatic.core.create_users import CreateUsersTask
from chrisomatic.core.omniclient import OmniClient, A
from chrisomatic.core.plugins import RegisterPluginTask, PluginRegistration
from chrisomatic.core.waitup import WaitUp
from chrisomatic.framework.outcome import Outcome
from chrisomatic.framework.runner import (
    TableTaskRunner,
    TableDisplayConfig,
    ProgressTaskRunner,
)
from chrisomatic.spec.given import On, GivenCubePlugin
from chrisomatic.spec.common import ComputeResource as GivenComputeResource, User
from chris.cube.deserialization import ComputeResource as CubeComputeResource


@dataclass(frozen=True)
class Actions:
    console: Console
    omniclient: OmniClient

    async def create_compute_resources(
        self,
        existing: Collection[CubeComputeResource],
        givens: Sequence[GivenComputeResource],
    ) -> Sequence[tuple[Outcome, CubeComputeResource]]:
        runner = ProgressTaskRunner(
            title="Adding compute resources",
            tasks=[
                ComputeResourceTask(self.omniclient, given, existing)
                for given in givens
            ],
            console=self.console,
        )
        return await runner.apply()

    async def create_users(
        self,
        url: ChrisURL,
        users: Sequence[User],
        user_type: Type[A],
        progress_title: str,
    ) -> Sequence[tuple[Outcome, A]]:
        runner = ProgressTaskRunner(
            tasks=[
                CreateUsersTask[user_type](self.omniclient, url, user, user_type)
                for user in users
            ],
            title=progress_title,
            console=self.console,
        )
        return await runner.apply()

    async def register_plugins(
        self,
        plugins: Sequence[GivenCubePlugin],
        store_clients: dict[ChrisUsername, ChrisStoreClient],
    ) -> Sequence[tuple[Outcome, PluginRegistration]]:
        runner = TableTaskRunner(
            tasks=[
                RegisterPluginTask(
                    plugin=p,
                    linked_store=(
                        store_clients[p.owner] if p.owner in store_clients else None
                    ),
                    other_stores=self.omniclient.public_stores,
                    docker=self.omniclient.docker,
                    cube=self.omniclient.cube,
                )
                for p in plugins
            ],
            console=self.console,
        )
        return await runner.apply()


@dataclass(frozen=True)
class PreActions:
    console: Console

    async def wait_for_backends(self, on: On):
        user_urls = [url + "users/" for url in (on.cube_url, on.chris_store_url) if url]
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
    ) -> tuple[Outcome, AsyncContextManager[Actions]]:
        fact = OmniClientFactory(on=on, docker=docker)
        task_set = TableTaskRunner(tasks=[fact], console=self.console)
        (result,) = await task_set.apply()
        superuser_creation, cm = result
        return superuser_creation, self.__actions_context(cm)

    @asynccontextmanager
    async def __actions_context(self, cm: OmniClient):
        async with cm as omniclient:
            yield Actions(self.console, omniclient)
