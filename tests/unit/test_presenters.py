from __future__ import annotations

from datetime import datetime, timezone

from src.application.presenters.run_presenter import RunPresenter
from src.application.presenters.step_presenter import StepPresenter
from src.domain.entities.step import Step


def test_run_presenter_formats_response(run_factory) -> None:
    run = run_factory()
    run.current_step = 2
    run.last_action = "click"
    run.last_evaluation = "progress"
    run.final_evaluation = {"reason": "done"}
    run.error = None

    presenter = RunPresenter()
    result = presenter.handle(run=run, now=datetime.now(tz=timezone.utc))

    assert result["run_id"] == run.run_id.value
    assert result["status"] == run.status.value
    assert result["progress"]["current_step"] == 2
    assert result["summary"]["last_action"] == "click"


def test_step_presenter_formats_single_and_many(run_factory) -> None:
    run = run_factory()
    created_at = datetime.now(tz=timezone.utc)
    step = Step(
        run_id=run.run_id,
        index=1,
        action={"action": "wait"},
        action_result={"success": True},
        evaluation={"progress": "ok", "goal_achieved": False, "risk": "low", "reason": "test"},
        pre_screenshot="/tmp/pre.png",
        post_screenshot="/tmp/post.png",
        created_at=created_at,
    )

    presenter = StepPresenter()
    one = presenter.handle(step=step)
    many = presenter.handle_many(steps=[step])

    assert one["index"] == 1
    assert one["created_at"] == created_at.isoformat()
    assert len(many) == 1
    assert many[0]["action"]["action"] == "wait"
