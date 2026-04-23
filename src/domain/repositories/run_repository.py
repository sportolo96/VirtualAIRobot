from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.run import Run
from src.domain.value_objects.run_id import RunId


class RunRepository(ABC):
    """Repository contract for runs."""

    @abstractmethod
    def save(self, run: Run) -> None:
        raise NotImplementedError

    @abstractmethod
    def get(self, run_id: RunId) -> Run | None:
        raise NotImplementedError
