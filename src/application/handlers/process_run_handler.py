from __future__ import annotations

from src.application.commands.process_run_command import ProcessRunCommand
from src.domain.services.run_execution_service import RunExecutionService


class ProcessRunHandler:
    """Handle run processing trigger."""

    def __init__(self, run_execution_service: RunExecutionService) -> None:
        self._run_execution_service = run_execution_service

    def handle(self, command: ProcessRunCommand) -> None:
        self._run_execution_service.handle(run_id=command.run_id)
