from __future__ import annotations

from flask import Flask

from src.interfaces.http.app_factory import create_app


class HandlerStub:
    """Generic handler stub."""

    def handle(self, **kwargs):
        _ = kwargs
        return None


class MinimalContainer:
    """Minimal container for app factory tests."""

    def create_create_run_handler(self):
        return HandlerStub()

    def create_get_run_status_handler(self):
        return HandlerStub()

    def create_list_run_steps_handler(self):
        return HandlerStub()

    def create_cancel_run_handler(self):
        return HandlerStub()


def test_health_endpoint_is_available_with_container() -> None:
    app: Flask = create_app(container=MinimalContainer())
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
