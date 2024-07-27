"""
Helpers for getting the ChRIS plugin JSON description from a container image.
"""
from typing import Optional, Callable, Awaitable, Sequence

import aiodocker
from rich.text import Text

from chrisomatic.core.docker import (
    rich_pull_if_missing,
    PullResult,
    get_cmd,
    check_output,
    NonZeroExitCodeError,
)
from chrisomatic.framework.task import Channel
from chrisomatic.spec.given import GivenCubePlugin


async def try_obtain_json_description(
    docker: Optional[aiodocker.Docker], plugin: GivenCubePlugin, status: Channel
) -> Optional[str]:
    """
    Attempt to use Docker to run containers of the plugin to extract its JSON description.
    """
    if docker is None:
        status.replace("Docker not available")
        return None
    if plugin.dock_image is None:
        status.replace("Unknown image name")
        return None
    pull_result = await rich_pull_if_missing(docker, plugin.dock_image, status)
    if pull_result == PullResult.error:
        return None
    if pull_result == PullResult.pulled:
        status.keep_current()
    guessing_methods: list[
        Callable[
            [aiodocker.Docker, GivenCubePlugin, Channel],
            Awaitable[Optional[str]],
        ]
    ] = [
        _json_from_chris_plugin_info_post030,
        _json_from_chris_plugin_info_pre030,
        _json_from_old_chrisapp,
    ]
    for guess_method in guessing_methods:
        json_representation = await guess_method(docker, plugin, status)
        if json_representation is not None:
            return json_representation
    return None


async def _json_from_chris_plugin_info_post030(
    docker: aiodocker.Docker, plugin: GivenCubePlugin, status: Channel
) -> Optional[str]:
    """
    Run `chris_plugin_info` with its usage since version 0.3.0
    """
    command = ["chris_plugin_info", "--dock-image", plugin.dock_image]
    if plugin.public_repo:
        command.extend(["--public-repo", plugin.public_repo])
    if plugin.name:
        command.extend(["--name", plugin.name])
    return await _try_run(docker, plugin, status, command)


async def _json_from_chris_plugin_info_pre030(
    docker: aiodocker.Docker, plugin: GivenCubePlugin, status: Channel
) -> Optional[str]:
    """
    Run `chris_plugin_info` with its usage from before version 0.3.0
    """
    return await _try_run(docker, plugin, status, ("chris_plugin_info",))


async def _json_from_old_chrisapp(
    docker: aiodocker.Docker, plugin: GivenCubePlugin, status: Channel
) -> Optional[str]:
    cmd = await get_cmd(docker, plugin.dock_image)
    if len(cmd) == 0:
        return None
    return await _try_run(docker, plugin, status, (cmd[0], "--json"))


async def _try_run(
    docker: aiodocker.Docker,
    plugin: GivenCubePlugin,
    status: Channel,
    command: Sequence[str],
) -> Optional[str]:
    msg = Text("Running ")
    msg.append(" ".join(command), style="yellow")
    status.replace(msg)
    try:
        return await check_output(docker, plugin.dock_image, command)
    except aiodocker.DockerContainerError:
        return None
    except NonZeroExitCodeError:
        return None
