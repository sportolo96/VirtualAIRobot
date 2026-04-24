from __future__ import annotations

from src.application.queries.get_run_status_query import GetRunStatusQuery
from src.domain.entities.run import Run
from src.domain.repositories.run_repository import RunRepository
from src.domain.value_objects.run_id import RunId


class GetRunStatusHandler:
    """Handle run status lookup."""

    def __init__(self, run_repository: RunRepository) -> None:
        self._run_repository = run_repository

    def handle(self, query: GetRunStatusQuery) -> Run | None:
        return self._run_repository.get(run_id=RunId(value=query.run_id))
