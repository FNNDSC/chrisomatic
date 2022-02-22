"""
Everything to do with the rich display and parallel execution of tasks.
"""

import asyncio
from rich.console import RenderableType, ConsoleRenderable, StyleType
from rich.text import Text
from rich.live import Live
from rich.table import Table, Column
from rich.panel import Panel
from rich.spinner import Spinner
from typing import Sequence, ClassVar
from dataclasses import dataclass, InitVar
from chrisomatic.task import State, ChrisomaticTask, Outcome


@dataclass
class _RunningTask:

    chrisomatic_task: InitVar[ChrisomaticTask]
    task: ClassVar[asyncio.Task]
    state: ClassVar[State]
    spinner: ClassVar[RenderableType] = Spinner('dots')

    def __post_init__(self, chrisomatic_task: ChrisomaticTask):
        self.state = chrisomatic_task.initial_state()
        self.task = asyncio.create_task(chrisomatic_task.run(self.state))

    def done(self) -> bool:
        return self.task.done()

    def to_row(self) -> tuple[RenderableType, RenderableType, RenderableType]:
        return self.__get_icon(), self.__get_title(), self.state.status

    def __get_icon(self) -> RenderableType:
        if self.done():
            return self.__outcome.emoji
        return self.spinner

    @property
    def __outcome(self) -> Outcome:
        return self.task.result()

    def __get_title(self) -> RenderableType:
        return Text(self.state.title,
                    style=self.__outcome.style if self.done() else None)


@dataclass(frozen=True)
class TableDisplayConfig:
    refresh_per_second: float = 15
    polling_interval: float = 0.25
    # task_title_width: int = 20
    # task_status_width: int = 50
    border_style: StyleType = 'bold yellow'


_DEFAULT_DISPLAY_CONFIG = TableDisplayConfig()


@dataclass
class TaskSet:
    """
    A `TaskSet` executes multiple `ChrisomaticTask` concurrently.
    """
    title: str
    tasks: Sequence[ChrisomaticTask]
    config: TableDisplayConfig = _DEFAULT_DISPLAY_CONFIG

    async def apply(self):
        """
        Execute all tasks in parallel while displaying a table that shows their live statuses.
        """
        running_tasks = tuple(_RunningTask(t) for t in self.tasks)
        with Live(self._render(running_tasks),
                  refresh_per_second=self.config.refresh_per_second) as live:
            while not self._all_done(running_tasks):
                await asyncio.sleep(self.config.polling_interval)
                live.update(self._render(running_tasks))

    def _render(self, tasks: Sequence[_RunningTask]) -> ConsoleRenderable:
        table = Table.grid(
            Column(width=3, justify='center'),
            Column(ratio=1, min_width=20, max_width=120),
            Column(ratio=2, min_width=40),
            expand=True
        )
        for running_task in tasks:
            table.add_row(*running_task.to_row())
        panel = Panel(
            table,
            title=self.title,
            title_align='left',
            border_style=self.config.border_style,
        )
        return panel

    @staticmethod
    def _all_done(tasks: Sequence[_RunningTask]) -> bool:
        return all(t.done() for t in tasks)
