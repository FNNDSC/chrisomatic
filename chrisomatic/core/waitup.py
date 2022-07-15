import asyncio
import enum
import time
from dataclasses import dataclass

import aiohttp
from rich.text import Text

from chrisomatic.framework.task import ChrisomaticTask, State, Outcome


class _WaitResult(str, enum.Enum):
    OK = "OK"
    DOWN = "DOWN"
    ERROR = "ERROR"

    def to_outcome(self) -> Outcome:
        if self == _WaitResult.OK:
            return Outcome.NO_CHANGE
        return Outcome.FAILED


_waiting_text = Text("waiting until server is online...", style="dim")


@dataclass(frozen=True)
class WaitUp(ChrisomaticTask[float]):
    url: str
    good_status: int
    interval: float
    timeout: float

    def initial_state(self) -> State:
        return State(
            title=self.url, status=Text("checking if server is online...", style="dim")
        )

    async def run(self, emit: State) -> tuple[Outcome, float]:
        start_time = time.monotonic()
        async with aiohttp.ClientSession() as session:
            elapsed_time = 0.0
            while elapsed_time <= self.timeout:
                try:
                    res = await session.get(self.url)
                    elapsed_time = time.monotonic() - start_time
                    if res.status == self.good_status:
                        emit.status = f"server is ready after {elapsed_time:.1f}s"
                        return Outcome.NO_CHANGE, elapsed_time
                    emit.status = (
                        f"bad status={res.status} (expected {self.good_status})"
                    )
                    return Outcome.FAILED, elapsed_time
                except aiohttp.ClientConnectorError:
                    await asyncio.sleep(self.interval)
                    elapsed_time = time.monotonic() - start_time
                    emit.status = Text(
                        f"waiting until server is online... ({elapsed_time:.1f})",
                        style="dim",
                    )

        emit.status = f"timed out after {elapsed_time:.1f}s"
        return Outcome.FAILED, elapsed_time
