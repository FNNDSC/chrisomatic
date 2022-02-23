from typing import Optional
from dataclasses import dataclass
from chris.cube.deserialization import ComputeResource as CubeComputeResource
from chrisomatic.framework.task import ChrisomaticTask, State, Outcome
from chrisomatic.spec.common import ComputeResource as GivenComputeResource


@dataclass
class ComputeResourceTask(ChrisomaticTask[CubeComputeResource]):

    given: GivenComputeResource

    def initial_state(self) -> State:
        return State(
            title=self.given.name,
            status='checking for compute resource...'
        )

    def run(self, emit: State) -> tuple[Outcome, Optional[CubeComputeResource]]:
        ...

