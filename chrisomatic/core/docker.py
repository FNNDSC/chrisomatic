"""
Docker-related helpers.
"""
from typing import Optional, Sequence, AsyncContextManager
import aiodocker
from contextlib import asynccontextmanager
from aiodocker.containers import DockerContainer

_CHRIS_ROLE = {
    'label': {
        'org.chrisproject.role=ChRIS ultron backEnd': True
    }
}


async def find_cube(docker: aiodocker.Docker,
                    ) -> Optional[DockerContainer]:
    """
    Find the container with the label `org.chrisproject.role=ChRIS ultron backEnd`
    """
    results = await docker.containers.list(filters=_CHRIS_ROLE, limit=1)
    if len(results) > 1:
        raise MultipleContainersFoundError(results)
    if len(results) == 1:
        return results[0]
    return None


class MultipleContainersFoundError(Exception):
    pass


@asynccontextmanager
async def run_rm(docker: aiodocker.Docker,
                 image: str, cmd: Sequence[str]) -> AsyncContextManager[DockerContainer]:
    try:
        container = await docker.containers.run({
            'Image': image, 'Cmd': cmd
        })
    except aiodocker.DockerContainerError as e:
        container_id = e.args[-1]
        container = await docker.containers.get(container_id)
        await container.delete()
        raise e
    try:
        yield container
    finally:
        await container.delete()


async def check_output(docker: aiodocker.Docker,
                       image: str, cmd: Sequence[str]) -> str:
    """
    Run a command in a container and return the logs from stdout.

    Raises
    ------
    NonZeroExitCodeError: exit code is not 0
    """
    async with run_rm(docker, image, cmd) as container:
        await container.wait()
        info = await container.show()
        if info['State']['ExitCode'] != 0:
            raise NonZeroExitCodeError(info)
        output = await container.log(stdout=True)
        return ''.join(output)


async def get_cmd(docker: aiodocker.Docker, image: str) -> list[str]:
    info = await docker.images.inspect(image)
    return info['Config']['Cmd']


class NonZeroExitCodeError(Exception):
    pass
