"""
Models for interfacing asynchronous programs with pretty CLI output.

# The Big Picture

"Tasks" are subclasses of `ChrisomaticTask`. One task defines one atomic operation to do.
For example, a task could be for creating a user or adding a plugin.

Batches of tasks are executed by `TaskRunner`. An implementation of `TaskRunner` is responsible
for running tasks, usually concurrently, and displaying status information from their tasks
to the console.

Tasks transmit status information to `TaskRunner` via a `Channel`.

There are two implementations of `TaskRunner`:

- `TableTaskRunner` is suitable for a small number of concurrent tasks. The status of each task
  is shown in a table.
- `ProgressTaskRunner` is suitable for a large number of quick tasks. Status information from
  individual tasks is not shown. Instead, a progress bar is shown and updated whenever a task
  completes.
"""

from chrisomatic.framework.task import ChrisomaticTask, Channel
from chrisomatic.framework.runner import (
    TaskRunner,
    TableTaskRunner,
    ProgressTaskRunner,
    TableDisplayConfig,
)
from chrisomatic.framework.outcome import Outcome

__all__ = [
    "ChrisomaticTask",
    "Channel",
    "TaskRunner",
    "TableTaskRunner",
    "TableDisplayConfig",
    "ProgressTaskRunner",
    "Outcome",
]
