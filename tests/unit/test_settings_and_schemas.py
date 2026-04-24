from __future__ import annotations

from pathlib import Path

from src.infrastructure.config.settings import load_settings
from src.interfaces.http.schemas import CreateRunRequestSchema


def test_load_settings_defaults(monkeypatch) -> None:
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("QUEUE_NAME", raising=False)
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    monkeypatch.delenv("AI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ARTIFACT_ROOT", raising=False)
    monkeypatch.delenv("PLANNER_TEMPLATE_PATH", raising=False)
    monkeypatch.delenv("EVALUATOR_TEMPLATE_PATH", raising=False)
    monkeypatch.delenv("FLASK_HOST", raising=False)
    monkeypatch.delenv("FLASK_PORT", raising=False)

    settings = load_settings()

    assert settings.redis_url == "redis://redis:6379/0"
    assert settings.queue_name == "runs"
    assert settings.ai_provider == "openai"
    assert settings.ai_model == "gpt-5.4"
    assert settings.openai_api_key == ""
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
    monkeypatch.setenv("AI_MODEL", "gpt-5.4")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    monkeypatch.setenv("PLANNER_TEMPLATE_PATH", str(planner))
    monkeypatch.setenv("EVALUATOR_TEMPLATE_PATH", str(evaluator))
    monkeypatch.setenv("FLASK_HOST", "127.0.0.1")
    monkeypatch.setenv("FLASK_PORT", "5001")

    settings = load_settings()

    assert settings.redis_url == "redis://localhost:6380/1"
    assert settings.queue_name == "custom"
    assert settings.ai_provider == "openai"
    assert settings.ai_model == "gpt-5.4"
    assert settings.openai_api_key == "test-key"
    assert settings.artifact_root == tmp_path / "artifacts"
    assert settings.planner_template_path == planner
    assert settings.evaluator_template_path == evaluator
    assert settings.flask_host == "127.0.0.1"
    assert settings.flask_port == 5001


def test_create_run_schema_defaults_chatgpt_and_terminal_actions() -> None:
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

    assert schema.llm.planner_model == "gpt-5.4"
    assert schema.llm.evaluator_model == "gpt-5.4"
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
