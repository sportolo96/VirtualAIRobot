from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Protocol

from flask import Flask, Response, g, jsonify, request

from src.bootstrap.dependency_container import DependencyContainer
from src.infrastructure.config.settings import Settings, load_settings
from src.infrastructure.security.api_auth import (
    ApiAuthConfigError,
    ApiAuthRegistry,
    ApiAuthUnauthorized,
)
from src.interfaces.http.routes.runs import create_runs_blueprint
from src.interfaces.http.routes.webhooks import create_webhooks_blueprint


class RunsContainer(Protocol):
    """Protocol for runs route dependencies."""

    def create_create_run_handler(self) -> Any:
        raise NotImplementedError

    def create_get_run_status_handler(self) -> Any:
        raise NotImplementedError

    def create_list_run_steps_handler(self) -> Any:
        raise NotImplementedError

    def create_cancel_run_handler(self) -> Any:
        raise NotImplementedError


def _required_role_for_request(method: str, path: str) -> str | None:
    normalized_method = method.upper().strip()
    normalized_path = path.strip()

    if normalized_method == "POST" and normalized_path == "/v1/runs":
        return "runs.write"
    if normalized_method == "POST" and normalized_path.endswith("/cancel"):
        return "runs.write"
    if normalized_method == "GET" and normalized_path.startswith("/v1/runs/"):
        return "runs.read"
    return None


def create_app(
    container: RunsContainer | None = None,
    settings: Settings | None = None,
) -> Flask:
    """Create Flask application."""

    if settings is None:
        settings = load_settings()

    if container is None:
        container = DependencyContainer(settings=settings)

    app = Flask(__name__)
    http_logger = logging.getLogger("virtualairobot.http")
    auth_registry_error: str | None = None
    try:
        auth_registry = ApiAuthRegistry(
            shared_api_key=settings.api_auth_key,
            clients_json=settings.api_auth_clients_json,
        )
    except ApiAuthConfigError as exc:
        auth_registry = ApiAuthRegistry(shared_api_key=settings.api_auth_key, clients_json="")
        auth_registry_error = str(exc)

    @app.before_request
    def enforce_api_auth() -> Response | tuple[Response, int] | None:
        g.request_id = request.headers.get("X-Request-Id", "").strip() or uuid.uuid4().hex
        g.request_started = time.perf_counter()

        if request.path == "/health" or request.path.startswith("/webhooks/"):
            return None
        if not settings.api_auth_enabled:
            return None
        if auth_registry_error:
            return jsonify({"error": auth_registry_error}), 503

        if not auth_registry.is_configured():
            return (
                jsonify(
                    {
                        "error": (
                            "API auth is enabled but no keys are configured. "
                            "Set API_AUTH_KEY or API_AUTH_CLIENTS_JSON."
                        )
                    }
                ),
                503,
            )

        try:
            principal = auth_registry.authenticate(
                provided_key=request.headers.get("X-API-Key", ""),
                requested_client_id=request.headers.get("X-Client-Id", ""),
            )
        except ApiAuthUnauthorized:
            return jsonify({"error": "Unauthorized"}), 401

        required_role = _required_role_for_request(method=request.method, path=request.path)
        if not auth_registry.has_role(principal=principal, required_role=required_role):
            return jsonify({"error": "Forbidden"}), 403

        g.auth_client_id = principal.client_id
        g.auth_key_id = principal.key_id
        g.auth_source = principal.source
        return None

    @app.after_request
    def emit_request_log(response: Response) -> Response:
        request_id = getattr(g, "request_id", uuid.uuid4().hex)
        started = getattr(g, "request_started", None)
        duration_ms = (
            round((time.perf_counter() - started) * 1000, 3)
            if isinstance(started, float)
            else None
        )
        response.headers["X-Request-Id"] = request_id
        http_logger.info(
            json.dumps(
                {
                    "event": "http_request",
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "request_id": request_id,
                    "auth_client_id": getattr(g, "auth_client_id", None),
                    "auth_key_id": getattr(g, "auth_key_id", None),
                    "auth_source": getattr(g, "auth_source", None),
                },
                ensure_ascii=True,
            )
        )
        return response

    app.register_blueprint(create_runs_blueprint(container=container))
    create_webhooks = getattr(container, "create_webhook_receiver_enforcer", None)
    if callable(create_webhooks):
        app.register_blueprint(create_webhooks_blueprint(container=container))

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
