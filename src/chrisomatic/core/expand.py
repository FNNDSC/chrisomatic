import asyncio
import dataclasses
from typing import Optional

from aiodocker import Docker, DockerError

from aiochris.types import ImageTag, Username
from chrisomatic.spec.given import GivenCubePlugin, GivenConfig, ExpandedConfig


async def smart_expand_config(
    given_config: GivenConfig,
    docker: Docker,
) -> ExpandedConfig:
    """
    Expand the given config, i.e. fill in default values, but use information
    we are able to obtain using Docker to make better choices.

    Specifically, what that means is that:

    - if a plugin string is a docker image known by the docker daemon, then mark it as such
    - if a plugin's owner is not specified, provide a default value
    - TODO add all required plugins from pipelines to plugin list
    """
    resolved_plugins: tuple[str | GivenCubePlugin, ...] = await asyncio.gather(
        *(mark_if_is_image(docker, plugin) for plugin in given_config.cube.plugins)
    )
    realized_config: GivenConfig = dataclasses.replace(
        given_config,
        cube=dataclasses.replace(given_config.cube, plugins=list(resolved_plugins)),
    )
    return realized_config.expand()


async def mark_if_is_image(
    docker: Optional[Docker], plugin: str | GivenCubePlugin
) -> str | GivenCubePlugin:
    if isinstance(plugin, GivenCubePlugin):
        return plugin
    if docker is None:
        return plugin
    if await is_local_image(docker, plugin):
        return GivenCubePlugin(dock_image=ImageTag(plugin))
    return plugin


async def is_local_image(docker: Docker, name: str) -> bool:
    if "://" in name:
        return False
    try:
        await docker.images.inspect(name)
        return True
    except DockerError:
        return False
