from dataclasses import dataclass
from serde import serialize

from chrisomatic.framework.outcome import Outcome


@serialize
@dataclass(frozen=True)
class FinalResult:
    summary: dict[Outcome, int]
