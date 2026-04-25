from __future__ import annotations

import json
from typing import Any

from flask import Blueprint, Response, jsonify, request

from src.infrastructure.security.webhook_receiver_enforcer import WebhookVerificationError


def create_webhooks_blueprint(container: Any) -> Blueprint:
    """Create webhook receiver blueprint."""

    blueprint = Blueprint(name="webhooks", import_name=__name__)
    enforcer_factory = getattr(container, "create_webhook_receiver_enforcer", None)
    enforcer = enforcer_factory() if callable(enforcer_factory) else None

    @blueprint.post("/webhooks/run-completion")
    def receive_run_completion() -> tuple[Response, int]:
        if enforcer is None:
            return jsonify({"error": "Webhook receiver is disabled."}), 503

        raw_body = request.get_data(cache=False, as_text=False)
        try:
            verification_state = enforcer.enforce(headers=request.headers, raw_body=raw_body)
        except WebhookVerificationError as exc:
            return jsonify({"error": str(exc)}), exc.status_code

        try:
            payload: Any = json.loads(raw_body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return jsonify({"error": "Invalid webhook JSON payload."}), 400

        if not isinstance(payload, dict):
            return jsonify({"error": "Invalid webhook JSON payload."}), 400

        if str(payload.get("event", "")).strip() != "run.completed":
            return jsonify({"error": "Unsupported webhook event."}), 400

        if verification_state == "duplicate":
            return jsonify({"status": "duplicate"}), 200
        return jsonify({"status": "accepted"}), 202

    return blueprint
