import enum
from rich.console import RenderableType
from rich.text import Text
from rich.emoji import Emoji
from rich.style import Style


class Outcome(enum.Enum):
    FAILED = "failed"
    NO_CHANGE = "no change"
    CHANGE = "changed"

    @property
    def emoji(self) -> RenderableType:
        return _ICONS[self]

    @property
    def style(self) -> Style:
        return _STYLES[self]


__green_check = Text.from_markup(":heavy_check_mark:")
__green_check.stylize("bold green")


_ICONS: dict[Outcome, RenderableType] = {
    Outcome.FAILED: Emoji("x"),
    Outcome.NO_CHANGE: Emoji("heavy_minus_sign"),
    Outcome.CHANGE: __green_check,
}

_STYLES: dict[Outcome, Style] = {
    Outcome.FAILED: Style(color="red", bold=True),
    Outcome.NO_CHANGE: Style(color="green"),
    Outcome.CHANGE: Style(color="cyan"),
}
