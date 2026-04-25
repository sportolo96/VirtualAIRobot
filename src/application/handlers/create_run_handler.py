from __future__ import annotations

from datetime import datetime, timezone

from src.application.commands.create_run_command import CreateRunCommand
from src.application.ports.queue_client import QueueClient
from src.domain.entities.run import Run
from src.domain.repositories.run_repository import RunRepository
from src.domain.value_objects.run_limits import RunLimits


class CreateRunHandler:
    """Handle run creation and enqueue."""

    def __init__(self, run_repository: RunRepository, queue_client: QueueClient) -> None:
        self._run_repository = run_repository
        self._queue_client = queue_client

    def handle(self, command: CreateRunCommand) -> Run:
        now = datetime.now(tz=timezone.utc)
        run = Run.create(
            goal=command.goal,
            start_url=command.start_url,
            success_criteria=command.success_criteria,
            runtime=command.runtime,
            limits=RunLimits(
                max_steps=command.limits["max_steps"],
                time_budget_sec=command.limits["time_budget_sec"],
                max_retries_per_step=command.limits["max_retries_per_step"],
            ),
            allowed_actions=command.allowed_actions,
            now=now,
            callbacks=command.callbacks,
        )
        self._run_repository.save(run=run)
        self._queue_client.enqueue_process_run(run_id=run.run_id.value)
        return run
