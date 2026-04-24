from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.domain.value_objects.run_status import RunStatus


def test_run_create_defaults(run_factory) -> None:
    now = datetime.now(tz=timezone.utc)
    run = run_factory(now=now)

    assert run.status == RunStatus.QUEUED
    assert run.goal_achieved is False
    assert run.current_step == 0
    assert run.created_at == now
    assert run.updated_at == now


def test_run_mark_running_sets_started_once(run_factory) -> None:
    run = run_factory()
    first = datetime.now(tz=timezone.utc)
    second = first + timedelta(seconds=10)

    run.mark_running(now=first)
    run.mark_running(now=second)

    assert run.status == RunStatus.RUNNING
    assert run.started_at == first
    assert run.updated_at == second


def test_run_mark_succeeded_sets_final_evaluation(run_factory) -> None:
    run = run_factory()
    now = datetime.now(tz=timezone.utc)
    evaluation = {"reason": "ok", "terminal_action": "done"}

    run.mark_succeeded(now=now, final_evaluation=evaluation)

    assert run.status == RunStatus.SUCCEEDED
    assert run.goal_achieved is True
    assert run.final_evaluation == evaluation
    assert run.finished_at == now


def test_run_failure_and_cancel_transitions(run_factory) -> None:
    run = run_factory()
    failed_at = datetime.now(tz=timezone.utc)

    run.mark_failed(now=failed_at, reason="boom")
    assert run.status == RunStatus.FAILED
    assert run.error == "boom"

    timeout_run = run_factory()
    timeout_now = datetime.now(tz=timezone.utc)
    timeout_run.mark_timeout(now=timeout_now)
    assert timeout_run.status == RunStatus.TIMEOUT
    assert timeout_run.error == "Time budget exceeded"

    cancelled_run = run_factory()
    cancel_now = datetime.now(tz=timezone.utc)
    cancelled_run.mark_cancelled(now=cancel_now)
    assert cancelled_run.status == RunStatus.CANCELLED
    assert cancelled_run.error == "Run cancelled"


def test_run_update_progress_and_elapsed(run_factory) -> None:
    run = run_factory()
    started = datetime.now(tz=timezone.utc)
    ended = started + timedelta(seconds=7)

    run.mark_running(now=started)
    run.update_progress(now=ended, current_step=2, last_action="click", last_evaluation="progress")

    assert run.current_step == 2
    assert run.last_action == "click"
    assert run.last_evaluation == "progress"
    assert run.elapsed_sec(now=ended) == 7
