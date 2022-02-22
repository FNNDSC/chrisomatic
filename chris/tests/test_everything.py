import pytest
import time
import aiohttp
from pathlib import Path
from contextlib import asynccontextmanager
from chris.common.types import ChrisURL
from typing import Type, TypeVar
from chris.common.client import AuthenticatedClient, AuthenticatedCollectionLinks, generic_of
from chris.common.deserialization import CreatedUser
from chris.cube.client import CubeClient
from chris.cube.types import ComputeResourceName
from chris.store.client import AnonymousChrisStoreClient, ChrisStoreClient
from chris.tests.examples.plugin_description import pl_nums2mask

C = TypeVar('C', bound=AuthenticatedClient)


async def test_anonymous_chris_store(session: aiohttp.ClientSession):
    cm = await AnonymousChrisStoreClient.from_url(
        'https://chrisstore.co/api/v1/',
        connector=session.connector,
        connector_owner=False
    )
    async with cm as c:
        plugin = await c.get_first_plugin(name_exact='pl-lungct')
        assert plugin.name == 'pl-lungct'
    assert not session.connector.closed


@pytest.fixture()
def some_name() -> str:
    return str(int(time.time()))


@asynccontextmanager
async def create_user_and_client(session: aiohttp.ClientSession, client_type: Type[C],
                                 api_url: ChrisURL, unique_name: str) -> C:
    username = f'test-user-{unique_name}'
    password = 'test1234'
    user = await client_type.create_user(
        url=api_url,
        username=username,
        password=password,
        email=f'user{unique_name}@example.com',
        session=session
    )
    assert isinstance(user, CreatedUser)

    client = await client_type.from_login(
        url=api_url,
        username=username,
        password=password,
        connector=session.connector,
        connector_owner=False
    )
    assert isinstance(client, client_type)
    client_links_type = generic_of(client_type, AuthenticatedCollectionLinks)
    assert isinstance(client.collection_links, client_links_type)
    assert client.collection_links.user == user.url

    yield client
    await client.close()
    assert client.s.closed
    assert not session.closed


@pytest.fixture
async def chris_store_client(session, chris_store_url, some_name) -> ChrisStoreClient:
    async with create_user_and_client(session, ChrisStoreClient, chris_store_url, some_name) as client:
        yield client


@pytest.fixture
async def cube_client(session, cube_url, some_name) -> CubeClient:
    async with create_user_and_client(session, CubeClient, cube_url, some_name) as client:
        yield client


async def test_upload_and_register(chris_store_client: ChrisStoreClient,
                                   normal_cube_client: CubeClient,
                                   # superuser_cube_client: CubeClient,
                                   some_name: str, example_plugin: Path):
    dock_image = f'localhost/fnndsc/pl-nums2mask:{some_name}'
    uploaded_plugin = await chris_store_client.upload_plugin(
        name=f'test-{some_name}',
        dock_image=dock_image,
        public_repo=f'https://github.com/FNNDSC/{some_name}',
        descriptor_file=example_plugin
    )
    get_uploaded = await chris_store_client.get_first_plugin(dock_image=dock_image)
    assert uploaded_plugin.id == get_uploaded.id

    # TODO
    # registered_plugin = await cube_client.register_plugin(get_uploaded.url, ComputeResourceName('host'))
    # assert registered_plugin.dock_image == dock_image


@pytest.fixture
def example_plugin(tmp_path: Path) -> Path:
    file = tmp_path.with_suffix('.json')
    file.write_text(pl_nums2mask)
    return file
