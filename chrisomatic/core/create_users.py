from typing import Optional, Sequence, Type
from dataclasses import dataclass

import aiohttp
from rich.text import Text
from chris.common.types import ChrisURL
from chris.common.client import AuthenticatedClient
from chris.common.errors import IncorrectLoginError
from chrisomatic.spec.common import User
from chrisomatic.framework.task import ChrisomaticTask, State, Outcome
from chrisomatic.core.superclient import SuperClient, A
from chrisomatic.framework.taskrunner import ProgressTaskRunner


@dataclass
class CreateUsersTask(ChrisomaticTask[A]):
    superclient: SuperClient
    url: ChrisURL
    user: User
    user_type: Type[A]

    def initial_state(self) -> State:
        return State(title=self.user.username, status='checking if user exists...')

    async def run(self, emit: State) -> tuple[Outcome, Optional[A]]:
        try:
            client: AuthenticatedClient = await self.superclient.create_client(self.url, self.user, self.user_type)
            emit.status = client.collection_links.user
            return Outcome.NO_CHANGE, client
        except IncorrectLoginError:
            emit.status = 'creating user...'
            try:
                await self.superclient.create_user(self.url, self.user, self.user_type)
            except aiohttp.ClientResponseError:
                emit.status = Text('failed to create user', style='bold red')
                return Outcome.FAILED, None
            client: AuthenticatedClient = await self.superclient.create_client(self.url, self.user, self.user_type)
            emit.status = client.collection_links.user
            return Outcome.CHANGE, client


async def create_users(superclient: SuperClient,
                       url: ChrisURL,
                       users: Sequence[User],
                       user_type: Type[A],
                       progress_title: str) -> Sequence[tuple[Outcome, A]]:
    runner = ProgressTaskRunner(
        tasks=[CreateUsersTask[user_type](superclient, url, user, user_type) for user in users],
        title=progress_title
    )
    return await runner.apply()
