import asyncio
import dataclasses
from typing import Optional, Sequence

import aiodocker
import aiohttp

from chris.common.errors import IncorrectLoginError, ResponseError
from chris.common.types import ChrisURL
from chris.cube.client import CubeClient
from chris.store.client import AnonymousChrisStoreClient
from chrisomatic.core.omniclient import OmniClient
from chrisomatic.core.superuser import create_superuser, SuperuserCreationError
from chrisomatic.framework.outcome import Outcome
from chrisomatic.framework.task import ChrisomaticTask, State
from chrisomatic.spec.given import On


@dataclasses.dataclass(frozen=True)
class OmniClientFactory(ChrisomaticTask[OmniClient]):

    on: On
    docker: aiodocker.Docker
    connector: Optional[aiohttp.BaseConnector] = None
    connector_owner: bool = True
    attempt: int = 0

    def initial_state(self) -> State:
        user = self.on.chris_superuser
        return State(
            title=f"superuser ({user.username})",
            status=f"checking for superuser: username={user.username}",
        )

    async def run(self, emit: State) -> tuple[Outcome, Optional[OmniClient]]:
        """
        Constructor for `OmniClient`.
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
                connector_owner=self.connector_owner,
            )
            emit.status = "connected!"
            outcome = Outcome.NO_CHANGE

            omniclient = await self.__from_client(cube, emit)
            if omniclient is None:
                await asyncio.gather(cube.close(), self.docker.close())
                return Outcome.FAILED, None
        except ResponseError as e:
            emit.status = str(e)
            await self.docker.close()
            return Outcome.FAILED, None
        except IncorrectLoginError:
            if self.attempt >= 1:
                # previously tried to create new superuser, but still
                # unable to log in as them
                emit.status = "Did not create superuser."
                return Outcome.FAILED, None

            # couldn't log in as superuser, so create new superuser
            emit.status = f'Creating superuser "{user.username}" ...'
            try:
                await create_superuser(self.docker, user)
            except SuperuserCreationError as e:
                emit.status = str(e)
                return Outcome.FAILED, None
            emit.status = f'Superuser "{user.username}" created.'
            second_attempt = dataclasses.replace(self, attempt=self.attempt + 1)
            outcome, omniclient = await second_attempt.run(emit)
            if outcome != Outcome.FAILED:
                outcome = Outcome.CHANGE
                emit.status = f'created new superuser: "{user.username}"'
        return outcome, omniclient

    async def __from_client(
        self, cube_client: CubeClient, emit: State
    ) -> Optional[OmniClient]:
        """
        Use the created `cube_client`'s `aiohttp.BaseConnector` to create everything else.
        Returns `None` if connection with any of the public _ChRIS_ stores failed.
        """
        emit.status = "connecting to ChRIS store..."

        try:
            stores = await self.__public_store_clients(
                self.on.public_store, cube_client.s.connector
            )
        except aiohttp.ClientConnectorError as e:
            emit.status = f"Connection to ChRIS store: {e}"
            return None

        emit.status = "creating session..."
        session = aiohttp.ClientSession(
            connector=cube_client.s.connector, connector_owner=False
        )
        emit.status = "created client sessions."
        return OmniClient(
            cube=cube_client,
            docker=self.docker,
            store_url=self.on.chris_store_url,
            session=session,
            public_stores=stores,
        )

    @staticmethod
    async def __public_store_clients(
        stores: Sequence[ChrisURL], connector: aiohttp.BaseConnector
    ) -> Sequence[AnonymousChrisStoreClient]:
        """
        Create `AnonymousChrisStoreClient` from the given public _ChRIS_ store URLs.
        """
        store_clients = await asyncio.gather(
            *(
                AnonymousChrisStoreClient.from_url(
                    url=url, connector=connector, connector_owner=False
                )
                for url in stores
            ),
            return_exceptions=True,
        )

        exceptions = [c for c in store_clients if isinstance(c, Exception)]
        if exceptions:
            await asyncio.gather(
                *(
                    client.close()
                    for client in store_clients
                    if hasattr(client, "close") and callable(client.close)
                )
            )
            raise exceptions[0]

        return store_clients
