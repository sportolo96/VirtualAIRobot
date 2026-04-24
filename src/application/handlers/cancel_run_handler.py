from __future__ import annotations

from datetime import datetime, timezone

from src.application.commands.cancel_run_command import CancelRunCommand
from src.domain.entities.run import Run
from src.domain.repositories.run_repository import RunRepository
from src.domain.value_objects.run_id import RunId


class CancelRunHandler:
    """Handle run cancellation requests."""

    def __init__(self, run_repository: RunRepository) -> None:
        self._run_repository = run_repository

    def handle(self, command: CancelRunCommand) -> Run | None:
        run = self._run_repository.get(run_id=RunId(value=command.run_id))
        if run is None:
            return None
        now = datetime.now(tz=timezone.utc)
        run.request_cancel(now=now)
        self._run_repository.save(run=run)
        return run
