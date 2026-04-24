from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.interfaces.worker import jobs


@dataclass(frozen=True)
class FakeSettings:
    redis_url: str = "redis://test:6379/0"
    queue_name: str = "runs"
    artifact_root: Path = Path("/tmp/artifacts")
    planner_template_path: Path = Path("/tmp/planner.txt")
    evaluator_template_path: Path = Path("/tmp/evaluator.txt")
    flask_host: str = "0.0.0.0"
    flask_port: int = 8000


class ProcessRunHandlerSpy:
    """Spy handler for worker job tests."""

    def __init__(self) -> None:
        self.run_ids: list[str] = []

    def handle(self, command) -> None:
        self.run_ids.append(command.run_id)


class DependencyContainerStub:
    """Container stub for worker job tests."""

    def __init__(self, settings) -> None:
        self.settings = settings
        self.handler = ProcessRunHandlerSpy()

    def create_process_run_handler(self) -> ProcessRunHandlerSpy:
        return self.handler


def test_process_run_job_uses_container_and_handler(monkeypatch) -> None:
    container_holder: dict[str, DependencyContainerStub] = {}

    def _container_factory(settings) -> DependencyContainerStub:
        container = DependencyContainerStub(settings=settings)
        container_holder["container"] = container
        return container

    monkeypatch.setattr(jobs, "load_settings", lambda: FakeSettings())
    monkeypatch.setattr(jobs, "DependencyContainer", _container_factory)

    jobs.process_run_job(run_id="run_123")

    container = container_holder["container"]
    assert container.handler.run_ids == ["run_123"]
