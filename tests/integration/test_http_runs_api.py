from __future__ import annotations

from flask import Flask

from src.application.handlers.cancel_run_handler import CancelRunHandler
from src.application.handlers.create_run_handler import CreateRunHandler
from src.application.handlers.get_run_status_handler import GetRunStatusHandler
from src.application.handlers.list_run_steps_handler import ListRunStepsHandler
from src.application.ports.queue_client import QueueClient
from src.infrastructure.repositories.in_memory_run_repository import InMemoryRunRepository
from src.infrastructure.repositories.in_memory_step_repository import InMemoryStepRepository
from src.interfaces.http.app_factory import create_app


class QueueSpy(QueueClient):
    """Queue spy for API integration tests."""

    def __init__(self) -> None:
        self.enqueued: list[str] = []

    def enqueue_process_run(self, run_id: str) -> None:
        self.enqueued.append(run_id)


class ApiContainerStub:
    """Test dependency container."""

    def __init__(self) -> None:
        run_repository = InMemoryRunRepository()
        step_repository = InMemoryStepRepository()
        queue_client = QueueSpy()
        self._create_run_handler = CreateRunHandler(run_repository=run_repository, queue_client=queue_client)
        self._get_run_status_handler = GetRunStatusHandler(run_repository=run_repository)
        self._list_run_steps_handler = ListRunStepsHandler(step_repository=step_repository)
        self._cancel_run_handler = CancelRunHandler(run_repository=run_repository)

    def create_create_run_handler(self) -> CreateRunHandler:
        return self._create_run_handler

    def create_get_run_status_handler(self) -> GetRunStatusHandler:
        return self._get_run_status_handler

    def create_list_run_steps_handler(self) -> ListRunStepsHandler:
        return self._list_run_steps_handler

    def create_cancel_run_handler(self) -> CancelRunHandler:
        return self._cancel_run_handler


def test_runs_api_baseline_flow() -> None:
    app: Flask = create_app(container=ApiContainerStub())
    client = app.test_client()

    payload = {
        "goal": "Open profile page",
        "start_url": "https://example.com/login",
        "success_criteria": {
            "type": "text_or_dom",
            "must_include": ["Profile"],
            "must_not_include": ["Error"],
        },
        "runtime": {
            "mode": "container_desktop",
            "viewport": {"width": 1080, "height": 1920},
        },
        "limits": {
            "max_steps": 5,
            "time_budget_sec": 60,
            "max_retries_per_step": 1,
        },
        "allowed_actions": ["move", "click", "scroll", "type", "key", "wait"],
        "llm": {
            "planner_model": "deterministic",
            "evaluator_model": "deterministic",
        },
    }

    create_response = client.post("/v1/runs", json=payload)
    assert create_response.status_code == 202
    run_id = create_response.get_json()["run_id"]

    status_response = client.get(f"/v1/runs/{run_id}")
    assert status_response.status_code == 200
    assert status_response.get_json()["status"] == "queued"

    steps_response = client.get(f"/v1/runs/{run_id}/steps")
    assert steps_response.status_code == 200
    assert steps_response.get_json()["steps"] == []
