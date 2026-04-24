from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.step import Step
from src.domain.value_objects.run_id import RunId


class StepRepository(ABC):
    """Repository contract for steps."""

    @abstractmethod
    def add(self, step: Step) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_by_run_id(self, run_id: RunId) -> list[Step]:
        raise NotImplementedError
