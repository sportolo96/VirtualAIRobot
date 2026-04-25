from __future__ import annotations

from pathlib import Path

import pytest

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
        ai_provider="openai",
        ai_fallback_providers=(),
        ai_model="gpt-5.4",
        planner_model="gpt-5.4",
        evaluator_model="gpt-5.4",
        openai_api_key="test-key",
        azure_openai_api_key="",
        azure_openai_api_base_url="",
        azure_openai_api_version="2024-10-21",
        api_auth_enabled=False,
        api_auth_key="",
        api_auth_clients_json="",
        webhook_enabled=False,
        webhook_timeout_sec=10,
        webhook_max_retries=3,
        webhook_retry_backoff_sec=1.0,
        webhook_signing_secret="",
        webhook_dead_letter_dir=tmp_path / "dead_letters",
        webhook_receiver_enabled=False,
        webhook_receiver_signing_secret="",
        webhook_receiver_require_signature=True,
        webhook_receiver_max_age_sec=300,
        webhook_receiver_idempotency_ttl_sec=86400,
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


def test_dependency_container_ai_runtime_ready_requires_api_key(monkeypatch, tmp_path: Path) -> None:
    planner = tmp_path / "planner_prompt.txt"
    evaluator = tmp_path / "evaluator_prompt.txt"
    planner.write_text("Goal: {goal}\n{format_instructions}", encoding="utf-8")
    evaluator.write_text("Goal: {goal}\n{format_instructions}", encoding="utf-8")

    monkeypatch.setattr(container_module.Redis, "from_url", lambda _url: object())
    monkeypatch.setattr(container_module, "RqQueueClient", QueueClientStub)

    settings = Settings(
        redis_url="redis://unused:6379/0",
        queue_name="runs",
        ai_provider="openai",
        ai_fallback_providers=(),
        ai_model="gpt-5.4",
        planner_model="gpt-5.4",
        evaluator_model="gpt-5.4",
        openai_api_key="",
        azure_openai_api_key="",
        azure_openai_api_base_url="",
        azure_openai_api_version="2024-10-21",
        api_auth_enabled=False,
        api_auth_key="",
        api_auth_clients_json="",
        webhook_enabled=False,
        webhook_timeout_sec=10,
        webhook_max_retries=3,
        webhook_retry_backoff_sec=1.0,
        webhook_signing_secret="",
        webhook_dead_letter_dir=tmp_path / "dead_letters",
        webhook_receiver_enabled=False,
        webhook_receiver_signing_secret="",
        webhook_receiver_require_signature=True,
        webhook_receiver_max_age_sec=300,
        webhook_receiver_idempotency_ttl_sec=86400,
        artifact_root=tmp_path / "artifacts",
        planner_template_path=planner,
        evaluator_template_path=evaluator,
        flask_host="0.0.0.0",
        flask_port=8000,
    )

    container = container_module.DependencyContainer(settings=settings)

    with pytest.raises(RuntimeError) as exc_info:
        container.assert_ai_runtime_ready()

    assert str(exc_info.value) == "AI runtime is not configured. Set OPENAI_API_KEY to start runs."


def test_dependency_container_ai_runtime_ready_checks_live_connectivity(
    monkeypatch, tmp_path: Path
) -> None:
    planner = tmp_path / "planner_prompt.txt"
    evaluator = tmp_path / "evaluator_prompt.txt"
    planner.write_text("Goal: {goal}\n{format_instructions}", encoding="utf-8")
    evaluator.write_text("Goal: {goal}\n{format_instructions}", encoding="utf-8")

    monkeypatch.setattr(container_module.Redis, "from_url", lambda _url: object())
    monkeypatch.setattr(container_module, "RqQueueClient", QueueClientStub)
    captured: list[str] = []
    monkeypatch.setattr(
        container_module.OpenAIResponsesClient,
        "health_check",
        lambda self, model: captured.append(model),
    )

    settings = Settings(
        redis_url="redis://unused:6379/0",
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
        api_auth_enabled=False,
        api_auth_key="",
        api_auth_clients_json="",
        webhook_enabled=False,
        webhook_timeout_sec=10,
        webhook_max_retries=3,
        webhook_retry_backoff_sec=1.0,
        webhook_signing_secret="",
        webhook_dead_letter_dir=tmp_path / "dead_letters",
        webhook_receiver_enabled=False,
        webhook_receiver_signing_secret="",
        webhook_receiver_require_signature=True,
        webhook_receiver_max_age_sec=300,
        webhook_receiver_idempotency_ttl_sec=86400,
        artifact_root=tmp_path / "artifacts",
        planner_template_path=planner,
        evaluator_template_path=evaluator,
        flask_host="0.0.0.0",
        flask_port=8000,
    )

    container = container_module.DependencyContainer(settings=settings)
    container.assert_ai_runtime_ready()

    assert captured == ["gpt-5.4"]


