from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ListRunStepsQuery:
    """List run steps query."""

    run_id: str
