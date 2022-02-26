import abc
from typing import TypeVar, Generic, Optional
from dataclasses import dataclass, InitVar, field
from chrisomatic.framework.outcome import Outcome
from rich.console import RenderableType
from rich.console import Group
from rich.highlighter import ReprHighlighter
from rich.text import Text

_R = TypeVar("_R")
highlighter = ReprHighlighter()


@dataclass
class State:
    """
    Mutable object used to relay information between `ChrisomaticTask.run`
    and a live display.

    When setting its `status` property while `append=False`, its status will be overwritten.
    But when `append=True`, setting `status` will instead append it to a list of its
    previous values. Getting `status` returns a
    [`rich.group.Group`](https://rich.readthedocs.io/en/latest/group.html)
    """

    title: str
    status: InitVar[RenderableType]
    append: bool = False
    __rows: list[RenderableType] = field(init=False, default_factory=list)

    def __post_init__(self, status: RenderableType):
        self.__rows.append(status)

    @property
    def status(self) -> RenderableType:
        return Group(*self.__rows)

    @status.setter
    def status(self, value: RenderableType):
        highlighted = self.__highlight(value)
        if self.append:
            self.__rows.append(highlighted)
        else:
            self.__rows[-1] = highlighted

    @staticmethod
    def __highlight(s: RenderableType) -> RenderableType:
        if isinstance(s, (int, float, bool, str, list, tuple, set, frozenset)):
            text = Text(str(s))
            highlighter.highlight(text)
            return text
        return s


class ChrisomaticTask(abc.ABC, Generic[_R]):
    @abc.abstractmethod
    async def run(self, emit: State) -> tuple[Outcome, Optional[_R]]:
        ...

    @abc.abstractmethod
    def initial_state(self) -> State:
        ...
