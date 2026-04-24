from __future__ import annotations

import socket
from datetime import datetime, timezone
from typing import Any, Callable

import pytest

from src.domain.entities.run import Run
from src.domain.value_objects.run_limits import RunLimits


@pytest.fixture(autouse=True)
def block_network_access(monkeypatch: pytest.MonkeyPatch) -> None:
    """Disable outbound network access and real AI calls for every test."""

    def _blocked_connect(self: socket.socket, *args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Network access is disabled in tests")

    def _blocked_create_connection(*args: Any, **kwargs: Any) -> None:
        raise RuntimeError("Network access is disabled in tests")

    def _blocked_connect_ex(self: socket.socket, *args: Any, **kwargs: Any) -> int:
        raise RuntimeError("Network access is disabled in tests")

    monkeypatch.setattr(socket.socket, "connect", _blocked_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", _blocked_connect_ex)
    monkeypatch.setattr(socket, "create_connection", _blocked_create_connection)


@pytest.fixture
def run_factory() -> Callable[..., Run]:
    """Create run aggregate instances with defaults."""

    def _factory(**overrides: Any) -> Run:
        now = overrides.pop("now", datetime.now(tz=timezone.utc))
        return Run.create(
            goal=overrides.pop("goal", "Open profile"),
            start_url=overrides.pop("start_url", "https://example.com"),
            success_criteria=overrides.pop(
                "success_criteria",
                {"type": "text_or_dom", "must_include": ["Profile"], "must_not_include": []},
            ),
            runtime=overrides.pop(
                "runtime",
                {"mode": "container_desktop", "viewport": {"width": 1080, "height": 1920}},
            ),
            limits=overrides.pop(
                "limits", RunLimits(max_steps=5, time_budget_sec=60, max_retries_per_step=1)
            ),
            allowed_actions=overrides.pop(
                "allowed_actions",
                ["move", "click", "scroll", "type", "key", "wait", "done", "failed"],
            ),
            llm=overrides.pop(
                "llm", {"planner_model": "gpt-5.4", "evaluator_model": "gpt-5.4"}
            ),
            now=now,
        )

    return _factory
