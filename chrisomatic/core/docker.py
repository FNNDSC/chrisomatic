from typing import Optional
import aiodocker
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
