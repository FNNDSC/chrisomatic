from pathlib import Path
import asyncio
import aiohttp
from typing import AsyncContextManager
from chris.store.client import AnonymousChrisStoreClient, ChrisStoreClient
from chris.common.types import ChrisToken, ChrisURL
import time


desc_json = Path('/hdd/neuro/fnndsc/pl-dypi/chris_plugin_info.json')
localhost = ChrisURL('http://localhost:8010/api/v1/')


async def main():
    print('started main')
    # cm = await AnonymousChrisStoreClient.from_url('https://chrisstore.co/api/v1/')
    # async with cm as c:
    #     print(await c.get_first_plugin(name_exact='pl-lungct'))

    cm = await ChrisStoreClient.from_login(
        url='http://localhost:8010/api/v1/',
        username='aaaa3',
        password='aaa12345'
    )

    async with cm as client:
        r = await client.upload_plugin(name='pl-dypi2',
                                       dock_image='localhost/rudolph/pl-dypi:1.2.1',
                                       public_repo='https://github.com/FNNDSC/pl-dypi',
                                       descriptor_file=desc_json)
        print(r)

    # async with aiohttp.ClientSession() as session:
    #     d = await ChrisStoreClient.create_user(
    #         url='http://localhost:8010/api/v1/',
    #         username='aaaa3',
    #         password='aaa12345',
    #         email='a3@example.com',
    #         session=session
    #     )
    #     print(d)

asyncio.run(main())
