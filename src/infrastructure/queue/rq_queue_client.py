from __future__ import annotations

from typing import Any

from rq import Queue

from src.application.ports.queue_client import QueueClient


class RqQueueClient(QueueClient):
    """RQ-based queue producer."""

    def __init__(self, redis_client: Any, queue_name: str, job_path: str) -> None:
        self._queue = Queue(name=queue_name, connection=redis_client)
        self._job_path = job_path

    def enqueue_process_run(self, run_id: str) -> None:
        self._queue.enqueue(self._job_path, run_id)
