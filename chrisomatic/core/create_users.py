from dataclasses import dataclass
from typing import Optional

import aiohttp
from aiochris import ChrisClient
from aiochris.errors import BaseClientError, IncorrectLoginError
from aiochris.models.data import UserData
from aiochris.types import ChrisURL
from rich.console import RenderableType

from chrisomatic.framework.task import ChrisomaticTask, Channel, Outcome
from chrisomatic.spec.common import User


@dataclass
class CreateUsersTask(ChrisomaticTask[UserData]):
    url: ChrisURL
    user: User
    connector: Optional[aiohttp.BaseConnector] = None

    def first_status(self) -> tuple[str, RenderableType]:
        return self.user.username, "checking if user exists..."

    async def run(self, status: Channel) -> tuple[Outcome, Optional[UserData]]:
        try:
            if user := await self._login():
                status.replace(user.url)
                return Outcome.NO_CHANGE, user
            user = await self._create_user()
            status.replace(user.url)
            return Outcome.CHANGE, user
        except BaseClientError as e:
            status.replace(f"Error: {e}")
            return Outcome.FAILED, None

    async def _login(self) -> Optional[UserData]:
        """Returns True if the user is able to log in."""
        try:
            user = await ChrisClient.from_login(
                url=self.url,
                username=self.user.username,
                password=self.user.password,
                connector=self.connector,
                connector_owner=False,
            )
            async with user:
                return user
        except IncorrectLoginError:
            return None

    async def _create_user(self) -> Optional[UserData]:
        async with aiohttp.ClientSession(
            connector=self.connector, connector_owner=False
        ) as session:
            return await ChrisClient.create_user(
                url=self.url,
                username=self.user.username,
                password=self.user.password,
                email=self.user.email,
                session=session,
            )
