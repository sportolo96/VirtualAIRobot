from __future__ import annotations

from src.domain.entities.step import Step
from src.domain.repositories.step_repository import StepRepository
from src.domain.value_objects.run_id import RunId


class InMemoryStepRepository(StepRepository):
    """In-memory step repository for tests."""

    def __init__(self) -> None:
        self._items: dict[str, list[Step]] = {}

    def add(self, step: Step) -> None:
        self._items.setdefault(step.run_id.value, []).append(step)

    def list_by_run_id(self, run_id: RunId) -> list[Step]:
        return list(self._items.get(run_id.value, []))
