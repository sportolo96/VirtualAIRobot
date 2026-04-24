from __future__ import annotations

from typing import Any, Protocol

from flask import Flask, jsonify

from src.bootstrap.dependency_container import DependencyContainer
from src.infrastructure.config.settings import load_settings
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


def create_app(container: RunsContainer | None = None) -> Flask:
    """Create Flask application."""

    if container is None:
        settings = load_settings()
        container = DependencyContainer(settings=settings)

    app = Flask(__name__)
    app.register_blueprint(create_runs_blueprint(container=container))

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
