import time
import aiohttp
from chris.common.types import ChrisURL
from chris.common.deserialization import CreatedUser
from chris.cube.client import CubeClient
from chris.cube.deserialization import CubeCollectionLinks

cube_url = ChrisURL('http://localhost:8000/api/v1/')


async def test_cube_client(session: aiohttp.ClientSession):
    unique_name = str(int(time.time()))
    username = f'test-user-{unique_name}'
    password = 'test1234'
    user = await CubeClient.create_user(
        url=cube_url,
        username=username,
        password=password,
        email=f'user{unique_name}@example.com',
        session=session
    )
    assert isinstance(user, CreatedUser)

    client = await CubeClient.from_login(
        url=cube_url,
        username=username,
        password=password,
        connector=session.connector,
        connector_owner=False
    )
    assert isinstance(client, CubeClient)
    assert isinstance(client.collection_links, CubeCollectionLinks)
    assert client.collection_links.user == user.url
