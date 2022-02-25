import asyncio
import aiodocker
from chrisomatic.core.docker import find_cube


async def wait_on_cube() -> None:
    async with aiodocker.Docker() as docker:
        container = await find_cube(docker)
        await container.wait()


if __name__ == "__main__":
    asyncio.run(wait_on_cube())
