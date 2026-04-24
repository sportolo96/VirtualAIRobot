from __future__ import annotations

from src.domain.entities.run import Run
from src.domain.repositories.run_repository import RunRepository
from src.domain.value_objects.run_id import RunId


class InMemoryRunRepository(RunRepository):
    """In-memory run repository for tests."""

    def __init__(self) -> None:
        self._items: dict[str, Run] = {}

    def save(self, run: Run) -> None:
        self._items[run.run_id.value] = run

    def get(self, run_id: RunId) -> Run | None:
        return self._items.get(run_id.value)
