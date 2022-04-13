import asyncio
import time
import pytest
import aiodocker
from chrisomatic.core.docker import (
    find_cube,
    check_output,
    run_rm,
    get_cmd,
    has_image,
    parse_image_tag,
    NonZeroExitCodeError,
)
from chrisomatic.core.expand import is_local_image


async def test_find_cube(docker: aiodocker.Docker):
    cube_container = await find_cube(docker)
    container_info = await cube_container.show()
    # I've renamed the container for some builds...
    # We should remove one or the other in the near future.
    assert "fnndsc/chris" in container_info["Config"]["Image"] \
        or "fnndsc/cube" in container_info["Config"]["Image"]
    assert "8000/tcp" in container_info["NetworkSettings"]["Ports"]
    assert container_info["Config"]["WorkingDir"] == "/home/localuser/chris_backend"


@pytest.fixture(scope="session")
async def example_images(docker: aiodocker.Docker) -> tuple[str, str]:
    await docker.images.pull("docker.io/library/hello-world:latest")
    await docker.images.tag(
        "docker.io/library/hello-world:latest", "localhost/chrisomatic/test"
    )
    yield "docker.io/library/hello-world:latest", "localhost/chrisomatic/test"
    await docker.images.delete("localhost/chrisomatic/test")


async def test_is_local_image(
    docker: aiodocker.Docker, example_images: tuple[str, str]
):
    example1, example2 = example_images
    assert await is_local_image(docker, example1)
    assert await is_local_image(docker, example2)
    assert not await is_local_image(docker, "docker.io/chrisomatic/dne")
    assert not await is_local_image(docker, "https://chrisstore.co/api/v1/")


async def test_check_output_nonzero(docker: aiodocker.Docker):
    with pytest.raises(NonZeroExitCodeError):
        await check_output(docker, "alpine", ("sh", "-c", "false"))


async def test_check_output(docker: aiodocker.Docker):
    assert (
        await check_output(docker, "alpine", ("printf", "hello dude")) == "hello dude"
    )
    assert (
        await check_output(docker, "alpine", ("printf", r"hello\ndude"))
        == "hello\ndude"
    )


async def test_get_cmd(docker: aiodocker.Docker):
    assert await get_cmd(docker, "postgres:13") == ["postgres"]
    assert await get_cmd(docker, "rabbitmq:3") == ["rabbitmq-server"]


# async def test_run_rm(docker: aiodocker.Docker):
#     assert container removed afterwards


async def test_run_rm(docker: aiodocker.Docker):
    message = "it is wednesday my dude"
    command = ["printf", message]
    async with run_rm(docker, "alpine", command) as container:
        info = await container.show()
        container_id = info["Id"]
        await docker.containers.get(container_id)  # make sure the container exists
        await container.wait()
        output = await container.log(stdout=True)
        assert output[0] == message

    # assert container was removed
    with pytest.raises(aiodocker.DockerError) as exception:
        await docker.containers.get(container_id)
    assert exception.value.args == (
        404,
        {"message": f"No such container: {container_id}"},
    )


async def test_run_rm_command_not_found(docker: aiodocker.Docker):
    command = f"command_which_doesnt_exist_{time.time()}"
    with pytest.raises(aiodocker.DockerError):
        async with run_rm(docker, "alpine", [command]):
            pytest.fail("Should not be able to run a command which does not exist")

    # check if it's been removed
    created_containers = await docker.containers.list(filters={"status": ["created"]})
    created_containers_info = await asyncio.gather(
        *(c.show() for c in created_containers)
    )
    for info in created_containers_info:
        if command in info["Config"]["Cmd"]:
            pytest.fail(f'Container not removed: {info["Id"]}')


async def test_has_image(docker: aiodocker.Docker):
    a_tag = f"localhost/whatever/something:{time.time()}"
    assert not await has_image(docker, a_tag)
    try:
        await docker.images.tag("alpine:latest", a_tag)
        assert await has_image(docker, a_tag)
    finally:
        await docker.images.delete(a_tag)


def test_parse_image_tag(docker: aiodocker.Docker):
    assert parse_image_tag("python:3") == ("python", "3")
    assert parse_image_tag("python:3.10") == ("python", "3.10")
    assert parse_image_tag("python:latest") == ("python", "latest")
    assert parse_image_tag("python") == ("python", "latest")
    assert parse_image_tag("python:latest:3") is None
