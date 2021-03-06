import asyncio
import aiohttp
import aiodocker
from typing import Sequence, AsyncContextManager, TypeVar, Type, Optional
from dataclasses import dataclass, field
from chris.common.types import ChrisURL
from chris.common.deserialization import CreatedUser
from chris.common.client import AbstractClient, AuthenticatedClient
from chris.cube.client import CubeClient
from chris.store.client import AnonymousChrisStoreClient
from chrisomatic.spec.common import User

A = TypeVar("A", bound=AuthenticatedClient)


@dataclass(frozen=True)
class OmniClient(AsyncContextManager["OmniClient"]):
    """
    A wrapper around a `CubeClient` that represents a *CUBE* superuser,
    and some ChRIS store clients as well.

    I.e. `OmniClient` does everything.
    """

    cube: CubeClient
    docker: Optional[aiodocker.Docker]
    store_url: Optional[ChrisURL]
    session: aiohttp.ClientSession
    public_stores: Sequence[AnonymousChrisStoreClient]
    _other_clients: list[AbstractClient] = field(default_factory=list)

    async def create_user(
        self, url: ChrisURL, user: User, client_class: Type[AuthenticatedClient]
    ) -> CreatedUser:
        user = await client_class.create_user(
            url=url,
            username=user.username,
            password=user.password,
            email=user.email,
            session=self.session,
        )
        return user

    async def create_client(
        self, url: ChrisURL, user: User, client_class: Type[A]
    ) -> A:
        client = await client_class.from_login(
            url=url,
            username=user.username,
            password=user.password,
            connector=self.cube.s.connector,
            connector_owner=False,
        )
        self._other_clients.append(client)
        return client

    @property
    def _all_clients(self) -> Sequence[AbstractClient | aiohttp.ClientSession]:
        clients = [self.cube, *self.public_stores, *self._other_clients]
        if self.docker is not None:
            clients.append(self.docker)
        return clients

    async def close(self):
        await asyncio.gather(*(c.close() for c in self._all_clients))

    async def __aenter__(self) -> "OmniClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
