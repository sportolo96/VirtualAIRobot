from __future__ import annotations

import hashlib
import hmac
import json
from pathlib import Path
from typing import Any
from urllib import error

from src.infrastructure.notifications import webhook_completion_notifier as notifier_module
from src.infrastructure.notifications.webhook_completion_notifier import WebhookCompletionNotifier


def test_webhook_notifier_skips_when_completion_url_missing(run_factory, monkeypatch) -> None:
    called: list[bool] = []

    def _urlopen_stub(*args, **kwargs):
        _ = (args, kwargs)
        called.append(True)
        raise AssertionError("urlopen must not be called when completion_url is missing")

    monkeypatch.setattr(notifier_module.request, "urlopen", _urlopen_stub)

    run = run_factory(callbacks={})
    notifier = WebhookCompletionNotifier(
        timeout_sec=5,
        max_retries=2,
        retry_backoff_sec=0,
        dead_letter_dir=Path("."),
    )
    notifier.handle(run=run)

    assert called == []


def test_webhook_notifier_posts_payload_once_on_success(run_factory, monkeypatch, tmp_path) -> None:
    captured: dict[str, Any] = {}

    class _ResponseStub:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = (exc_type, exc, tb)
            return False

        def getcode(self) -> int:
            return 204

    def _urlopen_stub(req, timeout: int):
        captured["url"] = req.full_url
        captured["timeout"] = timeout
        captured["headers"] = dict(req.header_items())
        captured["raw_body"] = req.data.decode("utf-8")
        captured["payload"] = json.loads(req.data.decode("utf-8"))
        return _ResponseStub()

    monkeypatch.setattr(notifier_module.request, "urlopen", _urlopen_stub)

    run = run_factory(
        callbacks={
            "completion_url": "https://example.test/webhook",
            "headers": {"X-Webhook-Key": "secret"},
        }
    )
    run.mark_succeeded(now=run.updated_at, final_evaluation={"terminal_action": "done"})
    notifier = WebhookCompletionNotifier(
        timeout_sec=7,
        max_retries=2,
        retry_backoff_sec=0,
        dead_letter_dir=tmp_path,
    )

    notifier.handle(run=run)

    assert captured["url"] == "https://example.test/webhook"
    assert captured["timeout"] == 7
    headers = captured["headers"]
    assert isinstance(headers, dict)
    lowered_headers = {str(k).lower(): v for k, v in headers.items()}
    assert "content-type" in lowered_headers
    assert "x-var-idempotency-key" in lowered_headers
    assert "x-var-timestamp" in lowered_headers
    assert "x-var-signature" not in lowered_headers
    payload = captured["payload"]
    assert isinstance(payload, dict)
    assert payload["event"] == "run.completed"
    assert payload["run_id"] == run.run_id.value


def test_webhook_notifier_signs_payload_when_secret_is_configured(
    run_factory, monkeypatch, tmp_path
) -> None:
    captured: dict[str, Any] = {}

    class _ResponseStub:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            _ = (exc_type, exc, tb)
            return False

        def getcode(self) -> int:
            return 200

    def _urlopen_stub(req, timeout: int):
        captured["timeout"] = timeout
        captured["headers"] = dict(req.header_items())
        captured["raw_body"] = req.data.decode("utf-8")
        return _ResponseStub()

    monkeypatch.setattr(notifier_module.request, "urlopen", _urlopen_stub)

    run = run_factory(callbacks={"completion_url": "https://example.test/webhook"})
    run.mark_succeeded(now=run.updated_at, final_evaluation={"terminal_action": "done"})
    notifier = WebhookCompletionNotifier(
        timeout_sec=7,
        max_retries=0,
        retry_backoff_sec=0,
        dead_letter_dir=tmp_path,
        signing_secret="whsec_test",
    )

    notifier.handle(run=run)

    lowered_headers = {str(k).lower(): str(v) for k, v in captured["headers"].items()}
    timestamp = lowered_headers["x-var-timestamp"]
    signature = lowered_headers["x-var-signature"]
    signed_payload = f"{timestamp}.{captured['raw_body']}".encode("utf-8")
    expected = hmac.new(b"whsec_test", signed_payload, hashlib.sha256).hexdigest()
    assert signature == f"sha256={expected}"
    assert lowered_headers["x-var-signature-alg"] == "hmac-sha256"


def test_webhook_notifier_writes_dead_letter_after_retries(
    run_factory, monkeypatch, tmp_path
) -> None:
    attempts: list[int] = []

    def _urlopen_stub(req, timeout: int):
        _ = (req, timeout)
        attempts.append(1)
        raise error.URLError("connection refused")

    monkeypatch.setattr(notifier_module.request, "urlopen", _urlopen_stub)
    monkeypatch.setattr(notifier_module.time, "sleep", lambda seconds: None)

    run = run_factory(callbacks={"completion_url": "https://example.test/webhook"})
    run.mark_failed(now=run.updated_at, reason="Maximum steps reached")
    notifier = WebhookCompletionNotifier(
        timeout_sec=5,
        max_retries=2,
        retry_backoff_sec=0.1,
        dead_letter_dir=tmp_path / "dead_letters",
    )

    notifier.handle(run=run)

    assert len(attempts) == 3
    dead_letters = list((tmp_path / "dead_letters").glob("*.json"))
    assert len(dead_letters) == 1
    record = json.loads(dead_letters[0].read_text(encoding="utf-8"))
    assert record["run_id"] == run.run_id.value
    assert record["attempts_total"] == 3
    assert "X-VAR-Idempotency-Key" in record["headers"]
    assert "URL error" in record["last_error"]
