from typing import Optional, Collection
from dataclasses import dataclass

from aiochris import ChrisAdminClient
from aiochris.models.public import ComputeResource
from rich.console import RenderableType

from chrisomatic.framework.task import ChrisomaticTask, Channel, Outcome
from chrisomatic.spec.common import ComputeResource as GivenComputeResource


@dataclass
class ComputeResourceTask(ChrisomaticTask[ComputeResource]):
    """
    Check if a compute resource already exists. If not, create it and return it.
    """

    cube: ChrisAdminClient
    given: GivenComputeResource
    existing: Collection[ComputeResource]

    def first_status(self) -> tuple[str, RenderableType]:
        return self.given.name, "checking for compute resource..."

    async def run(self, status: Channel) -> tuple[Outcome, Optional[ComputeResource]]:
        preexisting = self.find_in_existing()
        if preexisting is not None:
            status.replace(preexisting.url)
            if self.same_as(preexisting):
                return Outcome.NO_CHANGE, preexisting
            status.replace(
                f'Existing "{preexisting.name}" ' "is different from given_config."
            )
            return Outcome.FAILED, preexisting
        missing = self.given.get_missing()
        if missing:
            status.replace(f"Missing configurations: {missing}")
            return Outcome.FAILED, None
        created_compute_resource = await self.cube.create_compute_resource(
            name=self.given.name,
            compute_url=self.given.url,
            compute_user=self.given.username,
            compute_password=self.given.password,
            description=self.given.description,
            compute_innetwork=self.given.innetwork,
        )
        status.replace(created_compute_resource.url)
        return Outcome.CHANGE, created_compute_resource

    def find_in_existing(self) -> Optional[ComputeResource]:
        """
        Get the existing compute environment with the same name as the given configuration.
        """
        for existing in self.existing:
            if existing.name == self.given.name:
                return existing
        return None

    def same_as(self, preexisting: ComputeResource) -> bool:
        """
        Returns `True` if the given configuration describes a specified pre-existing
        compute environment.
        """
        if self.given.name != preexisting.name:
            return False
        if self.given.url is not None and self.given.url != preexisting.compute_url:
            return False
        if (
            self.given.description is not None
            and self.given.description != preexisting.description
        ):
            return False
        return True
