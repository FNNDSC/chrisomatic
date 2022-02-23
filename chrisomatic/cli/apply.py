import chrisomatic
from rich.console import Console
from rich.panel import Panel
from chrisomatic.spec.given import On, GivenConfig
from chrisomatic.core.create import SuperClientFactory
from chrisomatic.framework.outcome import Outcome
from chrisomatic.framework.taskset import TableTaskSet
from chrisomatic.core.superclient import SuperClient

console = Console()

Gstr_title = r"""
        __         _                            __  _     
  _____/ /_  _____(_)________  ____ ___  ____ _/ /_(_)____
 / ___/ __ \/ ___/ / ___/ __ \/ __ `__ \/ __ `/ __/ / ___/
/ /__/ / / / /  / (__  ) /_/ / / / / / / /_/ / /_/ / /__  
\___/_/ /_/_/  /_/____/\____/_/ /_/ /_/\__,_/\__/_/\___/  

"""
Gstr_title += (' ' * 30) + 'version ' + chrisomatic.__version__ + '\n'


async def apply(config: GivenConfig):
    _print_header()
    superuser_creation, superclient_cm = await _create_super_client(config.on)
    async with superclient_cm as superclient:
        print('lit')


def _print_header():
    console.print(Gstr_title)


async def _create_super_client(on: On) -> tuple[Outcome, SuperClient]:
    fact = SuperClientFactory(on=on)
    task_set = TableTaskSet(tasks=[fact])
    results = await task_set.apply()
    return results[0]
