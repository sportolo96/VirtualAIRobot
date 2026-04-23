from __future__ import annotations

from src.application.commands.process_run_command import ProcessRunCommand
from src.bootstrap.dependency_container import DependencyContainer
from src.infrastructure.config.settings import load_settings


def process_run_job(run_id: str) -> None:
    """Process run queue job."""

    settings = load_settings()
    container = DependencyContainer(settings=settings)
    handler = container.create_process_run_handler()
    handler.handle(command=ProcessRunCommand(run_id=run_id))
