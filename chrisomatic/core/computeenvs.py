from typing import Optional, Collection
from dataclasses import dataclass

from chris.cube.models import ComputeResource as CubeComputeResource
from chrisomatic.framework.task import ChrisomaticTask, State, Outcome
from chrisomatic.spec.common import ComputeResource as GivenComputeResource
from chrisomatic.core.omniclient import OmniClient


@dataclass
class ComputeResourceTask(ChrisomaticTask[CubeComputeResource]):
    """
    Check if a compute resource already exists. If not, create it and return it.
    """

    omniclient: OmniClient
    given: GivenComputeResource
    existing: Collection[CubeComputeResource]

    def initial_state(self) -> State:
        return State(title=self.given.name, status="checking for compute resource...")

    async def run(self, emit: State) -> tuple[Outcome, Optional[CubeComputeResource]]:
        preexisting = self.find_in_existing()
        if preexisting is not None:
            emit.status = preexisting.url
            if self.same_as(preexisting):
                return Outcome.NO_CHANGE, preexisting
            emit.status = (
                f'Existing "{preexisting.name}" '
                "is different from given_config."
            )
            return Outcome.FAILED, preexisting
        if not self.given.is_some():
            emit.status = f'No configuration for "{self.given.name}"'
            return Outcome.FAILED, None
        created: CubeComputeResource = (
            await self.omniclient.cube.create_compute_resource(
                name=self.given.name,
                compute_url=self.given.url,
                compute_user=self.given.username,
                compute_password=self.given.password,
                description=self.given.description,
            )
        )
        emit.status = created.url
        return Outcome.CHANGE, created

    def find_in_existing(self) -> Optional[CubeComputeResource]:
        """
        Get the existing compute environment with the same name as the given configuration.
        """
        for existing in self.existing:
            if existing.name == self.given.name:
                return existing
        return None

    def same_as(self, preexisting: CubeComputeResource) -> bool:
        """
        Returns `True` if the given configuration describes a specified pre-existing
        compute environment.
        """
        if self.given.name != preexisting.name:
            return False
        if self.given.url is not None and self.given.url != preexisting.compute_url:
            return False
        if self.given.description is not None and self.given.description != preexisting.description:
            return False
        return True
