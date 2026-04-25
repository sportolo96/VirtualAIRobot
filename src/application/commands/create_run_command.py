from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CreateRunCommand:
    """Create run command payload."""

    goal: str
    start_url: str
    success_criteria: dict[str, Any]
    runtime: dict[str, Any]
    limits: dict[str, int]
    allowed_actions: list[str]
    llm: dict[str, Any]
    callbacks: dict[str, Any] = field(default_factory=dict)
