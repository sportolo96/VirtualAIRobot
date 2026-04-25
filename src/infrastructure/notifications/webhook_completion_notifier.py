from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

from src.application.ports.completion_notifier import CompletionNotifier
from src.domain.entities.run import Run


class WebhookCompletionNotifier(CompletionNotifier):
    """Webhook notifier with retry and dead-letter fallback."""

    def __init__(
        self,
        timeout_sec: int,
        max_retries: int,
        retry_backoff_sec: float,
        dead_letter_dir: Path,
        signing_secret: str = "",
    ) -> None:
        self._timeout_sec = max(1, int(timeout_sec))
        self._max_retries = max(0, int(max_retries))
        self._retry_backoff_sec = max(0.0, float(retry_backoff_sec))
        self._dead_letter_dir = dead_letter_dir
        self._signing_secret = signing_secret.encode("utf-8")
        self._logger = logging.getLogger("virtualairobot.webhook")

    def handle(self, run: Run) -> None:
        callbacks = run.callbacks if isinstance(run.callbacks, dict) else {}
        completion_url = str(callbacks.get("completion_url", "")).strip()
        if not completion_url:
            return

        raw_headers = callbacks.get("headers", {})
        headers = (
            {str(k): str(v) for k, v in raw_headers.items()}
            if isinstance(raw_headers, dict)
            else {}
        )

        payload = self._build_payload(run=run)
        body = self._serialize_payload(payload=payload)
        headers = self._prepare_headers(run=run, headers=headers, body=body)
        attempts_total = self._max_retries + 1
        last_error: str | None = None

        for attempt in range(1, attempts_total + 1):
            try:
                self._post_json(url=completion_url, body=body, headers=headers)
                return
            except Exception as exc:
                last_error = str(exc)
                self._logger.warning(
                    "Webhook completion attempt failed: run_id=%s attempt=%s/%s error=%s",
                    run.run_id.value,
                    attempt,
                    attempts_total,
                    last_error,
                )
                if attempt < attempts_total and self._retry_backoff_sec > 0:
                    time.sleep(self._retry_backoff_sec * attempt)

        self._write_dead_letter(
            run=run,
            completion_url=completion_url,
            headers=headers,
            payload=payload,
            attempts_total=attempts_total,
            last_error=last_error or "unknown",
        )

    def _build_payload(self, run: Run) -> dict[str, Any]:
        return {
            "event": "run.completed",
            "run_id": run.run_id.value,
            "status": run.status.value,
            "goal_achieved": run.goal_achieved,
            "error": run.error,
            "final_evaluation": run.final_evaluation,
            "progress": {
                "current_step": run.current_step,
                "max_steps": run.limits.max_steps,
                "elapsed_sec": run.elapsed_sec(now=datetime.now(tz=timezone.utc)),
            },
            "updated_at": run.updated_at.isoformat(),
            "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        }

    def _serialize_payload(self, payload: dict[str, Any]) -> bytes:
        return json.dumps(payload, ensure_ascii=True, sort_keys=True).encode("utf-8")

    def _prepare_headers(self, run: Run, headers: dict[str, str], body: bytes) -> dict[str, str]:
        prepared = dict(headers)
        prepared.setdefault("Content-Type", "application/json")

        timestamp = str(int(datetime.now(tz=timezone.utc).timestamp()))
        idempotency_key = f"{run.run_id.value}:{run.status.value}"
        prepared["X-VAR-Timestamp"] = timestamp
        prepared["X-VAR-Idempotency-Key"] = idempotency_key

        if self._signing_secret:
            signature = self._build_signature(timestamp=timestamp, body=body)
            prepared["X-VAR-Signature"] = signature
            prepared["X-VAR-Signature-Alg"] = "hmac-sha256"

        return prepared

    def _build_signature(self, timestamp: str, body: bytes) -> str:
        signed_payload = timestamp.encode("utf-8") + b"." + body
        digest = hmac.new(self._signing_secret, signed_payload, hashlib.sha256).hexdigest()
        return f"sha256={digest}"

    def _post_json(self, url: str, body: bytes, headers: dict[str, str]) -> None:
        req = request.Request(url=url, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self._timeout_sec) as response:
                status = int(response.getcode())
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {' '.join(detail.split())}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"URL error: {exc.reason}") from exc
        except TimeoutError as exc:
            raise RuntimeError("Request timed out") from exc

        if status < 200 or status >= 300:
            raise RuntimeError(f"HTTP {status}")

    def _write_dead_letter(
        self,
        run: Run,
        completion_url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        attempts_total: int,
        last_error: str,
    ) -> None:
        self._dead_letter_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        path = self._dead_letter_dir / f"{run.run_id.value}_{timestamp}.json"
        record = {
            "run_id": run.run_id.value,
            "event": "run.completed",
            "completion_url": completion_url,
            "headers": headers,
            "payload": payload,
            "attempts_total": attempts_total,
            "last_error": last_error,
            "written_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        path.write_text(json.dumps(record, ensure_ascii=True), encoding="utf-8")
