import pytest
from typing import TypedDict

import aiodocker
import aiohttp
import pytest
from aiochris.types import ChrisURL, Username, Password
from pytest_asyncio import is_async_test


# N.B.: We're doing wacky things with asyncio, pytest, and aiohttp here.
# In our tests, notably in test_client.py, I want to use a session-scoped
# fixture to create a new CUBE user account. In order to do so, we need
# the definitions below for session and pytest_collection_modifyitems.


@pytest.fixture(scope="session")
async def session() -> aiohttp.ClientSession:
    async with aiohttp.ClientSession() as session:
        yield session


def pytest_collection_modifyitems(items):
    """
    See https://pytest-asyncio.readthedocs.io/en/latest/how-to-guides/run_session_tests_in_same_loop.html
    """
    pytest_asyncio_tests = (item for item in items if is_async_test(item))
    session_scope_marker = pytest.mark.asyncio(scope="session")
    for async_test in pytest_asyncio_tests:
        async_test.add_marker(session_scope_marker, append=False)


@pytest.fixture(scope="session")
async def docker():
    async with aiohttp.UnixConnector("/var/run/docker.sock") as connector:
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
def cube_url(in_docker_network: bool):
    if in_docker_network:
        return minichris_cube_url
    return ChrisURL("http://localhost:8000/api/v1/")


class UserCredentials(TypedDict):
    username: Username
    password: Password


@pytest.fixture(scope="session")
def cube_superuser() -> UserCredentials:
    return {"username": Username("chris"), "password": Password("chris1234")}
