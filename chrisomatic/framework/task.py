import abc
from typing import TypeVar, Generic, Optional
from dataclasses import dataclass, field, InitVar
from chrisomatic.framework.outcome import Outcome
from rich.console import RenderableType, Group
from rich.highlighter import ReprHighlighter
from rich.text import Text

_R = TypeVar("_R")
highlighter = ReprHighlighter()


@dataclass
class Channel:
    """
    A channel for a task to communicate status/progress information during `ChrisomaticTask.run` to some live display.
    """

    title: str
    first_status: InitVar[Optional[RenderableType]]
    __rows: list[RenderableType] = field(init=False, default_factory=list)

    def __post_init__(self, first_status: Optional[RenderableType]):
        if first_status is not None:
            self.append(first_status)

    def render(self) -> RenderableType:
        return Group(*self.__rows)

    def append(self, s: RenderableType) -> None:
        """Append to this status."""
        highlighted = self.__highlight(s)
        self.__rows.append(highlighted)

    def replace(self, s: RenderableType) -> None:
        """Set a new status."""
        self.__rows.clear()
        self.append(s)

    @staticmethod
    def __highlight(s: RenderableType) -> RenderableType:
        if isinstance(s, (int, float, bool, str, list, tuple, set, frozenset)):
            text = Text(str(s))
            highlighter.highlight(text)
            return text
        return s


class ChrisomaticTask(abc.ABC, Generic[_R]):
    """
    A single task to do.
    """

    @abc.abstractmethod
    async def run(self, status: Channel) -> tuple[Outcome, Optional[_R]]:
        ...

    @abc.abstractmethod
    def first_status(self) -> tuple[str, RenderableType]:
        """
        Returns the title and initial status text for this task.
        """
        ...
