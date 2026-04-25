from __future__ import annotations

from pathlib import Path

from flask import Flask

from src.application.handlers.cancel_run_handler import CancelRunHandler
from src.application.handlers.create_run_handler import CreateRunHandler
from src.application.handlers.get_run_status_handler import GetRunStatusHandler
from src.application.handlers.list_run_steps_handler import ListRunStepsHandler
from src.application.ports.queue_client import QueueClient
from src.infrastructure.config.settings import Settings
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
        self._create_run_handler = CreateRunHandler(
            run_repository=run_repository, queue_client=queue_client
        )
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


class ApiContainerMissingAIStub(ApiContainerStub):
    """Test dependency container with missing AI runtime."""

    def assert_ai_runtime_ready(self) -> None:
        raise RuntimeError("AI runtime is not configured. Set OPENAI_API_KEY to start runs.")


def _build_payload() -> dict:
    return {
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
        "allowed_actions": ["move", "click", "scroll", "type", "key", "wait", "done", "failed"],
        "llm": {
            "planner_model": "gpt-5.4",
            "evaluator_model": "gpt-5.4",
        },
    }


def _create_client() -> Flask:
    return create_app(container=ApiContainerStub())


def _build_settings(*, auth_enabled: bool, auth_key: str) -> Settings:
    return Settings(
        redis_url="redis://redis:6379/0",
        queue_name="runs",
        ai_provider="openai",
        ai_model="gpt-5.4",
        openai_api_key="test-key",
        api_auth_enabled=auth_enabled,
        api_auth_key=auth_key,
        webhook_enabled=False,
        webhook_timeout_sec=10,
        webhook_max_retries=3,
        webhook_retry_backoff_sec=1.0,
        webhook_signing_secret="",
        webhook_dead_letter_dir=Path("/tmp/artifacts/dead_letters"),
        artifact_root=Path("/tmp/artifacts"),
        planner_template_path=Path("/tmp/planner.txt"),
        evaluator_template_path=Path("/tmp/evaluator.txt"),
        flask_host="0.0.0.0",
        flask_port=8000,
    )


def test_runs_api_baseline_flow() -> None:
    app = _create_client()
    client = app.test_client()

    create_response = client.post("/v1/runs", json=_build_payload())
    assert create_response.status_code == 202
    assert create_response.headers.get("X-Request-Id")
    run_id = create_response.get_json()["run_id"]

    status_response = client.get(f"/v1/runs/{run_id}")
    assert status_response.status_code == 200
    assert status_response.get_json()["status"] == "queued"

    steps_response = client.get(f"/v1/runs/{run_id}/steps")
    assert steps_response.status_code == 200
    assert steps_response.get_json()["steps"] == []


def test_runs_api_returns_422_on_invalid_payload() -> None:
    app = _create_client()
    client = app.test_client()

    response = client.post("/v1/runs", json={"goal": "missing fields"})

    assert response.status_code == 422
    assert "errors" in response.get_json()


def test_runs_api_returns_404_for_missing_run_status() -> None:
    app = _create_client()
    client = app.test_client()

    response = client.get("/v1/runs/run_missing")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Run not found"


def test_runs_api_returns_404_for_missing_run_cancel() -> None:
    app = _create_client()
    client = app.test_client()

    response = client.post("/v1/runs/run_missing/cancel")

    assert response.status_code == 404
    assert response.get_json()["error"] == "Run not found"


def test_runs_api_cancel_flow() -> None:
    app = _create_client()
    client = app.test_client()

    create_response = client.post("/v1/runs", json=_build_payload())
    run_id = create_response.get_json()["run_id"]

    cancel_response = client.post(f"/v1/runs/{run_id}/cancel")

    assert cancel_response.status_code == 202
    assert cancel_response.get_json()["status"] == "cancel_requested"


def test_runs_api_returns_503_when_ai_runtime_is_not_ready() -> None:
    app = create_app(container=ApiContainerMissingAIStub())
    client = app.test_client()

    response = client.post("/v1/runs", json=_build_payload())

    assert response.status_code == 503
    assert response.get_json()["error"] == (
        "AI runtime is not configured. Set OPENAI_API_KEY to start runs."
    )


def test_runs_api_requires_api_key_when_auth_enabled() -> None:
    app = create_app(
        container=ApiContainerStub(),
        settings=_build_settings(auth_enabled=True, auth_key="shared-secret"),
    )
    client = app.test_client()

    missing_key_response = client.post("/v1/runs", json=_build_payload())
    assert missing_key_response.status_code == 401
    assert missing_key_response.get_json() == {"error": "Unauthorized"}

    success_response = client.post(
        "/v1/runs",
        json=_build_payload(),
        headers={"X-API-Key": "shared-secret"},
    )
    assert success_response.status_code == 202
