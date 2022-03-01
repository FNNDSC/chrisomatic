import asyncio
import abc
import random
from dataclasses import dataclass
from typing import TypeVar, Generic, Callable, Awaitable
from rich.text import Text
from chrisomatic.framework.task import State

R = TypeVar("R")


@dataclass(frozen=True)
class RetryWrapper(Generic[R], abc.ABC):
    """
    This helper class provides a mechanism for retrying a function call.
    """

    fn: Callable[[], Awaitable[R]]
    """
    Original function to be wrapped by this `RetryWrapper`.
    `fn` is a `Callable` which is prone to random failures that
    might not happen again when simply called again.
    """
    wait_min: float = 1.0
    wait_max: float = 2.0

    async def call(self, emit: State, max_attempt: int = 2, attempt: int = 0) -> R:
        try:
            return await self.fn()
        except BaseException as e:
            if attempt >= max_attempt:
                raise e
            if not self.check_exception(e):
                raise e
            t = Text()
            t.append(str(e), style="red")
            t.append(f" (attempt {attempt + 1}/{max_attempt})", style="dim")
            emit.status = t
            wait = random.random() * self.wait_max + self.wait_min
            await asyncio.sleep(wait)
            return await self.call(emit, attempt + 1)

    @abc.abstractmethod
    def check_exception(self, e: BaseException) -> bool:
        """
        Check the type and message of an exception and return whether it was expected.
        """
        ...
