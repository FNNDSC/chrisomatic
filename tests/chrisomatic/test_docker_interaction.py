import aiodocker
from chrisomatic.action.docker import find_cube


async def test_find_cube(docker: aiodocker.Docker):
    cube_container = await find_cube(docker)
    container_info = await cube_container.show()
    assert 'fnndsc/chris' in container_info['Config']['Image']
    assert '8000/tcp' in container_info['NetworkSettings']['Ports']
    assert container_info['Config']['WorkingDir'] == '/home/localuser/chris_backend'
