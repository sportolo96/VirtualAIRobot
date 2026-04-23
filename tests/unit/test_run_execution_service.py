from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.application.ports.action_executor import ActionExecutor
from src.application.ports.capture_adapter import CaptureAdapter
from src.application.ports.evaluator import Evaluator
from src.application.ports.planner import Planner
from src.application.ports.safety_guard import SafetyGuard
from src.domain.entities.run import Run
from src.domain.services.run_execution_service import RunExecutionService
from src.domain.value_objects.run_limits import RunLimits
from src.infrastructure.repositories.in_memory_run_repository import InMemoryRunRepository
from src.infrastructure.repositories.in_memory_step_repository import InMemoryStepRepository


class PlannerStub(Planner):
    """Planner stub for tests."""

    def handle(
        self,
        goal: str,
        start_url: str,
        allowed_actions: list[str],
        step_index: int,
        pre_screenshot: str,
        last_evaluation: str | None,
    ) -> dict[str, Any]:
        return {"action": "wait", "target": None, "value": None, "reason": "stub"}


class EvaluatorStub(Evaluator):
    """Evaluator stub for tests."""

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
            "progress": f"step:{step_index}",
            "goal_achieved": step_index >= 2,
            "risk": "low",
            "reason": "stub",
        }


class CaptureStub(CaptureAdapter):
    """Capture stub for tests."""

    def handle(self, run_id: str, step_index: int, phase: str) -> str:
        return f"/tmp/{run_id}_step_{step_index}_{phase}.png"


class ActionExecutorStub(ActionExecutor):
    """Action executor stub for tests."""

    def handle(self, action: dict[str, Any], start_url: str) -> dict[str, Any]:
        return {"success": True, "action": action["action"], "url": start_url}


class SafetyGuardStub(SafetyGuard):
    """Safety guard stub for tests."""

    def handle(self, allowed_actions: list[str], requested_action: str) -> None:
        if requested_action not in allowed_actions:
            raise ValueError("Disallowed action")


def test_run_execution_service_marks_success_and_writes_steps() -> None:
    run_repository = InMemoryRunRepository()
    step_repository = InMemoryStepRepository()
    service = RunExecutionService(
        run_repository=run_repository,
        step_repository=step_repository,
        planner=PlannerStub(),
        evaluator=EvaluatorStub(),
        capture_adapter=CaptureStub(),
        action_executor=ActionExecutorStub(),
        safety_guard=SafetyGuardStub(),
    )

    run = Run.create(
        goal="Reach dashboard",
        start_url="https://example.com/login",
        success_criteria={"type": "text_or_dom", "must_include": ["Dashboard"], "must_not_include": []},
        runtime={"mode": "container_desktop", "viewport": {"width": 1080, "height": 1920}},
        limits=RunLimits(max_steps=5, time_budget_sec=60, max_retries_per_step=1),
        allowed_actions=["move", "click", "scroll", "type", "key", "wait"],
        llm={"planner_model": "deterministic", "evaluator_model": "deterministic"},
        now=datetime.now(tz=timezone.utc),
    )
    run_repository.save(run=run)

    service.handle(run_id=run.run_id.value)

    processed = run_repository.get(run.run_id)
    steps = step_repository.list_by_run_id(run.run_id)

    assert processed is not None
    assert processed.status.value == "succeeded"
    assert processed.goal_achieved is True
    assert len(steps) == 2
