from __future__ import annotations

import hashlib
import hmac

import pytest

from src.infrastructure.security import webhook_receiver_enforcer as enforcer_module
from src.infrastructure.security.webhook_receiver_enforcer import (
    WebhookReceiverEnforcer,
    WebhookVerificationError,
)


class FakeRedis:
    """Minimal redis set(nx/ex) behavior for webhook idempotency tests."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}

    def set(self, key: str, value: str, ex: int, nx: bool):  # noqa: ANN001
        _ = ex
        if nx and key in self._values:
            return None
        self._values[key] = value
        return True


def _signature(secret: str, timestamp: str, body: bytes) -> str:
    signed_payload = timestamp.encode("utf-8") + b"." + body
    digest = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def test_webhook_receiver_enforcer_accepts_valid_signed_request(monkeypatch) -> None:
    monkeypatch.setattr(enforcer_module.time, "time", lambda: 1_700_000_000)
    redis_client = FakeRedis()
    enforcer = WebhookReceiverEnforcer(
        redis_client=redis_client,
        signing_secret="whsec",
        max_age_sec=300,
        idempotency_ttl_sec=3600,
        require_signature=True,
    )
    body = b'{"event":"run.completed","run_id":"run_1"}'
    timestamp = "1700000000"
    headers = {
        "X-VAR-Timestamp": timestamp,
        "X-VAR-Idempotency-Key": "run_1:succeeded",
        "X-VAR-Signature": _signature("whsec", timestamp, body),
    }

    result = enforcer.enforce(headers=headers, raw_body=body)

    assert result == "accepted"


def test_webhook_receiver_enforcer_returns_duplicate_on_second_request(monkeypatch) -> None:
    monkeypatch.setattr(enforcer_module.time, "time", lambda: 1_700_000_000)
    redis_client = FakeRedis()
    enforcer = WebhookReceiverEnforcer(
        redis_client=redis_client,
        signing_secret="whsec",
        max_age_sec=300,
        idempotency_ttl_sec=3600,
        require_signature=True,
    )
    body = b'{"event":"run.completed","run_id":"run_1"}'
    timestamp = "1700000000"
    headers = {
        "X-VAR-Timestamp": timestamp,
        "X-VAR-Idempotency-Key": "run_1:succeeded",
        "X-VAR-Signature": _signature("whsec", timestamp, body),
    }

    first = enforcer.enforce(headers=headers, raw_body=body)
    second = enforcer.enforce(headers=headers, raw_body=body)

    assert first == "accepted"
    assert second == "duplicate"


def test_webhook_receiver_enforcer_rejects_stale_timestamp(monkeypatch) -> None:
    monkeypatch.setattr(enforcer_module.time, "time", lambda: 1_700_000_500)
    redis_client = FakeRedis()
    enforcer = WebhookReceiverEnforcer(
        redis_client=redis_client,
        signing_secret="whsec",
        max_age_sec=300,
        idempotency_ttl_sec=3600,
        require_signature=True,
    )
    body = b'{"event":"run.completed"}'
    timestamp = "1700000000"
    headers = {
        "X-VAR-Timestamp": timestamp,
        "X-VAR-Idempotency-Key": "run_1:succeeded",
        "X-VAR-Signature": _signature("whsec", timestamp, body),
    }

    with pytest.raises(WebhookVerificationError) as exc_info:
        enforcer.enforce(headers=headers, raw_body=body)

    assert exc_info.value.status_code == 409


def test_webhook_receiver_enforcer_allows_unsigned_when_optional(monkeypatch) -> None:
    monkeypatch.setattr(enforcer_module.time, "time", lambda: 1_700_000_000)
    redis_client = FakeRedis()
    enforcer = WebhookReceiverEnforcer(
        redis_client=redis_client,
        signing_secret="",
        max_age_sec=300,
        idempotency_ttl_sec=3600,
        require_signature=False,
    )
    body = b'{"event":"run.completed"}'
    headers = {
        "X-VAR-Timestamp": "1700000000",
        "X-VAR-Idempotency-Key": "run_1:succeeded",
    }

    result = enforcer.enforce(headers=headers, raw_body=body)

    assert result == "accepted"
