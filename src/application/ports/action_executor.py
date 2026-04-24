from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ActionExecutor(ABC):
    """Action execution contract."""

    @abstractmethod
    def handle(self, action: dict[str, Any], start_url: str) -> dict[str, Any]:
        raise NotImplementedError
