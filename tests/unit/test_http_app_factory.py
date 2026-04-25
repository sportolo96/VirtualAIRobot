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


class WebhookEnforcerStub:
    """Webhook enforcer stub."""

    def __init__(self, result: str) -> None:
        self.result = result

    def enforce(self, headers, raw_body):  # noqa: ANN001
        _ = (headers, raw_body)
        return self.result


class WebhookContainerStub(MinimalContainer):
    """Container with webhook receiver enforcer."""

    def __init__(self, result: str) -> None:
        self._enforcer = WebhookEnforcerStub(result=result)

    def create_webhook_receiver_enforcer(self):
        return self._enforcer


def _build_settings(
    *,
    api_auth_enabled: bool,
    api_auth_key: str,
    api_auth_clients_json: str = "",
) -> Settings:
    return Settings(
        redis_url="redis://redis:6379/0",
        queue_name="runs",
        ai_provider="openai",
        ai_fallback_providers=(),
        ai_model="gpt-5.4",
        planner_model="gpt-5.4",
        evaluator_model="gpt-5.4",
        openai_api_key="test-key",
        azure_openai_api_key="",
        azure_openai_api_base_url="",
        azure_openai_api_version="2024-10-21",
        api_auth_enabled=api_auth_enabled,
        api_auth_key=api_auth_key,
        api_auth_clients_json=api_auth_clients_json,
        webhook_enabled=False,
        webhook_timeout_sec=10,
        webhook_max_retries=3,
        webhook_retry_backoff_sec=1.0,
        webhook_signing_secret="",
        webhook_dead_letter_dir=Path("/tmp/artifacts/dead_letters"),
        webhook_receiver_enabled=False,
        webhook_receiver_signing_secret="",
        webhook_receiver_require_signature=True,
        webhook_receiver_max_age_sec=300,
        webhook_receiver_idempotency_ttl_sec=86400,
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


def test_non_health_endpoint_returns_503_when_no_auth_keys_are_configured() -> None:
    app: Flask = create_app(
        container=MinimalContainer(),
        settings=_build_settings(api_auth_enabled=True, api_auth_key=""),
    )
    client = app.test_client()

    response = client.get("/v1/runs/run_missing")

    assert response.status_code == 503
    assert response.get_json() == {
        "error": "API auth is enabled but no keys are configured. Set API_AUTH_KEY or API_AUTH_CLIENTS_JSON."
    }


def test_non_health_endpoint_accepts_client_registry_key() -> None:
    app: Flask = create_app(
        container=MinimalContainer(),
        settings=_build_settings(
            api_auth_enabled=True,
            api_auth_key="",
            api_auth_clients_json=(
                '[{"client_id":"ops","roles":["runs.read"],'
                '"keys":[{"id":"k1","secret":"client-secret","status":"active"}]}]'
            ),
        ),
    )
    client = app.test_client()

    response = client.get(
        "/v1/runs/run_missing",
        headers={"X-API-Key": "client-secret", "X-Client-Id": "ops"},
    )

    assert response.status_code == 404


def test_non_health_endpoint_enforces_rbac_roles() -> None:
    app: Flask = create_app(
        container=MinimalContainer(),
        settings=_build_settings(
            api_auth_enabled=True,
            api_auth_key="",
            api_auth_clients_json=(
                '[{"client_id":"reader","roles":["runs.read"],'
                '"keys":[{"id":"k1","secret":"reader-secret","status":"active"}]}]'
            ),
        ),
    )
    client = app.test_client()

    response = client.post("/v1/runs", json={}, headers={"X-API-Key": "reader-secret"})

    assert response.status_code == 403
    assert response.get_json() == {"error": "Forbidden"}


def test_webhook_endpoint_accepts_request_without_api_key() -> None:
    app: Flask = create_app(
        container=WebhookContainerStub(result="accepted"),
        settings=_build_settings(api_auth_enabled=True, api_auth_key="shared-secret"),
    )
    client = app.test_client()

    response = client.post("/webhooks/run-completion", json={"event": "run.completed"})

    assert response.status_code == 202
    assert response.get_json() == {"status": "accepted"}


def test_webhook_endpoint_returns_duplicate_when_enforcer_reports_duplicate() -> None:
    app: Flask = create_app(
        container=WebhookContainerStub(result="duplicate"),
        settings=_build_settings(api_auth_enabled=True, api_auth_key="shared-secret"),
    )
    client = app.test_client()

    response = client.post("/webhooks/run-completion", json={"event": "run.completed"})

    assert response.status_code == 200
    assert response.get_json() == {"status": "duplicate"}
