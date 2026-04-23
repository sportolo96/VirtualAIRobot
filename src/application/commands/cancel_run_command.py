from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CancelRunCommand:
    """Cancel run command."""

    run_id: str
