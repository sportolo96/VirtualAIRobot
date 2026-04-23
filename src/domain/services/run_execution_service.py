from __future__ import annotations

from datetime import datetime, timezone

from src.application.ports.action_executor import ActionExecutor
from src.application.ports.capture_adapter import CaptureAdapter
from src.application.ports.evaluator import Evaluator
from src.application.ports.planner import Planner
from src.application.ports.safety_guard import SafetyGuard
from src.domain.entities.step import Step
from src.domain.repositories.run_repository import RunRepository
from src.domain.repositories.step_repository import StepRepository
from src.domain.value_objects.run_id import RunId
from src.domain.value_objects.run_status import RunStatus


class RunExecutionService:
    """Run execution loop service."""

    def __init__(
        self,
        run_repository: RunRepository,
        step_repository: StepRepository,
        planner: Planner,
        evaluator: Evaluator,
        capture_adapter: CaptureAdapter,
        action_executor: ActionExecutor,
        safety_guard: SafetyGuard,
    ) -> None:
        self._run_repository = run_repository
        self._step_repository = step_repository
        self._planner = planner
        self._evaluator = evaluator
        self._capture_adapter = capture_adapter
        self._action_executor = action_executor
        self._safety_guard = safety_guard

    def handle(self, run_id: str) -> None:
        identity = RunId(value=run_id)
        run = self._run_repository.get(run_id=identity)
        if run is None:
            return
        if run.status.is_terminal:
            return

        now = datetime.now(tz=timezone.utc)
        run.mark_running(now=now)
        self._run_repository.save(run=run)

        for step_index in range(run.current_step + 1, run.limits.max_steps + 1):
            run = self._run_repository.get(run_id=identity)
            if run is None:
                return
            if run.status.is_terminal:
                return

            now = datetime.now(tz=timezone.utc)
            if run.cancel_requested:
                run.mark_cancelled(now=now)
                self._run_repository.save(run=run)
                return

            if run.elapsed_sec(now=now) >= run.limits.time_budget_sec:
                run.mark_timeout(now=now)
                self._run_repository.save(run=run)
                return

            pre_screenshot = self._capture_adapter.handle(
                run_id=run.run_id.value,
                step_index=step_index,
                phase="pre",
            )

            planner_decision = self._planner.handle(
                goal=run.goal,
                start_url=run.start_url,
                allowed_actions=run.allowed_actions,
                step_index=step_index,
                pre_screenshot=pre_screenshot,
                last_evaluation=run.last_evaluation,
            )

            action_name = str(planner_decision.get("action", "wait"))
            try:
                self._safety_guard.handle(
                    allowed_actions=run.allowed_actions,
                    requested_action=action_name,
                )
            except Exception as exc:
                run.mark_failed(now=now, reason=str(exc))
                self._run_repository.save(run=run)
                return

            action_result: dict[str, object] = {
                "success": False,
                "error": "No execution attempt",
            }
            final_error: str | None = None

            for attempt in range(run.limits.max_retries_per_step + 1):
                try:
                    action_result = self._action_executor.handle(
                        action=planner_decision,
                        start_url=run.start_url,
                    )
                    action_result["attempt"] = attempt + 1
                    final_error = None
                    break
                except Exception as exc:
                    final_error = str(exc)
                    action_result = {
                        "success": False,
                        "error": final_error,
                        "attempt": attempt + 1,
                    }

            post_screenshot = self._capture_adapter.handle(
                run_id=run.run_id.value,
                step_index=step_index,
                phase="post",
            )

            evaluation = self._evaluator.handle(
                goal=run.goal,
                success_criteria=run.success_criteria,
                step_index=step_index,
                action=planner_decision,
                action_result=action_result,
                post_screenshot=post_screenshot,
            )

            step = Step(
                run_id=run.run_id,
                index=step_index,
                action=planner_decision,
                action_result=action_result,
                evaluation=evaluation,
                pre_screenshot=pre_screenshot,
                post_screenshot=post_screenshot,
                created_at=now,
            )
            self._step_repository.add(step=step)

            run.update_progress(
                now=now,
                current_step=step_index,
                last_action=action_name,
                last_evaluation=str(evaluation.get("progress", "")),
            )

            if final_error is not None and not bool(action_result.get("success", False)):
                run.mark_failed(now=now, reason=final_error)
                self._run_repository.save(run=run)
                return

            if bool(evaluation.get("goal_achieved", False)):
                run.mark_succeeded(now=now, final_evaluation=evaluation)
                self._run_repository.save(run=run)
                return

            self._run_repository.save(run=run)

        run = self._run_repository.get(run_id=identity)
        if run is not None and run.status == RunStatus.RUNNING:
            now = datetime.now(tz=timezone.utc)
            run.mark_failed(now=now, reason="Maximum steps reached")
            self._run_repository.save(run=run)
