from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunLimits:
    """Execution limits for a run."""

    max_steps: int
    time_budget_sec: int
    max_retries_per_step: int

    def __post_init__(self) -> None:
        if self.max_steps <= 0:
            raise ValueError("max_steps must be positive")
        if self.time_budget_sec <= 0:
            raise ValueError("time_budget_sec must be positive")
        if self.max_retries_per_step < 0:
            raise ValueError("max_retries_per_step cannot be negative")
