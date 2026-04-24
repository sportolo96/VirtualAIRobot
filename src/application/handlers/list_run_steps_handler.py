from __future__ import annotations

from src.application.queries.list_run_steps_query import ListRunStepsQuery
from src.domain.entities.step import Step
from src.domain.repositories.step_repository import StepRepository
from src.domain.value_objects.run_id import RunId


class ListRunStepsHandler:
    """Handle step list lookup."""

    def __init__(self, step_repository: StepRepository) -> None:
        self._step_repository = step_repository

    def handle(self, query: ListRunStepsQuery) -> list[Step]:
        return self._step_repository.list_by_run_id(run_id=RunId(value=query.run_id))
