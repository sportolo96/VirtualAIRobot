from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.domain.value_objects.run_id import RunId


@dataclass
class Step:
    """Step entity for run trace."""

    run_id: RunId
    index: int
    action: dict[str, Any]
    action_result: dict[str, Any]
    evaluation: dict[str, Any]
    pre_screenshot: str
    post_screenshot: str
    created_at: datetime
