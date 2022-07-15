from typing import Optional, Type
from dataclasses import dataclass

from chris.common.types import ChrisURL
from chris.common.client import AuthenticatedClient
from chris.common.errors import IncorrectLoginError, ResponseError
from chrisomatic.spec.common import User
from chrisomatic.framework.task import ChrisomaticTask, State, Outcome
from chrisomatic.core.omniclient import OmniClient, A


@dataclass
class CreateUsersTask(ChrisomaticTask[A]):
    omniclient: OmniClient
    url: ChrisURL
    user: User
    user_type: Type[A]

    def initial_state(self) -> State:
        return State(title=self.user.username, status="checking if user exists...")

    async def run(self, emit: State) -> tuple[Outcome, Optional[A]]:
        try:
            client: AuthenticatedClient = await self.omniclient.create_client(
                self.url, self.user, self.user_type
            )
            emit.status = client.collection_links.user
            return Outcome.NO_CHANGE, client
        except IncorrectLoginError:
            emit.status = "creating user..."
            try:
                await self.omniclient.create_user(self.url, self.user, self.user_type)
            except ResponseError as e:
                emit.status = str(e)
                return Outcome.FAILED, None
            client: AuthenticatedClient = await self.omniclient.create_client(
                self.url, self.user, self.user_type
            )
            emit.status = client.collection_links.user
            return Outcome.CHANGE, client
