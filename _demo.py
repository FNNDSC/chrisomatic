import asyncio
from typing import Sequence
from dataclasses import dataclass
from chrisomatic.task import Outcome, ChrisomaticTask, State
from chrisomatic.taskset import TaskSet


@dataclass
class DemoTask(ChrisomaticTask):
    name: str
    stuff: Sequence[float | str]
    result: Outcome

    async def run(self, emit: State) -> Outcome:
        for i in self.stuff:
            if isinstance(i, (int, float)):
                await asyncio.sleep(i)
            else:
                emit.status = i
        return self.result

    def initial_state(self) -> State:
        return State(self.name, 'resolving info...')


tasks = (
    DemoTask(name='pl-dircopy',
             stuff=(2.0, '--> http://localhost:8000/api/v1/plugins/1/'),
             result=Outcome.NO_CHANGE),
    DemoTask(name='pl-nums2mask',
             stuff=(
                 1.5, 'checking chrisstore.co...',
                 0.9, 'found in ChRIS store',
                 0.8, '--> http://localhost:8000/api/v1/plugins/2/'
             ),
             result=Outcome.CHANGE),
    DemoTask(name='pl-infantfs',
             result=Outcome.CHANGE,
             stuff=(
                 0.9, 'pulling image...',
                 3.0, 'uploading to http://localhost:8010/api/v1/ ...',
                 0.5, 'registering...',
                 0.5, '--> http://localhost:8000/api/v1/plugins/3/'
             )),
    DemoTask(name='pl-dne',
             result=Outcome.FAILED,
             stuff=(
                 0.5, 'pulling image...',
                 1.0, 'ghcr.io/fnndsc/pl-dne:1.0.0 : not found.'
             )),
    DemoTask(name='pl-verylongnamewhathappensifitistoolong?',
             result=Outcome.NO_CHANGE,
             stuff=(1.1, '--> http://localhost:8010/api/v1/5/'))
)


async def demo():
    ts = TaskSet(title='ChRIS Ultron Backend', tasks=tasks)
    await ts.apply()


def main():
    asyncio.run(demo())


if __name__ == '__main__':
    main()
