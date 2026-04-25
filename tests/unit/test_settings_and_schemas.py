from __future__ import annotations

from pathlib import Path

from src.infrastructure.config.settings import load_settings
from src.interfaces.http.schemas import CreateRunRequestSchema


def test_load_settings_defaults(monkeypatch) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("QUEUE_NAME", raising=False)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_FALLBACK_PROVIDERS", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)
    monkeypatch.delenv("PLANNER_MODEL", raising=False)
    monkeypatch.delenv("EVALUATOR_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_BASE_URL", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_VERSION", raising=False)
    monkeypatch.delenv("API_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("API_AUTH_KEY", raising=False)
    monkeypatch.delenv("API_AUTH_CLIENTS_JSON", raising=False)
    monkeypatch.delenv("WEBHOOK_ENABLED", raising=False)
    monkeypatch.delenv("WEBHOOK_TIMEOUT_SEC", raising=False)
    monkeypatch.delenv("WEBHOOK_MAX_RETRIES", raising=False)
    monkeypatch.delenv("WEBHOOK_RETRY_BACKOFF_SEC", raising=False)
    monkeypatch.delenv("WEBHOOK_SIGNING_SECRET", raising=False)
    monkeypatch.delenv("WEBHOOK_DEAD_LETTER_DIR", raising=False)
    monkeypatch.delenv("WEBHOOK_RECEIVER_ENABLED", raising=False)
    monkeypatch.delenv("WEBHOOK_RECEIVER_SIGNING_SECRET", raising=False)
    monkeypatch.delenv("WEBHOOK_RECEIVER_REQUIRE_SIGNATURE", raising=False)
    monkeypatch.delenv("WEBHOOK_RECEIVER_MAX_AGE_SEC", raising=False)
    monkeypatch.delenv("WEBHOOK_RECEIVER_IDEMPOTENCY_TTL_SEC", raising=False)
    monkeypatch.delenv("ARTIFACT_ROOT", raising=False)
    monkeypatch.delenv("PLANNER_TEMPLATE_PATH", raising=False)
    monkeypatch.delenv("EVALUATOR_TEMPLATE_PATH", raising=False)
    monkeypatch.delenv("FLASK_HOST", raising=False)
    monkeypatch.delenv("FLASK_PORT", raising=False)

    settings = load_settings()

    assert settings.redis_url == "redis://redis:6379/0"
    assert settings.queue_name == "runs"
    assert settings.ai_provider == "openai"
    assert settings.ai_fallback_providers == ()
    assert settings.ai_model == "gpt-5.4"
    assert settings.planner_model == "gpt-5.4"
    assert settings.evaluator_model == "gpt-5.4"
    assert settings.openai_api_key == ""
    assert settings.azure_openai_api_key == ""
    assert settings.azure_openai_api_base_url == ""
    assert settings.azure_openai_api_version == "2024-10-21"
    assert settings.api_auth_enabled is False
    assert settings.api_auth_key == ""
    assert settings.api_auth_clients_json == ""
    assert settings.webhook_enabled is False
    assert settings.webhook_timeout_sec == 10
    assert settings.webhook_max_retries == 3
    assert settings.webhook_retry_backoff_sec == 1.0
    assert settings.webhook_signing_secret == ""
    assert settings.webhook_dead_letter_dir.name == "dead_letters"
    assert settings.webhook_receiver_enabled is False
    assert settings.webhook_receiver_signing_secret == ""
    assert settings.webhook_receiver_require_signature is True
    assert settings.webhook_receiver_max_age_sec == 300
    assert settings.webhook_receiver_idempotency_ttl_sec == 86400
    assert settings.flask_host == "0.0.0.0"
    assert settings.flask_port == 8000
    assert settings.planner_template_path.name == "planner_prompt.txt"
    assert settings.evaluator_template_path.name == "evaluator_prompt.txt"


def test_load_settings_from_environment(monkeypatch, tmp_path: Path) -> None:
    planner = tmp_path / "planner.txt"
    evaluator = tmp_path / "evaluator.txt"
    planner.write_text("planner", encoding="utf-8")
    evaluator.write_text("evaluator", encoding="utf-8")

    monkeypatch.setenv("REDIS_URL", "redis://localhost:6380/1")
    monkeypatch.setenv("QUEUE_NAME", "custom")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("AI_FALLBACK_PROVIDERS", "azure_openai")
    monkeypatch.setenv("AI_MODEL", "gpt-5.4")
    monkeypatch.setenv("PLANNER_MODEL", "gpt-5.4")
    monkeypatch.setenv("EVALUATOR_MODEL", "gpt-5.4")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "azure-key")
    monkeypatch.setenv("AZURE_OPENAI_API_BASE_URL", "https://example.openai.azure.com/openai/v1")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    monkeypatch.setenv("API_AUTH_ENABLED", "true")
    monkeypatch.setenv("API_AUTH_KEY", "shared-secret")
    monkeypatch.setenv(
        "API_AUTH_CLIENTS_JSON",
        '[{"client_id":"ci","roles":["runs.read"],"keys":[{"key":"k1","status":"active"}]}]',
    )
    monkeypatch.setenv("WEBHOOK_ENABLED", "true")
    monkeypatch.setenv("WEBHOOK_TIMEOUT_SEC", "12")
    monkeypatch.setenv("WEBHOOK_MAX_RETRIES", "5")
    monkeypatch.setenv("WEBHOOK_RETRY_BACKOFF_SEC", "2.5")
    monkeypatch.setenv("WEBHOOK_SIGNING_SECRET", "whsec_test")
    monkeypatch.setenv("WEBHOOK_DEAD_LETTER_DIR", str(tmp_path / "dead_letters"))
    monkeypatch.setenv("WEBHOOK_RECEIVER_ENABLED", "true")
    monkeypatch.setenv("WEBHOOK_RECEIVER_SIGNING_SECRET", "whrec_test")
    monkeypatch.setenv("WEBHOOK_RECEIVER_REQUIRE_SIGNATURE", "false")
    monkeypatch.setenv("WEBHOOK_RECEIVER_MAX_AGE_SEC", "120")
    monkeypatch.setenv("WEBHOOK_RECEIVER_IDEMPOTENCY_TTL_SEC", "7200")
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("PLANNER_TEMPLATE_PATH", str(planner))
    monkeypatch.setenv("EVALUATOR_TEMPLATE_PATH", str(evaluator))
    monkeypatch.setenv("FLASK_HOST", "127.0.0.1")
    monkeypatch.setenv("FLASK_PORT", "5001")

    settings = load_settings()

    assert settings.redis_url == "redis://localhost:6380/1"
    assert settings.queue_name == "custom"
    assert settings.ai_provider == "openai"
    assert settings.ai_fallback_providers == ("azure_openai",)
    assert settings.ai_model == "gpt-5.4"
    assert settings.planner_model == "gpt-5.4"
    assert settings.evaluator_model == "gpt-5.4"
    assert settings.openai_api_key == "test-key"
    assert settings.azure_openai_api_key == "azure-key"
    assert settings.azure_openai_api_base_url == "https://example.openai.azure.com/openai/v1"
    assert settings.azure_openai_api_version == "2024-10-21"
    assert settings.api_auth_enabled is True
    assert settings.api_auth_key == "shared-secret"
    assert settings.api_auth_clients_json.startswith("[")
    assert settings.webhook_enabled is True
    assert settings.webhook_timeout_sec == 12
    assert settings.webhook_max_retries == 5
    assert settings.webhook_retry_backoff_sec == 2.5
    assert settings.webhook_signing_secret == "whsec_test"
    assert settings.webhook_dead_letter_dir == tmp_path / "dead_letters"
    assert settings.webhook_receiver_enabled is True
    assert settings.webhook_receiver_signing_secret == "whrec_test"
    assert settings.webhook_receiver_require_signature is False
    assert settings.webhook_receiver_max_age_sec == 120
    assert settings.webhook_receiver_idempotency_ttl_sec == 7200
    assert settings.artifact_root == tmp_path / "artifacts"
    assert settings.planner_template_path == planner
    assert settings.evaluator_template_path == evaluator
    assert settings.flask_host == "127.0.0.1"
    assert settings.flask_port == 5001


def test_create_run_schema_defaults_and_terminal_actions() -> None:
    payload = {
        "goal": "Open profile",
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
    }

    schema = CreateRunRequestSchema.model_validate(payload)

    assert schema.callbacks.completion_url is None
    assert schema.callbacks.headers == {}
    assert "done" in schema.allowed_actions
    assert "failed" in schema.allowed_actions


def test_create_run_schema_uses_default_viewport_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("DEFAULT_VIEWPORT_WIDTH", "1366")
    monkeypatch.setenv("DEFAULT_VIEWPORT_HEIGHT", "768")

    payload = {
        "goal": "Open profile",
        "start_url": "https://example.com/login",
        "success_criteria": {
            "type": "text_or_dom",
            "must_include": ["Profile"],
            "must_not_include": ["Error"],
        },
        "runtime": {
            "mode": "container_desktop",
        },
        "limits": {
            "max_steps": 5,
            "time_budget_sec": 60,
            "max_retries_per_step": 1,
        },
    }

    schema = CreateRunRequestSchema.model_validate(payload)

    assert schema.runtime.viewport == {"width": 1366, "height": 768}
