from __future__ import annotations

from src.application.commands.create_run_command import CreateRunCommand
from src.application.handlers.create_run_handler import CreateRunHandler
from src.application.ports.queue_client import QueueClient
from src.infrastructure.repositories.in_memory_run_repository import InMemoryRunRepository


class QueueSpy(QueueClient):
    """Queue spy for assertions."""

    def __init__(self) -> None:
        self.enqueued: list[str] = []

    def enqueue_process_run(self, run_id: str) -> None:
        self.enqueued.append(run_id)


def test_create_run_handler_saves_and_enqueues() -> None:
    repository = InMemoryRunRepository()
    queue = QueueSpy()
    handler = CreateRunHandler(run_repository=repository, queue_client=queue)

    command = CreateRunCommand(
        goal="Open dashboard",
        start_url="https://example.com/login",
        success_criteria={
            "type": "text_or_dom",
            "must_include": ["Dashboard"],
            "must_not_include": ["Error"],
        },
        runtime={"mode": "container_desktop", "viewport": {"width": 1080, "height": 1920}},
        limits={"max_steps": 5, "time_budget_sec": 60, "max_retries_per_step": 1},
        allowed_actions=["move", "click", "scroll", "type", "key", "wait", "done", "failed"],
        llm={"planner_model": "chatgpt-5.4", "evaluator_model": "chatgpt-5.4"},
    )

    run = handler.handle(command=command)
    persisted = repository.get(run.run_id)

    assert persisted is not None
    assert persisted.status.value == "queued"
    assert queue.enqueued == [run.run_id.value]
