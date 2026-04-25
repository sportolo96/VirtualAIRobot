from __future__ import annotations

from src.application.ports.completion_notifier import CompletionNotifier
from src.domain.entities.run import Run


class NoOpCompletionNotifier(CompletionNotifier):
    """No-op notifier used when callbacks are disabled."""

    def handle(self, run: Run) -> None:
        _ = run
