from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.application.ports.action_executor import ActionExecutor
from src.application.ports.capture_adapter import CaptureAdapter
from src.application.ports.completion_notifier import CompletionNotifier
from src.application.ports.evaluator import Evaluator
from src.application.ports.planner import Planner
from src.application.ports.safety_guard import SafetyGuard
from src.domain.entities.run import Run
from src.domain.services.run_execution_service import RunExecutionService
from src.domain.value_objects.run_limits import RunLimits
from src.infrastructure.repositories.in_memory_run_repository import InMemoryRunRepository
from src.infrastructure.repositories.in_memory_step_repository import InMemoryStepRepository


class PlannerDone(Planner):
    """Planner returning terminal done."""

    def handle(
        self,
        goal: str,
        start_url: str,
        allowed_actions: list[str],
        step_index: int,
        pre_screenshot: str,
        last_evaluation: str | None,
        model: str | None = None,
    ) -> dict[str, Any]:
        _ = (goal, start_url, allowed_actions, step_index, pre_screenshot, last_evaluation, model)
        return {"action": "done", "target": None, "value": None, "reason": "done"}


class EvaluatorDone(Evaluator):
    """Evaluator returning goal achieved for done."""

    def handle(
        self,
        goal: str,
        success_criteria: dict[str, Any],
        step_index: int,
        action: dict[str, Any],
        action_result: dict[str, Any],
        post_screenshot: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        _ = (goal, success_criteria, step_index, action, action_result, post_screenshot, model)
        return {
            "progress": "done",
            "goal_achieved": True,
            "risk": "low",
            "reason": "done",
        }


class CaptureStub(CaptureAdapter):
    """Capture adapter stub."""

    def handle(self, run_id: str, step_index: int, phase: str) -> str:
        return f"/tmp/{run_id}_{step_index}_{phase}.png"


class ActionExecutorStub(ActionExecutor):
    """Action executor stub."""

    def handle(self, action: dict[str, Any], start_url: str, runtime: dict[str, Any]) -> dict[str, Any]:
        _ = (action, runtime)
        return {"success": True, "url": start_url}


class SafetyGuardAllow(SafetyGuard):
    """Safety guard allow stub."""

    def handle(self, allowed_actions: list[str], requested_action: str) -> None:
        _ = (allowed_actions, requested_action)


class CompletionNotifierSpy(CompletionNotifier):
    """Completion notifier spy."""

    def __init__(self) -> None:
        self.notified: list[tuple[str, str]] = []

    def handle(self, run: Run) -> None:
        self.notified.append((run.run_id.value, run.status.value))


def test_run_execution_service_notifies_completion_on_done() -> None:
    run_repository = InMemoryRunRepository()
    step_repository = InMemoryStepRepository()
    notifier = CompletionNotifierSpy()
    service = RunExecutionService(
        run_repository=run_repository,
        step_repository=step_repository,
        planner=PlannerDone(),
        evaluator=EvaluatorDone(),
        capture_adapter=CaptureStub(),
        action_executor=ActionExecutorStub(),
        safety_guard=SafetyGuardAllow(),
        completion_notifier=notifier,
    )

    run = Run.create(
        goal="Reach dashboard",
        start_url="https://example.com/login",
        success_criteria={
            "type": "text_or_dom",
            "must_include": ["Dashboard"],
            "must_not_include": [],
        },
        runtime={"mode": "container_desktop", "viewport": {"width": 1080, "height": 1920}},
        limits=RunLimits(max_steps=5, time_budget_sec=60, max_retries_per_step=1),
        allowed_actions=["move", "click", "scroll", "type", "key", "wait", "done", "failed"],
        now=datetime.now(tz=timezone.utc),
        callbacks={"completion_url": "https://example.test/webhook"},
    )
    run_repository.save(run=run)

    service.handle(run_id=run.run_id.value)

    assert notifier.notified == [(run.run_id.value, "succeeded")]
