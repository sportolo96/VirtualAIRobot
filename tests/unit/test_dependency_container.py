from __future__ import annotations

from pathlib import Path

from src.bootstrap import dependency_container as container_module
from src.infrastructure.config.settings import Settings


class QueueClientStub:
    """Queue client stub for container wiring tests."""

    def __init__(self, redis_client, queue_name: str, job_path: str) -> None:
        self.redis_client = redis_client
        self.queue_name = queue_name
        self.job_path = job_path

    def enqueue_process_run(self, run_id: str) -> None:
        _ = run_id


def test_dependency_container_builds_handlers(monkeypatch, tmp_path: Path) -> None:
    planner = tmp_path / "planner_prompt.txt"
    evaluator = tmp_path / "evaluator_prompt.txt"
    planner.write_text(
        "Goal: {goal}\nStart URL: {start_url}\nAllowed actions: {allowed_actions}\nStep index: {step_index}\nPre screenshot path: {pre_screenshot}\nLast evaluation: {last_evaluation}\n{format_instructions}",
        encoding="utf-8",
    )
    evaluator.write_text(
        "Goal: {goal}\nSuccess criteria: {success_criteria}\nStep index: {step_index}\nAction: {action}\nAction result: {action_result}\nPost screenshot path: {post_screenshot}\n{format_instructions}",
        encoding="utf-8",
    )

    monkeypatch.setattr(container_module.Redis, "from_url", lambda _url: object())
    monkeypatch.setattr(container_module, "RqQueueClient", QueueClientStub)

    settings = Settings(
        redis_url="redis://unused:6379/0",
        queue_name="runs",
        artifact_root=tmp_path / "artifacts",
        planner_template_path=planner,
        evaluator_template_path=evaluator,
        flask_host="0.0.0.0",
        flask_port=8000,
    )

    container = container_module.DependencyContainer(settings=settings)

    assert container.create_create_run_handler() is not None
    assert container.create_get_run_status_handler() is not None
    assert container.create_list_run_steps_handler() is not None
    assert container.create_cancel_run_handler() is not None
    assert container.create_process_run_handler() is not None
