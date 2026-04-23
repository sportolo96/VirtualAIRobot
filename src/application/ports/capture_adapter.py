from __future__ import annotations

from abc import ABC, abstractmethod


class CaptureAdapter(ABC):
    """Screenshot capture contract."""

    @abstractmethod
    def handle(self, run_id: str, step_index: int, phase: str) -> str:
        raise NotImplementedError
