"""
Everything to do with the rich display and parallel execution of tasks.
"""
import abc
import asyncio
from dataclasses import dataclass, InitVar, field
from typing import Sequence, TypeVar, Generic, Awaitable, Optional

from rich.console import RenderableType, ConsoleRenderable, Console
from rich.live import Live
from rich.progress import Progress, TaskID
from rich.spinner import Spinner
from rich.table import Table, Column
from rich.text import Text

from chrisomatic.framework.task import Channel, ChrisomaticTask, Outcome

_R = TypeVar("_R")


@dataclass
class _RunningTableTask(Generic[_R]):

    chrisomatic_task: InitVar[ChrisomaticTask[_R]]
    spinner: RenderableType
    task: asyncio.Task = field(init=False)
    status: Channel = field(init=False)

    def __post_init__(self, chrisomatic_task: ChrisomaticTask):
        title, first_status = chrisomatic_task.first_status()
        self.status = Channel(title, first_status)
        self.task = asyncio.create_task(chrisomatic_task.run(self.status))

    def to_row(self) -> tuple[RenderableType, RenderableType, RenderableType]:
        return self.__get_icon(), self.__get_title(), self.status.render()

    def done(self) -> bool:
        return self.task.done()

    def result(self) -> tuple[Outcome, _R]:
        return self.task.result()

    @property
    def outcome(self) -> Outcome:
        return self.result()[0]

    def __get_icon(self) -> RenderableType:
        if self.done():
            return self.outcome.emoji
        return self.spinner

    def __get_title(self) -> RenderableType:
        return Text(
            self.status.title, style=self.outcome.style if self.done() else None
        )


@dataclass
class TaskRunner(Generic[_R], abc.ABC):
    """
    A `TaskRunner` executes multiple `ChrisomaticTask` concurrently.
    """

    tasks: Sequence[ChrisomaticTask[_R]]
    console: Optional[Console] = None

    @abc.abstractmethod
    async def apply(self) -> Sequence[tuple[Outcome, _R]]:
        """
        Execute all tasks in parallel.
        """
        ...


@dataclass(frozen=True)
class TableDisplayConfig:
    refresh_per_second: float = 15
    polling_interval: float = 0.25
    # task_title_width: int = 20
    # task_status_width: int = 50
    spinner: Spinner = Spinner("dots")
    spinner_width: int = 3


_DEFAULT_DISPLAY_CONFIG = TableDisplayConfig()


@dataclass
class TableTaskRunner(TaskRunner[_R]):
    """
    `TableTaskRunner` shows the live statuses from the states of all its running tasks.
    It is more suitable for task sets which have few tasks,
    and tasks that take a long time.
    """

    config: TableDisplayConfig = _DEFAULT_DISPLAY_CONFIG

    async def apply(self) -> Sequence[tuple[Outcome, _R]]:
        """
        Execute all tasks in parallel while displaying a table that shows their live statuses.
        """
        running_tasks = tuple(
            _RunningTableTask(t, spinner=self.config.spinner) for t in self.tasks
        )
        with Live(
            self._render(running_tasks),
            refresh_per_second=self.config.refresh_per_second,
            console=self.console,
        ) as live:
            while not self._all_done(running_tasks):
                await asyncio.sleep(self.config.polling_interval)
                live.update(self._render(running_tasks))
        return tuple(t.result() for t in running_tasks)

    def _render(self, tasks: Sequence[_RunningTableTask]) -> ConsoleRenderable:
        table = Table.grid(
            Column(width=self.config.spinner_width, justify="center"),
            Column(ratio=3, min_width=20, max_width=120),
            Column(ratio=8, min_width=40),
            expand=True,
        )
        for running_task in tasks:
            table.add_row(*running_task.to_row())
        # panel = Panel(
        #     table,
        #     title=self.title,
        #     title_align='left',
        #     border_style=self.given_config.border_style,
        # )
        # return panel
        return table

    @staticmethod
    def _all_done(tasks: Sequence[_RunningTableTask]) -> bool:
        return all(t.done() for t in tasks)


@dataclass
class ProgressTaskRunner(TaskRunner[_R]):
    """
    `ProgressTaskRunner` is a task runner which displays a progress bar that updates
    after the completion of a `ChrisomaticTask`.
    It is more suitable for a set of many quick tasks.
    """

    title: str = ""
    noisy: bool = True
    transient: bool = False

    async def apply(self) -> Sequence[tuple[Outcome, _R]]:
        with Progress(console=self.console, transient=self.transient) as progress:
            progress_task = progress.add_task(
                f"[yellow]{self.title}", total=len(self.tasks)
            )
            return await asyncio.gather(
                *(self.wrap_update(progress, progress_task, ct) for ct in self.tasks)
            )

    def wrap_update(
        self,
        progress: Progress,
        progress_task: TaskID,
        chrisomatic_task: ChrisomaticTask,
    ) -> Awaitable[tuple[Outcome, _R]]:
        """
        Wrap a `ChrisomaticTask` so that it updates a progress bar after it finishes.
        """

        async def run_and_update() -> tuple[Outcome, _R]:
            title, first_status = chrisomatic_task.first_status()
            status_channel = Channel(title, first_status)
            outcome, result = await chrisomatic_task.run(status_channel)
            progress.update(progress_task, advance=1)
            if self.noisy:
                msg = self.__format_noise(outcome, status_channel)
                progress.console.print(msg)
            return outcome, result

        return run_and_update()

    @staticmethod
    def __format_noise(outcome: Outcome, status: Channel) -> RenderableType:
        title = Text(f"[{status.title}] ", style=outcome.style)
        table = Table.grid(Column(ratio=3), Column(ratio=8), expand=True)
        table.add_row(title, status.render())
        return table
