import asyncio
import aiohttp
import aiodocker
from typing import Optional, Sequence
import dataclasses
from chris.common.types import ChrisURL
from chris.common.errors import IncorrectLoginError
from chris.cube.client import CubeClient
from chris.store.client import AnonymousChrisStoreClient
from chrisomatic.core.superuser import create_superuser
from chrisomatic.core.superclient import SuperClient
from chrisomatic.framework.outcome import Outcome
from chrisomatic.framework.task import ChrisomaticTask, State
from chrisomatic.spec.given import On


@dataclasses.dataclass(frozen=True)
class SuperClientFactory(ChrisomaticTask[SuperClient]):

    on: On
    connector: Optional[aiohttp.BaseConnector] = None
    connector_owner: bool = True
    docker: aiodocker.Docker = dataclasses.field(default_factory=aiodocker.Docker)
    attempt: int = 0

    def initial_state(self) -> State:
        user = self.on.chris_superuser
        return State(
            title=f'superuser ({user.username})',
            status=f'checking for superuser: username={user.username}'
        )

    async def run(self, emit: State) -> tuple[Outcome, Optional[SuperClient]]:
        """
        Constructor for `SuperClient`.
        Create a `CubeClient` with the given superuser credentials.
        If that superuser does not exist, try to create it first.
        """
        user = self.on.chris_superuser
        try:
            cube = await CubeClient.from_login(
                url=self.on.cube_url,
                username=user.username,
                password=user.password,
                connector=self.connector,
                connector_owner=self.connector_owner
            )
            emit.status = 'connected!'
            outcome = Outcome.NO_CHANGE
            superclient = await self.__from_client(cube, emit)
        except IncorrectLoginError:
            if self.attempt >= 1:
                # previously tried to create new superuser, but still
                # unable to log in as them
                emit.status = 'Did not create superuser.'
                return Outcome.FAILED, None

            # couldn't log in as superuser, so create new superuser
            emit.status = f'Creating superuser "{user.username}" ...'
            await create_superuser(self.docker, user)
            emit.status = f'Superuser "{user.username}" created.'
            second_attempt = dataclasses.replace(self, attempt=self.attempt + 1)
            outcome, superclient = second_attempt.run(emit)
            if outcome != Outcome.FAILED:
                outcome = Outcome.CHANGE
                emit.status = f'created new superuser: "{user.username}"'
        return outcome, superclient

    async def __from_client(
            self,
            cube_client: CubeClient,
            emit: State
    ) -> SuperClient:
        """
        Use the created `cube_client`'s `aiohttp.BaseConnector` to create everything else.
        """
        emit.status = 'connecting to ChRIS store...'
        stores = await self.__public_store_clients(self.on.public_store, cube_client.s.connector)
        emit.status = 'creating session...'
        session = aiohttp.ClientSession(connector=cube_client.s.connector,
                                        connector_owner=False)
        emit.status = 'created session.'
        return SuperClient(
            cube=cube_client,
            docker=self.docker,
            store_url=self.on.chris_store_url,
            session=session,
            public_stores=stores
        )

    @staticmethod
    async def __public_store_clients(stores: Sequence[ChrisURL],
                                     connector: aiohttp.BaseConnector
                                     ) -> Sequence[AnonymousChrisStoreClient]:
        """
        Create `AnonymousChrisStoreClient` from the given public _ChRIS_ store URLs.
        """
        return await asyncio.gather(*(AnonymousChrisStoreClient.from_url(
            url=url,
            connector=connector,
            connector_owner=False
        ) for url in stores))
