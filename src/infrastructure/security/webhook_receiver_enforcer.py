from __future__ import annotations

import hashlib
import hmac
import time
from collections.abc import Mapping


class WebhookVerificationError(Exception):
    """Webhook verification failure with explicit HTTP status code."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code


class WebhookReceiverEnforcer:
    """Centralized webhook security validator."""

    def __init__(
        self,
        redis_client,
        signing_secret: str,
        max_age_sec: int,
        idempotency_ttl_sec: int,
        require_signature: bool,
    ) -> None:
        self._redis_client = redis_client
        self._signing_secret = signing_secret.encode("utf-8")
        self._max_age_sec = max(1, int(max_age_sec))
        self._idempotency_ttl_sec = max(1, int(idempotency_ttl_sec))
        self._require_signature = bool(require_signature)

    def enforce(self, headers: Mapping[str, str], raw_body: bytes) -> str:
        timestamp_raw = self._get_header(headers=headers, name="X-VAR-Timestamp")
        idempotency_key = self._get_header(headers=headers, name="X-VAR-Idempotency-Key")
        signature = self._get_header(headers=headers, name="X-VAR-Signature")

        if not timestamp_raw or not idempotency_key:
            raise WebhookVerificationError("Missing webhook security headers.", 400)

        try:
            timestamp = int(timestamp_raw)
        except ValueError as exc:
            raise WebhookVerificationError("Invalid webhook timestamp header.", 400) from exc

        now = int(time.time())
        if abs(now - timestamp) > self._max_age_sec:
            raise WebhookVerificationError("Webhook timestamp outside replay window.", 409)

        if self._require_signature and not self._signing_secret:
            raise WebhookVerificationError(
                "Webhook signature is required but receiver secret is not configured.",
                503,
            )

        if self._signing_secret:
            if not signature:
                raise WebhookVerificationError("Missing webhook signature header.", 401)
            if not self._verify_signature(
                timestamp=timestamp_raw,
                raw_body=raw_body,
                signature=signature,
            ):
                raise WebhookVerificationError("Invalid webhook signature.", 401)
        elif self._require_signature:
            raise WebhookVerificationError("Webhook signature is required.", 401)

        storage_key = f"webhook:run_completion:idem:{idempotency_key}"
        inserted = self._redis_client.set(
            storage_key,
            "1",
            ex=self._idempotency_ttl_sec,
            nx=True,
        )
        if not bool(inserted):
            return "duplicate"
        return "accepted"

    def _verify_signature(self, timestamp: str, raw_body: bytes, signature: str) -> bool:
        signed_payload = timestamp.encode("utf-8") + b"." + raw_body
        expected = hmac.new(self._signing_secret, signed_payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, f"sha256={expected}")

    def _get_header(self, headers: Mapping[str, str], name: str) -> str:
        value = headers.get(name)
        if isinstance(value, str) and value.strip():
            return value.strip()

        lowered = name.lower()
        for key, raw in headers.items():
            if str(key).lower() != lowered:
                continue
            if isinstance(raw, str):
                return raw.strip()
            return str(raw).strip()
        return ""
