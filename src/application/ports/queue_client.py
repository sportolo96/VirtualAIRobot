from __future__ import annotations

from abc import ABC, abstractmethod


class QueueClient(ABC):
    """Queue producer contract."""

    @abstractmethod
    def enqueue_process_run(self, run_id: str) -> None:
        raise NotImplementedError
