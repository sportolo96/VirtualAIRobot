from __future__ import annotations

from flask import Flask, jsonify

from src.bootstrap.dependency_container import DependencyContainer
from src.infrastructure.config.settings import load_settings
from src.interfaces.http.routes.runs import create_runs_blueprint


def create_app(container: DependencyContainer | None = None) -> Flask:
    """Create Flask application."""

    if container is None:
        settings = load_settings()
        container = DependencyContainer(settings=settings)

    app = Flask(__name__)
    app.register_blueprint(create_runs_blueprint(container=container))

    @app.get("/health")
    def health() -> tuple[object, int]:
        return jsonify({"status": "ok"}), 200

    return app
