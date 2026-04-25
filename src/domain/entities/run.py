from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from src.domain.value_objects.run_id import RunId
from src.domain.value_objects.run_limits import RunLimits
from src.domain.value_objects.run_status import RunStatus


@dataclass
class Run:
    """Run aggregate root."""

    run_id: RunId
    goal: str
    start_url: str
    success_criteria: dict[str, Any]
    runtime: dict[str, Any]
    limits: RunLimits
    allowed_actions: list[str]
    callbacks: dict[str, Any]
    status: RunStatus
    goal_achieved: bool
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    final_evaluation: dict[str, Any] | None = None
    cancel_requested: bool = False
    current_step: int = 0
    last_action: str | None = None
    last_evaluation: str | None = None
    error: str | None = None

    @classmethod
    def create(
        cls,
        goal: str,
        start_url: str,
        success_criteria: dict[str, Any],
        runtime: dict[str, Any],
        limits: RunLimits,
        allowed_actions: list[str],
        now: datetime,
        callbacks: dict[str, Any] | None = None,
    ) -> Run:
        return cls(
            run_id=RunId.new(),
            goal=goal,
            start_url=start_url,
            success_criteria=success_criteria,
            runtime=runtime,
            limits=limits,
            allowed_actions=allowed_actions,
            callbacks=callbacks or {},
            status=RunStatus.QUEUED,
            goal_achieved=False,
            created_at=now,
            updated_at=now,
        )

    def mark_running(self, now: datetime) -> None:
        self.status = RunStatus.RUNNING
        if self.started_at is None:
            self.started_at = now
        self.updated_at = now

    def mark_succeeded(self, now: datetime, final_evaluation: dict[str, Any]) -> None:
        self.status = RunStatus.SUCCEEDED
        self.goal_achieved = True
        self.final_evaluation = final_evaluation
        self.finished_at = now
        self.updated_at = now

    def mark_failed(self, now: datetime, reason: str) -> None:
        self.status = RunStatus.FAILED
        self.error = reason
        self.finished_at = now
        self.updated_at = now

    def mark_timeout(self, now: datetime) -> None:
        self.status = RunStatus.TIMEOUT
        self.error = "Time budget exceeded"
        self.finished_at = now
        self.updated_at = now

    def mark_cancelled(self, now: datetime) -> None:
        self.status = RunStatus.CANCELLED
        self.error = "Run cancelled"
        self.finished_at = now
        self.updated_at = now

    def request_cancel(self, now: datetime) -> None:
        self.cancel_requested = True
        self.updated_at = now

    def update_progress(
        self, now: datetime, current_step: int, last_action: str, last_evaluation: str
    ) -> None:
        self.current_step = current_step
        self.last_action = last_action
        self.last_evaluation = last_evaluation
        self.updated_at = now

    def elapsed_sec(self, now: datetime) -> int:
        if self.started_at is None:
            return 0
        end_time = self.finished_at or now
        return max(0, int((end_time - self.started_at).total_seconds()))
