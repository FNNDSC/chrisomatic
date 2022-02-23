import aiodocker
from chrisomatic.core.superuser import find_cube, create_superuser
from chrisomatic.spec.common import User
from chris.common.types import ChrisUsername, ChrisPassword


async def test_find_cube(docker: aiodocker.Docker):
    cube_container = await find_cube(docker)
    container_info = await cube_container.show()
    assert 'fnndsc/chris' in container_info['Config']['Image']
    assert '8000/tcp' in container_info['NetworkSettings']['Ports']
    assert container_info['Config']['WorkingDir'] == '/home/localuser/chris_backend'

#
# async def test_create_superuser(docker: aiodocker.Docker):
#     user = User(username=ChrisUsername('chrisagain'),
#                 password=ChrisPassword('chrisagain1234'))
#     await create_superuser(docker, user)
#
#
# async def test_create_whatever():
#     from chris.cube.client import CubeClient
#     await CubeClient.from_login(
#         url='http://localhost:8000/api/v1/',
#         username='bubba',
#         password='bubba1234'
#     )
