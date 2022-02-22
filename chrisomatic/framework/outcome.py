import enum
from rich.emoji import Emoji
from rich.style import Style


class Outcome(enum.Enum):
    FAILED = enum.auto()
    NO_CHANGE = enum.auto()
    CHANGE = enum.auto()

    @property
    def emoji(self) -> Emoji:
        return _ICONS[self]

    @property
    def style(self) -> Style:
        return _STYLES[self]


_ICONS: dict[Outcome, Emoji] = {
    Outcome.FAILED: Emoji('x'),
    Outcome.NO_CHANGE: Emoji('heavy_minus_sign'),
    Outcome.CHANGE: Emoji('heavy_check_mark')
}

_STYLES: dict[Outcome, Style] = {
    Outcome.FAILED: Style(color='red', bold=True),
    Outcome.NO_CHANGE: Style(color='green'),
    Outcome.CHANGE: Style(color='cyan')
}
