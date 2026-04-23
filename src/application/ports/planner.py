from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Planner(ABC):
    """Planner contract."""

    @abstractmethod
    def handle(
        self,
        goal: str,
        start_url: str,
        allowed_actions: list[str],
        step_index: int,
        pre_screenshot: str,
        last_evaluation: str | None,
    ) -> dict[str, Any]:
        raise NotImplementedError
