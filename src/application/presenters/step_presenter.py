from __future__ import annotations

from typing import Any

from src.domain.entities.step import Step


class StepPresenter:
    """Presenter for step responses."""

    def handle(self, step: Step) -> dict[str, Any]:
        return {
            "index": step.index,
            "action": step.action,
            "action_result": step.action_result,
            "evaluation": step.evaluation,
            "pre_screenshot": step.pre_screenshot,
            "post_screenshot": step.post_screenshot,
            "created_at": step.created_at.isoformat(),
        }

    def handle_many(self, steps: list[Step]) -> list[dict[str, Any]]:
        return [self.handle(step=step) for step in steps]
