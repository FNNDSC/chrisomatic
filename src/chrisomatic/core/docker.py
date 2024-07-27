"""
Docker-related helpers.
"""
import enum
from typing import Optional, Sequence, AsyncContextManager
from rich.progress import Progress, TaskID
import aiodocker
from contextlib import asynccontextmanager
from aiodocker.containers import DockerContainer
from chrisomatic.framework.task import Channel


BACKEND_CONTAINER_LABEL = "org.chrisproject.role=ChRIS_ultron_backEnd"
_CHRIS_ROLE = {"label": {BACKEND_CONTAINER_LABEL: True}}


async def find_cube(
    docker: aiodocker.Docker,
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
async def run_rm(
    docker: aiodocker.Docker, image: str, cmd: Sequence[str]
) -> AsyncContextManager[DockerContainer]:
    try:
        container = await docker.containers.run({"Image": image, "Cmd": cmd})
    except aiodocker.DockerContainerError as e:
        container_id = e.args[-1]
        container = await docker.containers.get(container_id)
        await container.delete()
        raise e
    try:
        yield container
    finally:
        await container.delete()


async def check_output(docker: aiodocker.Docker, image: str, cmd: Sequence[str]) -> str:
    """
    Run a command in a container and return the logs from stdout.

    Raises
    ------
    NonZeroExitCodeError: exit code is not 0
    """
    async with run_rm(docker, image, cmd) as container:
        await container.wait()
        info = await container.show()
        if info["State"]["ExitCode"] != 0:
            raise NonZeroExitCodeError(info)
        output = await container.log(stdout=True)
        return "".join(output)


async def get_cmd(docker: aiodocker.Docker, image: str) -> list[str]:
    info = await docker.images.inspect(image)
    return info["Config"]["Cmd"]


class PullResult(enum.Enum):
    not_pulled = "not pulled"
    pulled = "pulled"
    error = "error"


async def has_image(docker: aiodocker.Docker, image: str) -> bool:
    try:
        await docker.images.inspect(image)
        return True
    except aiodocker.DockerError as e:
        if e.args[0] == 404:
            return False
        raise e


async def rich_pull(
    docker: aiodocker.Docker, image: str, status: Channel
) -> PullResult:
    """
    Pull an image, while creating and updating its progress as a
    [`rich.progress.Progress`](https://rich.readthedocs.io/en/latest/progress.html)
    to `emit`. This should be used inside the context of a
    [`rich.live.Live`](https://rich.readthedocs.io/en/latest/live.html).

    `aiodocker.DockerError` (such as 400 "invalid reference format", 404 "not found")
    are caught, and `emit.state` is set to the error message.
    """
    # when pulling via docker API, if tag is not specified, then *all* tags
    # are pulled, and that's definitely not what we want!
    status.title = image
    status.replace("pulling...")
    parsed_image = parse_image_tag(image)
    if parsed_image is None:
        status.replace("invalid tag")
        return PullResult.error
    repo, tag = parsed_image

    # images are pulled in layers, each layer needs to be downloaded and extracted.
    # each layer will be represented by a task of the progress bar.
    layers: dict[str, TaskID] = {}
    progress = Progress()
    status.replace(progress)
    try:
        async for current in docker.images.pull(repo, tag=tag, stream=True):
            if "id" not in current:
                continue
            # noinspection PyShadowingBuiltins
            id = current["id"]
            if id == tag:
                continue
            if id not in layers:
                layers[id] = progress.add_task(f"({id})")
            task = layers[id]
            progress.update(task, description=f'({id}) {current["status"]}')
            # progress.update(task, description=f'[{id}]')
            if not __is_progress_update(current):
                continue
            detail = current["progressDetail"]
            progress.update(
                task,
                description=f'({id}) {current["status"]}',
                completed=detail["current"],
                total=detail["total"],
            )

    except aiodocker.DockerError as e:
        status.replace(str(e))
        return PullResult.error

    return PullResult.pulled


async def rich_pull_if_missing(
    docker: aiodocker.Docker, image: str, status: Channel
) -> PullResult:
    if await has_image(docker, image):
        return PullResult.not_pulled
    return await rich_pull(docker, image, status)


def parse_image_tag(image: str) -> Optional[tuple[str, str]]:
    """
    Split a full image ref, e.g. `"python:3"` into its repo and tag, `('python', '3')`.
    If there is no tag, `":latest"` is assumed.
    If the image ref cannot be parsed, `None` is returned.
    """
    if not isinstance(image, str):
        return None
    if image.count(":") > 1:
        return None
    if ":" in image:
        repo, tag = image.split(":")
        return repo, tag
    return image, "latest"


def __is_progress_update(p: dict) -> bool:
    return (
        "progressDetail" in p
        and "current" in p["progressDetail"]
        and "total" in p["progressDetail"]
    )


class NonZeroExitCodeError(Exception):
    pass
