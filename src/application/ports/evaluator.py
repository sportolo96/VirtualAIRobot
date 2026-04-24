from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Evaluator(ABC):
    """Evaluator contract."""

    @abstractmethod
    def handle(
        self,
        goal: str,
        success_criteria: dict[str, Any],
        step_index: int,
        action: dict[str, Any],
        action_result: dict[str, Any],
        post_screenshot: str,
    ) -> dict[str, Any]:
        raise NotImplementedError
