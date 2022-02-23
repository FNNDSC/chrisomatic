import asyncio
import aiohttp
import aiodocker
from typing import Sequence, AsyncContextManager
from dataclasses import dataclass
from chris.common.types import ChrisURL
from chris.cube.client import CubeClient
from chris.store.client import AnonymousChrisStoreClient, ChrisStoreClient
from chrisomatic.spec.common import User


@dataclass(frozen=True)
class SuperClient(AsyncContextManager['SuperClient']):
    """
    A wrapper around a `CubeClient` that represents a _CUBE_ superuser.
    It can do everything you want.
    """

    cube: CubeClient
    docker: aiodocker.Docker
    store_url: ChrisURL
    session: aiohttp.ClientSession
    public_stores: Sequence[AnonymousChrisStoreClient]

    async def create_store_user(self, user: User) -> ChrisStoreClient:
        """
        Create a `ChrisStoreClient` using the same `aiohttp.BaseConnector`
        as the one used by this client's `CubeClient`.
        """
        user = await ChrisStoreClient.create_user(
            url=self.store_url,
            username=user.username,
            password=user.password,
            email=user.email,
            session=self.session
        )
        return await ChrisStoreClient.from_login(
            url=self.store_url,
            username=user.username,
            password=user.password,
            connector=self.cube.s.connector,
            connector_owner=False
        )

    async def close(self):
        await asyncio.gather(
            self.cube.close(),
            self.docker.close(),
            *(s.close() for s in self.public_stores)
        )

    async def __aenter__(self) -> 'SuperClient':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
