"""Serializable contracts for the Plant-CellFM annotation agent.

The agent deliberately uses small dataclasses instead of a framework-specific
state object.  This keeps runs reproducible on a single GPU and makes every
decision easy to inspect in JSON/JSONL artifacts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AgentConfig:
    """Runtime policy; these values do not alter the frozen checkpoint."""

    review_threshold: float = 0.70
    accepted_coverage_target: float = 0.80
    fewshot_min_support: int = 8
    marker_top_n: int = 10
    marker_min_cells: int = 20
    batch_size: int = 128
    max_retries: int = 1

    def __post_init__(self) -> None:
        if not 0.0 < self.review_threshold <= 1.0:
            raise ValueError("review_threshold must be in (0, 1]")
        if not 0.0 <= self.accepted_coverage_target <= 1.0:
            raise ValueError("accepted_coverage_target must be in [0, 1]")
        if self.fewshot_min_support < 2:
            raise ValueError("fewshot_min_support must be at least 2")
        if self.marker_top_n < 1 or self.marker_min_cells < 2:
            raise ValueError("marker settings must be positive")


@dataclass
class AgentEvent:
    stage: str
    action: str
    status: str
    evidence: dict[str, Any] = field(default_factory=dict)
    timestamp_utc: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentRunResult:
    run_id: str
    status: str
    route: str
    output_dir: str
    input_audit: dict[str, Any]
    route_decision: dict[str, Any]
    quality: dict[str, Any]
    artifacts: dict[str, str]
    events: list[AgentEvent]
    created_at_utc: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["events"] = [event.to_dict() for event in self.events]
        return payload
