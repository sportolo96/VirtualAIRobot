from __future__ import annotations

from datetime import datetime
from typing import Any

from src.domain.entities.step import Step
from src.domain.value_objects.run_id import RunId


class StepTransformer:
    """Transform Step entity to and from storage record."""

    def to_record(self, step: Step) -> dict[str, Any]:
        return {
            "run_id": step.run_id.value,
            "index": step.index,
            "action": step.action,
            "action_result": step.action_result,
            "evaluation": step.evaluation,
            "pre_screenshot": step.pre_screenshot,
            "post_screenshot": step.post_screenshot,
            "created_at": step.created_at.isoformat(),
        }

    def from_record(self, record: dict[str, Any]) -> Step:
        return Step(
            run_id=RunId(value=str(record["run_id"])),
            index=int(record["index"]),
            action=dict(record["action"]),
            action_result=dict(record["action_result"]),
            evaluation=dict(record["evaluation"]),
            pre_screenshot=str(record["pre_screenshot"]),
            post_screenshot=str(record["post_screenshot"]),
            created_at=datetime.fromisoformat(str(record["created_at"])),
        )
