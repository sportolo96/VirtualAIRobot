from __future__ import annotations

from datetime import datetime
from typing import Any

from src.domain.entities.run import Run


class RunPresenter:
    """Presenter for run responses."""

    def handle(self, run: Run, now: datetime) -> dict[str, Any]:
        return {
            "run_id": run.run_id.value,
            "status": run.status.value,
            "goal_achieved": run.goal_achieved,
            "progress": {
                "current_step": run.current_step,
                "max_steps": run.limits.max_steps,
                "elapsed_sec": run.elapsed_sec(now=now),
            },
            "summary": {
                "last_action": run.last_action,
                "last_evaluation": run.last_evaluation,
            },
            "final_evaluation": run.final_evaluation,
            "error": run.error,
        }
