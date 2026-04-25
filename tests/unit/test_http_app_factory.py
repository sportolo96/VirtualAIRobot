from __future__ import annotations

from pathlib import Path

from flask import Flask

from src.infrastructure.config.settings import Settings
from src.interfaces.http.app_factory import create_app


class HandlerStub:
    """Generic handler stub."""

    def handle(self, **kwargs):
        _ = kwargs
        return None


class MinimalContainer:
    """Minimal container for app factory tests."""

    def create_create_run_handler(self):
        return HandlerStub()

    def create_get_run_status_handler(self):
        return HandlerStub()

    def create_list_run_steps_handler(self):
        return HandlerStub()

    def create_cancel_run_handler(self):
        return HandlerStub()


def _build_settings(*, api_auth_enabled: bool, api_auth_key: str) -> Settings:
    return Settings(
        redis_url="redis://redis:6379/0",
        queue_name="runs",
        ai_provider="openai",
        ai_model="gpt-5.4",
        openai_api_key="test-key",
        api_auth_enabled=api_auth_enabled,
        api_auth_key=api_auth_key,
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


def test_health_endpoint_is_available_with_container() -> None:
    app: Flask = create_app(
        container=MinimalContainer(),
        settings=_build_settings(api_auth_enabled=False, api_auth_key=""),
    )
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert response.headers.get("X-Request-Id")


def test_health_endpoint_ignores_auth_when_enabled() -> None:
    app: Flask = create_app(
        container=MinimalContainer(),
        settings=_build_settings(api_auth_enabled=True, api_auth_key="shared-secret"),
    )
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200


def test_non_health_endpoint_requires_api_key_when_auth_enabled() -> None:
    app: Flask = create_app(
        container=MinimalContainer(),
        settings=_build_settings(api_auth_enabled=True, api_auth_key="shared-secret"),
    )
    client = app.test_client()

    response = client.get("/v1/runs/run_missing")

    assert response.status_code == 401
    assert response.get_json() == {"error": "Unauthorized"}


def test_non_health_endpoint_returns_503_when_auth_key_missing() -> None:
    app: Flask = create_app(
        container=MinimalContainer(),
        settings=_build_settings(api_auth_enabled=True, api_auth_key=""),
    )
    client = app.test_client()

    response = client.get("/v1/runs/run_missing")

    assert response.status_code == 503
    assert response.get_json() == {
        "error": "API auth is enabled but API_AUTH_KEY is not configured."
    }
