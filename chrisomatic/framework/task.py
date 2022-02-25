import abc
from typing import TypeVar, Generic, Optional
from dataclasses import dataclass
from chrisomatic.framework.outcome import Outcome
from rich.console import RenderableType

_R = TypeVar("_R")


@dataclass
class State:
    """
    Mutable object used to relay information between `ChrisomaticTask.run`
    and a live display.
    """

    title: str
    status: RenderableType


class ChrisomaticTask(abc.ABC, Generic[_R]):
    @abc.abstractmethod
    async def run(self, emit: State) -> tuple[Outcome, Optional[_R]]:
        ...

    @abc.abstractmethod
    def initial_state(self) -> State:
        ...
