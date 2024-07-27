from inspect import cleandoc
from typing import Optional

import aiodocker
from chrisomatic.spec.common import User
from chrisomatic.core.docker import find_cube, BACKEND_CONTAINER_LABEL


async def create_superuser(docker: Optional[aiodocker.Docker], user: User) -> None:
    if docker is None:
        raise SuperuserCreationError(
            "Cannot create superuser without connection to Docker."
        )
    if (cube := await find_cube(docker)) is None:
        raise SuperuserCreationError(
            f"No container found on host {docker.docker_host} "
            f"with label {BACKEND_CONTAINER_LABEL}"
        )
    script = cleandoc(
        f"""
        from django.contrib.auth.models import User
        user = User.objects.create_superuser(username="{user.username}",
                                             password="{user.password}",
                                             email="{user.email}")
        print(user.username, end='')
        """
    )
    cmd = ("python", "manage.py", "shell", "-c", script)
    exec_instance = await cube.exec(cmd)
    async with exec_instance.start(detach=False) as stream:
        output_message = await stream.read_out()
        output_bytes = output_message.data
        output: str = output_bytes.decode("utf-8")
        if output != user.username:
            raise SuperuserCreationError(
                f"Failed to create user: {user}." "Exec output:\n", output
            )


class SuperuserCreationError(Exception):
    pass
