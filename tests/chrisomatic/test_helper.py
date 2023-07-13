from aiochris.types import PluginName, ImageTag

from chrisomatic.core.plugins import InferredPluginInfo
from chrisomatic.spec.given import GivenCubePlugin


def test_inferred_plugin_info():
    actual = InferredPluginInfo.from_given(
        GivenCubePlugin(dock_image=ImageTag("pl-py"))
    )
    expected = InferredPluginInfo(
        PluginName("pl-py"), ImageTag("pl-py"), "https://github.com/pl-py"
    )
    assert actual == expected

    actual = InferredPluginInfo.from_given(
        GivenCubePlugin(dock_image=ImageTag("fnndsc/pl-py"))
    )
    expected = InferredPluginInfo(
        PluginName("pl-py"), ImageTag("fnndsc/pl-py"), "https://github.com/fnndsc/pl-py"
    )
    assert actual == expected

    actual = InferredPluginInfo.from_given(
        GivenCubePlugin(dock_image=ImageTag("localhost/fnndsc/pl-py"))
    )
    expected = InferredPluginInfo(
        PluginName("pl-py"),
        ImageTag("localhost/fnndsc/pl-py"),
        "https://github.com/fnndsc/pl-py",
    )
    assert actual == expected

    actual = InferredPluginInfo.from_given(
        GivenCubePlugin(dock_image=ImageTag("fnndsc/pl-py:latest"))
    )
    expected = InferredPluginInfo(
        PluginName("pl-py"),
        ImageTag("fnndsc/pl-py:latest"),
        "https://github.com/fnndsc/pl-py",
    )
    assert actual == expected
