from __future__ import annotations

from datetime import datetime, timezone

from src.application.commands.cancel_run_command import CancelRunCommand
from src.application.commands.process_run_command import ProcessRunCommand
from src.application.handlers.cancel_run_handler import CancelRunHandler
from src.application.handlers.get_run_status_handler import GetRunStatusHandler
from src.application.handlers.list_run_steps_handler import ListRunStepsHandler
from src.application.handlers.process_run_handler import ProcessRunHandler
from src.application.queries.get_run_status_query import GetRunStatusQuery
from src.application.queries.list_run_steps_query import ListRunStepsQuery
from src.domain.entities.step import Step
from src.domain.services.run_execution_service import RunExecutionService
from src.infrastructure.repositories.in_memory_run_repository import InMemoryRunRepository
from src.infrastructure.repositories.in_memory_step_repository import InMemoryStepRepository


class ExecutionServiceSpy(RunExecutionService):
    """Execution service spy."""

    def __init__(self) -> None:
        self.called_with: list[str] = []

    def handle(self, run_id: str) -> None:
        self.called_with.append(run_id)


def test_get_run_status_handler_returns_none_when_missing() -> None:
    handler = GetRunStatusHandler(run_repository=InMemoryRunRepository())
    result = handler.handle(query=GetRunStatusQuery(run_id="run_missing"))
    assert result is None


def test_get_run_status_handler_returns_entity(run_factory) -> None:
    repository = InMemoryRunRepository()
    run = run_factory()
    repository.save(run=run)
    handler = GetRunStatusHandler(run_repository=repository)

    result = handler.handle(query=GetRunStatusQuery(run_id=run.run_id.value))

    assert result is not None
    assert result.run_id.value == run.run_id.value


def test_list_run_steps_handler_returns_steps(run_factory) -> None:
    step_repository = InMemoryStepRepository()
    run = run_factory()
    step_repository.add(
        Step(
            run_id=run.run_id,
            index=1,
            action={"action": "wait"},
            action_result={"success": True},
            evaluation={"progress": "ok", "goal_achieved": False, "risk": "low", "reason": "test"},
            pre_screenshot="/tmp/pre.png",
            post_screenshot="/tmp/post.png",
            created_at=datetime.now(tz=timezone.utc),
        )
    )
    handler = ListRunStepsHandler(step_repository=step_repository)

    steps = handler.handle(query=ListRunStepsQuery(run_id=run.run_id.value))

    assert len(steps) == 1
    assert steps[0].index == 1


def test_cancel_run_handler_marks_request(run_factory) -> None:
    repository = InMemoryRunRepository()
    run = run_factory()
    repository.save(run=run)
    handler = CancelRunHandler(run_repository=repository)

    result = handler.handle(command=CancelRunCommand(run_id=run.run_id.value))

    assert result is not None
    assert result.cancel_requested is True


def test_cancel_run_handler_returns_none_for_missing_run() -> None:
    handler = CancelRunHandler(run_repository=InMemoryRunRepository())
    result = handler.handle(command=CancelRunCommand(run_id="run_missing"))
    assert result is None


def test_process_run_handler_delegates_to_execution_service() -> None:
    spy = ExecutionServiceSpy()
    handler = ProcessRunHandler(run_execution_service=spy)

    handler.handle(command=ProcessRunCommand(run_id="run_123"))

    assert spy.called_with == ["run_123"]
