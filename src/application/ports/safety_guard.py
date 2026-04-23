from __future__ import annotations

from abc import ABC, abstractmethod


class SafetyGuard(ABC):
    """Safety guard contract."""

    @abstractmethod
    def handle(self, allowed_actions: list[str], requested_action: str) -> None:
        raise NotImplementedError
