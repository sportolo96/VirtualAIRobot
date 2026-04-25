from __future__ import annotations

from abc import ABC, abstractmethod

from src.domain.entities.run import Run


class CompletionNotifier(ABC):
    """Run completion notification contract."""

    @abstractmethod
    def handle(self, run: Run) -> None:
        """Notify external systems about terminal run state."""
