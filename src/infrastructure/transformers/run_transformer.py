from __future__ import annotations

from datetime import datetime
from typing import Any

from src.domain.entities.run import Run
from src.domain.value_objects.run_id import RunId
from src.domain.value_objects.run_limits import RunLimits
from src.domain.value_objects.run_status import RunStatus


class RunTransformer:
    """Transform Run entity to and from storage record."""

    def to_record(self, run: Run) -> dict[str, Any]:
        return {
            "run_id": run.run_id.value,
            "goal": run.goal,
            "start_url": run.start_url,
            "success_criteria": run.success_criteria,
            "runtime": run.runtime,
            "limits": {
                "max_steps": run.limits.max_steps,
                "time_budget_sec": run.limits.time_budget_sec,
                "max_retries_per_step": run.limits.max_retries_per_step,
            },
            "allowed_actions": run.allowed_actions,
            "llm": run.llm,
            "status": run.status.value,
            "goal_achieved": run.goal_achieved,
            "created_at": run.created_at.isoformat(),
            "updated_at": run.updated_at.isoformat(),
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            "final_evaluation": run.final_evaluation,
            "cancel_requested": run.cancel_requested,
            "current_step": run.current_step,
            "last_action": run.last_action,
            "last_evaluation": run.last_evaluation,
            "error": run.error,
        }

    def from_record(self, record: dict[str, Any]) -> Run:
        return Run(
            run_id=RunId(value=str(record["run_id"])),
            goal=str(record["goal"]),
            start_url=str(record["start_url"]),
            success_criteria=dict(record["success_criteria"]),
            runtime=dict(record["runtime"]),
            limits=RunLimits(
                max_steps=int(record["limits"]["max_steps"]),
                time_budget_sec=int(record["limits"]["time_budget_sec"]),
                max_retries_per_step=int(record["limits"]["max_retries_per_step"]),
            ),
            allowed_actions=list(record["allowed_actions"]),
            llm=dict(record["llm"]),
            status=RunStatus(str(record["status"])),
            goal_achieved=bool(record["goal_achieved"]),
            created_at=datetime.fromisoformat(str(record["created_at"])),
            updated_at=datetime.fromisoformat(str(record["updated_at"])),
            started_at=datetime.fromisoformat(str(record["started_at"]))
            if record["started_at"]
            else None,
            finished_at=datetime.fromisoformat(str(record["finished_at"]))
            if record["finished_at"]
            else None,
            final_evaluation=dict(record["final_evaluation"])
            if record["final_evaluation"]
            else None,
            cancel_requested=bool(record["cancel_requested"]),
            current_step=int(record["current_step"]),
            last_action=str(record["last_action"]) if record["last_action"] is not None else None,
            last_evaluation=str(record["last_evaluation"])
            if record["last_evaluation"] is not None
            else None,
            error=str(record["error"]) if record["error"] is not None else None,
        )
