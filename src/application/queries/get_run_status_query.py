from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GetRunStatusQuery:
    """Get run status query."""

    run_id: str
