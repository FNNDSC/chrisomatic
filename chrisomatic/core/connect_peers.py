import dataclasses
from typing import Optional

import aiohttp
from aiochris import AnonChrisClient
from aiochris.types import ChrisURL
from aiochris.errors import BaseClientError
from rich.console import RenderableType

from chrisomatic.framework import ChrisomaticTask, Channel, Outcome


@dataclasses.dataclass(frozen=True)
class PeerConnectionTask(ChrisomaticTask[AnonChrisClient]):
    """Connect to a peer CUBE."""

    cube_url: ChrisURL
    connector: Optional[aiohttp.BaseConnector] = None
    connector_owner: bool = False

    def first_status(self) -> tuple[str, RenderableType]:
        return self.cube_url, "Checking peer status..."

    async def run(self, status: Channel) -> tuple[Outcome, Optional[AnonChrisClient]]:
        try:
            client = await AnonChrisClient.from_url(
                self.cube_url,
                connector=self.connector,
                connector_owner=self.connector_owner,
            )
            status.replace("Connected")
            return Outcome.NO_CHANGE, client
        except BaseClientError as e:
            status.replace(f"Error: {str(e)}")
            return Outcome.FAILED, None
