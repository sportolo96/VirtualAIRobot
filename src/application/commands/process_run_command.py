from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProcessRunCommand:
    """Process run command."""

    run_id: str
