# Webhook Receiver Validation Guide

This guide provides a production-oriented validation baseline for `run.completed` callbacks.

## Required request inputs
- Header: `X-VAR-Timestamp`
- Header: `X-VAR-Idempotency-Key`
- Optional header (when signing is enabled): `X-VAR-Signature`
- Raw request body bytes

## Validation flow
1. Read the raw request body bytes before JSON parsing.
2. Validate `X-VAR-Timestamp` format and reject stale values outside replay window (example: 300 seconds).
3. Verify idempotency using `X-VAR-Idempotency-Key` (example: Redis `SET key value NX EX 86400`).
4. If signing is enabled, verify HMAC signature over `"{timestamp}.{raw_body}"`.
5. Parse JSON payload only after header and signature checks pass.

## Flask reference implementation
```python
from __future__ import annotations

import hashlib
import hmac
import time
from typing import Final

from flask import Flask, abort, request
from redis import Redis

WEBHOOK_SECRET: Final[str] = "replace_with_secret"
MAX_AGE_SEC: Final[int] = 300
IDEMPOTENCY_TTL_SEC: Final[int] = 86400

app = Flask(__name__)
redis_client = Redis.from_url("redis://localhost:6379/0")


def _verify_signature(timestamp: str, body: bytes, signature: str, secret: str) -> bool:
    signed_payload = f"{timestamp}.".encode("utf-8") + body
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, f"sha256={expected}")


@app.post("/webhooks/virtualairobot")
def webhook_receiver():
    timestamp = request.headers.get("X-VAR-Timestamp", "").strip()
    idempotency_key = request.headers.get("X-VAR-Idempotency-Key", "").strip()
    signature = request.headers.get("X-VAR-Signature", "").strip()

    if not timestamp or not idempotency_key:
        abort(400, description="Missing required webhook headers")

    try:
        ts = int(timestamp)
    except ValueError:
        abort(400, description="Invalid timestamp header")

    now = int(time.time())
    if abs(now - ts) > MAX_AGE_SEC:
        abort(409, description="Stale webhook timestamp")

    dedupe_key = f"var:webhook:{idempotency_key}"
    accepted = redis_client.set(
        dedupe_key,
        "1",
        ex=IDEMPOTENCY_TTL_SEC,
        nx=True,
    )
    if not accepted:
        return {"status": "duplicate"}, 200

    raw_body = request.get_data(cache=False, as_text=False)

    if WEBHOOK_SECRET:
        if not signature:
            abort(401, description="Missing signature header")
        if not _verify_signature(timestamp=timestamp, body=raw_body, signature=signature, secret=WEBHOOK_SECRET):
            abort(401, description="Invalid webhook signature")

    payload = request.get_json(force=True, silent=False)
    event = str(payload.get("event", ""))
    if event != "run.completed":
        abort(400, description="Unsupported event")

    return {"status": "ok"}, 200
```

## Secret rotation pattern
- Keep two secrets during rollout window: `ACTIVE_SECRET`, `PREVIOUS_SECRET`.
- Accept callback if either secret verifies.
- Remove `PREVIOUS_SECRET` after sender rollout is complete.

## Operational recommendations
- Keep webhook endpoint behind HTTPS only.
- Add receiver-side structured logs for signature failures and duplicate events.
- Alert when signature mismatch rate increases.
- Preserve failed payloads in receiver dead-letter storage for manual replay.
