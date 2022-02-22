import asyncio
import pytest
import aiohttp
from chris.common.types import ChrisURL


@pytest.fixture(scope='session')
def event_loop():
    """
    https://stackoverflow.com/questions/56236637/using-pytest-fixturescope-module-with-pytest-mark-asyncio/56238383#56238383
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def session(event_loop) -> aiohttp.ClientSession:
    async with aiohttp.ClientSession(loop=event_loop) as session:
        yield session


@pytest.fixture(scope='session')
def chris_store_url():
    return ChrisURL('http://localhost:8010/api/v1/')


@pytest.fixture(scope='session')
def cube_url():
    return ChrisURL('http://localhost:8000/api/v1/')
