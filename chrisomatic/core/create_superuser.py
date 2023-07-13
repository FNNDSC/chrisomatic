import dataclasses
from typing import Optional

import aiodocker
import aiohttp
from aiochris import ChrisAdminClient
from aiochris.errors import IncorrectLoginError, ResponseError
from rich.console import RenderableType

from chrisomatic.helpers.superuser import create_superuser, SuperuserCreationError
from chrisomatic.framework import ChrisomaticTask, Channel, Outcome
from chrisomatic.spec.given import On


@dataclasses.dataclass(frozen=True)
class SuperUserTask(ChrisomaticTask[ChrisAdminClient]):
    """
    Tries to log in as the _ChRIS superuser_. If the login is incorrect, create the superuser then try again.
    """

    on: On
    docker: aiodocker.Docker
    connector: Optional[aiohttp.BaseConnector] = None
    connector_owner: bool = True
    attempt: int = 0

    def first_status(self) -> tuple[str, RenderableType]:
        user = self.on.chris_superuser
        return (
            f"superuser ({user.username})",
            f"checking for superuser: username={user.username}",
        )

    async def run(self, status: Channel) -> tuple[Outcome, Optional[ChrisAdminClient]]:
        try:
            return await self.try_connect_conclude_with(status, Outcome.NO_CHANGE)
        except IncorrectLoginError:
            if await self.create_superuser_using_docker(status):
                try:
                    return await self.try_connect_conclude_with(status, Outcome.CHANGE)
                except IncorrectLoginError:
                    status.replace("Failed to create superuser.")
                    return Outcome.FAILED, None
            return Outcome.FAILED, None

    async def connect(self) -> ChrisAdminClient:
        user = self.on.chris_superuser
        return await ChrisAdminClient.from_login(
            url=self.on.cube_url,
            username=user.username,
            password=user.password,
            connector=self.connector,
            connector_owner=self.connector_owner,
        )

    async def try_connect(self, status) -> Optional[ChrisAdminClient]:
        try:
            superuser = await self.connect()
            status.replace("connected!")
            return superuser
        except ResponseError as e:
            status.replace(str(e))
            return None

    async def try_connect_conclude_with(
        self, status: Channel, outcome: Outcome
    ) -> tuple[Outcome, Optional[ChrisAdminClient]]:
        superuser = await self.try_connect(status)
        if superuser is None:
            return Outcome.FAILED, None
        return outcome, superuser

    async def create_superuser_using_docker(self, status: Channel) -> bool:
        user = self.on.chris_superuser
        status.replace(f'Creating superuser "{user.username}" ...')
        try:
            await create_superuser(self.docker, user)
            status.replace(f'Superuser "{user.username}" created.')
            return True
        except SuperuserCreationError as e:
            status.replace(str(e))
            return False
