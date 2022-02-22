import abc
from dataclasses import dataclass
from chrisomatic.outcome import Outcome
from rich.console import RenderableType


@dataclass
class State:
    title: str
    status: RenderableType


class ChrisomaticTask(abc.ABC):
    @abc.abstractmethod
    async def run(self, emit: State) -> Outcome:
        ...

    @abc.abstractmethod
    def initial_state(self) -> State:
        ...
