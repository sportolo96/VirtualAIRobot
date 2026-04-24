from __future__ import annotations

from datetime import datetime, timezone

from src.domain.entities.step import Step
from src.infrastructure.transformers.run_transformer import RunTransformer
from src.infrastructure.transformers.step_transformer import StepTransformer


def test_run_transformer_roundtrip(run_factory) -> None:
    run = run_factory()
    now = datetime.now(tz=timezone.utc)
    run.mark_running(now=now)
    run.update_progress(now=now, current_step=2, last_action="wait", last_evaluation="in progress")
    run.final_evaluation = {"terminal_action": "done", "reason": "ok"}

    transformer = RunTransformer()
    record = transformer.to_record(run=run)
    reconstructed = transformer.from_record(record=record)

    assert reconstructed.run_id.value == run.run_id.value
    assert reconstructed.status.value == run.status.value
    assert reconstructed.current_step == 2
    assert reconstructed.final_evaluation == {"terminal_action": "done", "reason": "ok"}


def test_step_transformer_roundtrip(run_factory) -> None:
    run = run_factory()
    created_at = datetime.now(tz=timezone.utc)
    step = Step(
        run_id=run.run_id,
        index=3,
        action={"action": "click", "target": "primary"},
        action_result={"success": True},
        evaluation={"progress": "ok", "goal_achieved": False, "risk": "low", "reason": "test"},
        pre_screenshot="/tmp/pre.png",
        post_screenshot="/tmp/post.png",
        created_at=created_at,
    )

    transformer = StepTransformer()
    record = transformer.to_record(step=step)
    reconstructed = transformer.from_record(record=record)

    assert reconstructed.index == 3
    assert reconstructed.action["action"] == "click"
    assert reconstructed.created_at == created_at
