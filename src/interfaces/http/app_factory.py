from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Protocol

from flask import Flask, Response, g, jsonify, request

from src.bootstrap.dependency_container import DependencyContainer
from src.infrastructure.config.settings import Settings, load_settings
from src.interfaces.http.routes.runs import create_runs_blueprint


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

    @app.before_request
    def enforce_api_auth() -> Response | tuple[Response, int] | None:
        g.request_id = request.headers.get("X-Request-Id", "").strip() or uuid.uuid4().hex
        g.request_started = time.perf_counter()

        if request.path == "/health":
            return None
        if not settings.api_auth_enabled:
            return None

        configured_key = settings.api_auth_key.strip()
        if not configured_key:
            return jsonify({"error": "API auth is enabled but API_AUTH_KEY is not configured."}), 503

        provided_key = request.headers.get("X-API-Key", "")
        if provided_key != configured_key:
            return jsonify({"error": "Unauthorized"}), 401
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
                },
                ensure_ascii=True,
            )
        )
        return response

    app.register_blueprint(create_runs_blueprint(container=container))

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
