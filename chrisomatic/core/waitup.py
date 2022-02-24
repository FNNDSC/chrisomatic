import asyncio
import aiohttp
import time
import enum
from dataclasses import dataclass
from rich.text import Text
from rich.spinner import Spinner
from typing import Sequence
from chrisomatic.framework.task import ChrisomaticTask, State, Outcome
from chrisomatic.framework.taskrunner import TableTaskRunner, TableDisplayConfig


class _WaitResult(str, enum.Enum):
    OK = 'OK'
    DOWN = 'DOWN'
    ERROR = 'ERROR'

    def to_outcome(self) -> Outcome:
        if self == _WaitResult.OK:
            return Outcome.NO_CHANGE
        return Outcome.FAILED


_waiting_text = Text('waiting until server is online...', style='dim')


@dataclass(frozen=True)
class WaitUp(ChrisomaticTask[float]):
    url: str
    good_status: int
    interval: float
    timeout: float

    def initial_state(self) -> State:
        return State(title=self.url, status=Text('checking if server is online...', style='dim'))

    async def run(self, emit: State) -> tuple[Outcome, float]:
        start_time = time.monotonic()
        async with aiohttp.ClientSession() as session:
            while (time.monotonic() - start_time) <= self.timeout:
                emit.status = _waiting_text
                try:
                    res = await session.get(self.url)
                    elapsed_time = time.monotonic() - start_time
                    if res.status == self.good_status:
                        emit.status = f'server is ready after {elapsed_time}s'
                        return Outcome.NO_CHANGE, elapsed_time
                    emit.status = f'bad status={res.status} (expected {self.good_status})'
                    return Outcome.FAILED, elapsed_time
                except aiohttp.ClientConnectorError:
                    await asyncio.sleep(self.interval)
        elapsed_time = time.monotonic() - start_time
        emit.status = f'timed out after {elapsed_time}s'
        return Outcome.FAILED, elapsed_time


async def wait_up(urls: Sequence[str], good_status: int = 200, interval: float = 2.0, timeout: float = 300.0,
            ) -> tuple[bool, Sequence[float]]:
    runner = TableTaskRunner(
        config=TableDisplayConfig(spinner=Spinner('aesthetic'), spinner_width=12, polling_interval=interval / 4),
        tasks=[WaitUp(url, good_status, interval, timeout) for url in urls]
    )
    results = await runner.apply()
    all_good = all(outcome != Outcome.FAILED for outcome, _ in results)
    elapseds = [elapsed for _, elapsed in results]
    return all_good, elapseds
