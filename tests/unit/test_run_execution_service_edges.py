from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from src.application.ports.action_executor import ActionExecutor
from src.application.ports.capture_adapter import CaptureAdapter
from src.application.ports.evaluator import Evaluator
from src.application.ports.planner import Planner
from src.application.ports.safety_guard import SafetyGuard
from src.domain.services.run_execution_service import RunExecutionService
from src.infrastructure.repositories.in_memory_run_repository import InMemoryRunRepository
from src.infrastructure.repositories.in_memory_step_repository import InMemoryStepRepository


class PlannerSequence(Planner):
    """Planner returning an action sequence."""

    def __init__(self, actions: list[str]) -> None:
        self._actions = actions

    def handle(
        self,
        goal: str,
        start_url: str,
        allowed_actions: list[str],
        step_index: int,
        pre_screenshot: str,
        last_evaluation: str | None,
    ) -> dict[str, Any]:
        index = min(step_index - 1, len(self._actions) - 1)
        return {"action": self._actions[index], "target": None, "value": None, "reason": "stub"}


class EvaluatorNeutral(Evaluator):
    """Evaluator returning neutral progress."""

    def handle(
        self,
        goal: str,
        success_criteria: dict[str, Any],
        step_index: int,
        action: dict[str, Any],
        action_result: dict[str, Any],
        post_screenshot: str,
    ) -> dict[str, Any]:
        return {
            "progress": "ongoing",
            "goal_achieved": False,
            "risk": "low",
            "reason": "neutral",
        }


class CaptureNeutral(CaptureAdapter):
    """Capture adapter stub."""

    def handle(self, run_id: str, step_index: int, phase: str) -> str:
        return f"/tmp/{run_id}_{step_index}_{phase}.png"


class ActionExecutorAlwaysFail(ActionExecutor):
    """Action executor that always fails."""

    def __init__(self) -> None:
        self.calls = 0

    def handle(self, action: dict[str, Any], start_url: str) -> dict[str, Any]:
        self.calls += 1
        raise RuntimeError("exec failed")


class ActionExecutorAlwaysSuccess(ActionExecutor):
    """Action executor that always succeeds."""

    def handle(self, action: dict[str, Any], start_url: str) -> dict[str, Any]:
        return {"success": True, "action": action["action"], "url": start_url}


class SafetyGuardRejectAll(SafetyGuard):
    """Safety guard rejecting all non-terminal actions."""

    def handle(self, allowed_actions: list[str], requested_action: str) -> None:
        raise ValueError("forbidden")


class SafetyGuardAllowAll(SafetyGuard):
    """Safety guard allowing all actions."""

    def handle(self, allowed_actions: list[str], requested_action: str) -> None:
        _ = (allowed_actions, requested_action)


def test_run_execution_service_marks_cancelled_when_requested(run_factory) -> None:
    run_repository = InMemoryRunRepository()
    step_repository = InMemoryStepRepository()
    run = run_factory()
    run.cancel_requested = True
    run_repository.save(run=run)

    service = RunExecutionService(
        run_repository=run_repository,
        step_repository=step_repository,
        planner=PlannerSequence(actions=["wait"]),
        evaluator=EvaluatorNeutral(),
        capture_adapter=CaptureNeutral(),
        action_executor=ActionExecutorAlwaysSuccess(),
        safety_guard=SafetyGuardAllowAll(),
    )

    service.handle(run_id=run.run_id.value)

    processed = run_repository.get(run_id=run.run_id)
    assert processed is not None
    assert processed.status.value == "cancelled"


def test_run_execution_service_marks_timeout_before_step(run_factory) -> None:
    run_repository = InMemoryRunRepository()
    step_repository = InMemoryStepRepository()
    run = run_factory()
    run.started_at = datetime.now(tz=timezone.utc) - timedelta(seconds=120)
    run_repository.save(run=run)

    service = RunExecutionService(
        run_repository=run_repository,
        step_repository=step_repository,
        planner=PlannerSequence(actions=["wait"]),
        evaluator=EvaluatorNeutral(),
        capture_adapter=CaptureNeutral(),
        action_executor=ActionExecutorAlwaysSuccess(),
        safety_guard=SafetyGuardAllowAll(),
    )

    service.handle(run_id=run.run_id.value)

    processed = run_repository.get(run_id=run.run_id)
    assert processed is not None
    assert processed.status.value == "timeout"


def test_run_execution_service_marks_failed_on_safety_rejection(run_factory) -> None:
    run_repository = InMemoryRunRepository()
    step_repository = InMemoryStepRepository()
    run = run_factory()
    run_repository.save(run=run)

    service = RunExecutionService(
        run_repository=run_repository,
        step_repository=step_repository,
        planner=PlannerSequence(actions=["click"]),
        evaluator=EvaluatorNeutral(),
        capture_adapter=CaptureNeutral(),
        action_executor=ActionExecutorAlwaysSuccess(),
        safety_guard=SafetyGuardRejectAll(),
    )

    service.handle(run_id=run.run_id.value)

    processed = run_repository.get(run_id=run.run_id)
    assert processed is not None
    assert processed.status.value == "failed"
    assert processed.error == "forbidden"


def test_run_execution_service_marks_failed_after_retries(run_factory) -> None:
    run_repository = InMemoryRunRepository()
    step_repository = InMemoryStepRepository()
    run = run_factory()
    run.limits = run.limits.__class__(max_steps=5, time_budget_sec=60, max_retries_per_step=2)
    run_repository.save(run=run)
    executor = ActionExecutorAlwaysFail()

    service = RunExecutionService(
        run_repository=run_repository,
        step_repository=step_repository,
        planner=PlannerSequence(actions=["click"]),
        evaluator=EvaluatorNeutral(),
        capture_adapter=CaptureNeutral(),
        action_executor=executor,
        safety_guard=SafetyGuardAllowAll(),
    )

    service.handle(run_id=run.run_id.value)

    processed = run_repository.get(run_id=run.run_id)
    assert processed is not None
    assert processed.status.value == "failed"
    assert processed.error == "exec failed"
    assert executor.calls == 3


def test_run_execution_service_marks_failed_on_max_steps(run_factory) -> None:
    run_repository = InMemoryRunRepository()
    step_repository = InMemoryStepRepository()
    run = run_factory()
    run.limits = run.limits.__class__(max_steps=2, time_budget_sec=120, max_retries_per_step=0)
    run_repository.save(run=run)

    service = RunExecutionService(
        run_repository=run_repository,
        step_repository=step_repository,
        planner=PlannerSequence(actions=["wait", "wait"]),
        evaluator=EvaluatorNeutral(),
        capture_adapter=CaptureNeutral(),
        action_executor=ActionExecutorAlwaysSuccess(),
        safety_guard=SafetyGuardAllowAll(),
    )

    service.handle(run_id=run.run_id.value)

    processed = run_repository.get(run_id=run.run_id)
    assert processed is not None
    assert processed.status.value == "failed"
    assert processed.error == "Maximum steps reached"
    assert len(step_repository.list_by_run_id(run_id=run.run_id)) == 2
