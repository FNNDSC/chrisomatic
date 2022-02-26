import asyncio
import pytest
import aiohttp
import aiodocker
from typing import TypedDict
from chris.common.types import ChrisURL, ChrisUsername, ChrisPassword


@pytest.fixture(scope="session")
def event_loop():
    """
    https://stackoverflow.com/questions/56236637/using-pytest-fixturescope-module-with-pytest-mark-asyncio/56238383#56238383
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def session(event_loop) -> aiohttp.ClientSession:
    async with aiohttp.ClientSession(loop=event_loop) as session:
        yield session


@pytest.fixture(scope="session")
async def docker(event_loop):
    async with aiohttp.UnixConnector(
        "/var/run/docker.sock", loop=event_loop
    ) as connector:
        d = aiodocker.Docker(url="unix://localhost", connector=connector)
        await d.images.pull("alpine", tag="latest", stream=False)
        yield d
        await d.close()


minichris_cube_url = ChrisURL("http://chris:8000/api/v1/")


@pytest.fixture(scope="session")
async def in_docker_network(session: aiohttp.ClientSession) -> bool:
    try:
        await session.get(minichris_cube_url + "users/")
        return True
    except aiohttp.ClientConnectorError:
        return False


@pytest.fixture(scope="session")
def chris_store_url(in_docker_network: bool):
    if in_docker_network:
        return ChrisURL("http://chrisstore.local:8010/api/v1/")
    return ChrisURL("http://localhost:8010/api/v1/")


@pytest.fixture(scope="session")
def cube_url(in_docker_network: bool):
    if in_docker_network:
        return minichris_cube_url
    return ChrisURL("http://localhost:8000/api/v1/")


class UserCredentials(TypedDict):
    username: ChrisUsername
    password: ChrisPassword


@pytest.fixture(scope="session")
def cube_superuser() -> UserCredentials:
    return {"username": ChrisUsername("chris"), "password": ChrisPassword("chris1234")}
