import pytest
import aiohttp
import time
from pathlib import Path
from chris.store.client import AnonymousChrisStoreClient, ChrisStoreClient
from chris.store.deserialization import StoreCollectionLinks
from chris.common.types import ChrisURL
from chris.common.deserialization import CreatedUser
from chris.tests.examples.plugin_description import pl_nums2mask

chris_store_url = ChrisURL('http://localhost:8010/api/v1/')


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


async def test_chris_store_client(session: aiohttp.ClientSession, example_plugin: Path):
    unique_name = str(int(time.time()))
    username = f'test-user-{unique_name}'
    password = 'test1234'
    user = await ChrisStoreClient.create_user(
        url=chris_store_url,
        username=username,
        password=password,
        email=f'user{unique_name}@example.com',
        session=session
    )
    assert isinstance(user, CreatedUser)

    client = await ChrisStoreClient.from_login(
        url=chris_store_url,
        username=username,
        password=password,
        connector=session.connector,
        connector_owner=False
    )
    assert isinstance(client, ChrisStoreClient)
    assert isinstance(client.collection_links, StoreCollectionLinks)
    assert client.collection_links.user == user.url

    dock_image = f'localhost/fnndsc/pl-nums2mask:{unique_name}'
    uploaded_plugin = await client.upload_plugin(
        name=f'test-{unique_name}',
        dock_image=dock_image,
        public_repo=f'https://github.com/FNNDSC/{unique_name}',
        descriptor_file=example_plugin
    )
    get_uploaded = await client.get_first_plugin(dock_image=dock_image)
    assert uploaded_plugin.id == get_uploaded.id

    await client.close()


@pytest.fixture
def example_plugin(tmp_path: Path) -> Path:
    file = tmp_path.with_suffix('.json')
    file.write_text(pl_nums2mask)
    return file
