from inspect import cleandoc
import aiodocker
from chrisomatic.spec.common import User
from chrisomatic.core.docker import find_cube


async def create_superuser(docker: aiodocker.Docker, user: User) -> None:
    cube = await find_cube(docker)
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
    # exec = await cube.exec(cmd)
    # await exec.start(detach=True)
    # cmd = ('python', '-c', 'print("hello from container")')
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
