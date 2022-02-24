import pytest
import aiodocker
from chrisomatic.core.docker import find_cube
from chrisomatic.core.expand import is_local_image


async def test_find_cube(docker: aiodocker.Docker):
    cube_container = await find_cube(docker)
    container_info = await cube_container.show()
    assert 'fnndsc/chris' in container_info['Config']['Image']
    assert '8000/tcp' in container_info['NetworkSettings']['Ports']
    assert container_info['Config']['WorkingDir'] == '/home/localuser/chris_backend'


@pytest.fixture(scope='session')
async def example_images(docker: aiodocker.Docker) -> tuple[str, str]:
    await docker.images.pull('docker.io/library/hello-world:latest')
    await docker.images.tag('docker.io/library/hello-world:latest', 'localhost/chrisomatic/test')
    yield 'docker.io/library/hello-world:latest', 'localhost/chrisomatic/test'
    await docker.images.delete('localhost/chrisomatic/test')


async def test_is_local_image(docker: aiodocker.Docker, example_images: tuple[str, str]):
    example1, example2 = example_images
    assert await is_local_image(docker, example1)
    assert await is_local_image(docker, example2)
    assert not await is_local_image(docker, 'docker.io/chrisomatic/dne')
    assert not await is_local_image(docker, 'https://chrisstore.co/api/v1/')