def test_dependency_container_ai_runtime_ready_uses_fallback_provider(
    monkeypatch, tmp_path: Path
) -> None:
    planner = tmp_path / "planner_prompt.txt"
    evaluator = tmp_path / "evaluator_prompt.txt"
    planner.write_text("Goal: {goal}\n{format_instructions}", encoding="utf-8")
    evaluator.write_text("Goal: {goal}\n{format_instructions}", encoding="utf-8")

    monkeypatch.setattr(container_module.Redis, "from_url", lambda _url: object())
    monkeypatch.setattr(container_module, "RqQueueClient", QueueClientStub)
    calls: list[str] = []

    def _openai_health_check(self, model: str) -> None:
        _ = model
        calls.append("openai")
        raise RuntimeError("openai outage")

    def _azure_health_check(self, model: str) -> None:
        _ = model
        calls.append("azure_openai")

    monkeypatch.setattr(container_module.OpenAIResponsesClient, "health_check", _openai_health_check)
    monkeypatch.setattr(
        container_module.AzureOpenAIResponsesClient,
        "health_check",
        _azure_health_check,
    )

    settings = Settings(
        redis_url="redis://unused:6379/0",
        queue_name="runs",
        ai_provider="openai",
        ai_fallback_providers=("azure_openai",),
        ai_model="gpt-5.4",
        planner_model="gpt-5.4",
        evaluator_model="gpt-5.4",
        openai_api_key="test-key",
        azure_openai_api_key="azure-key",
        azure_openai_api_base_url="https://example.openai.azure.com/openai/v1",
        azure_openai_api_version="2024-10-21",
        api_auth_enabled=False,
        api_auth_key="",
        api_auth_clients_json="",
        webhook_enabled=False,
        webhook_timeout_sec=10,
        webhook_max_retries=3,
        webhook_retry_backoff_sec=1.0,
        webhook_signing_secret="",
        webhook_dead_letter_dir=tmp_path / "dead_letters",
        webhook_receiver_enabled=False,
        webhook_receiver_signing_secret="",
        webhook_receiver_require_signature=True,
        webhook_receiver_max_age_sec=300,
        webhook_receiver_idempotency_ttl_sec=86400,
        artifact_root=tmp_path / "artifacts",
        planner_template_path=planner,
        evaluator_template_path=evaluator,
        flask_host="0.0.0.0",
        flask_port=8000,
    )

    container = container_module.DependencyContainer(settings=settings)
    container.assert_ai_runtime_ready()

    assert calls == ["openai", "azure_openai"]


def test_dependency_container_creates_webhook_receiver_enforcer_when_enabled(
    monkeypatch, tmp_path: Path
) -> None:
    planner = tmp_path / "planner_prompt.txt"
    evaluator = tmp_path / "evaluator_prompt.txt"
    planner.write_text("Goal: {goal}\n{format_instructions}", encoding="utf-8")
    evaluator.write_text("Goal: {goal}\n{format_instructions}", encoding="utf-8")

    monkeypatch.setattr(container_module.Redis, "from_url", lambda _url: object())
    monkeypatch.setattr(container_module, "RqQueueClient", QueueClientStub)

    settings = Settings(
        redis_url="redis://unused:6379/0",
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
        api_auth_enabled=False,
        api_auth_key="",
        api_auth_clients_json="",
        webhook_enabled=False,
        webhook_timeout_sec=10,
        webhook_max_retries=3,
        webhook_retry_backoff_sec=1.0,
        webhook_signing_secret="",
        webhook_dead_letter_dir=tmp_path / "dead_letters",
        webhook_receiver_enabled=True,
        webhook_receiver_signing_secret="whsec",
        webhook_receiver_require_signature=True,
        webhook_receiver_max_age_sec=300,
        webhook_receiver_idempotency_ttl_sec=86400,
        artifact_root=tmp_path / "artifacts",
        planner_template_path=planner,
        evaluator_template_path=evaluator,
        flask_host="0.0.0.0",
        flask_port=8000,
    )

    container = container_module.DependencyContainer(settings=settings)

    assert container.create_webhook_receiver_enforcer() is not None
