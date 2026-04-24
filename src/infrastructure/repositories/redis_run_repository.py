from __future__ import annotations

import json
from typing import Any

from src.domain.entities.run import Run
from src.domain.repositories.run_repository import RunRepository
from src.domain.value_objects.run_id import RunId
from src.infrastructure.transformers.run_transformer import RunTransformer


class RedisRunRepository(RunRepository):
    """Redis-backed run repository."""

    def __init__(self, redis_client: Any, transformer: RunTransformer) -> None:
        self._redis_client = redis_client
        self._transformer = transformer

    def save(self, run: Run) -> None:
        key = self._run_key(run_id=run.run_id.value)
        record = self._transformer.to_record(run=run)
        self._redis_client.set(key, json.dumps(record))

    def get(self, run_id: RunId) -> Run | None:
        key = self._run_key(run_id=run_id.value)
        payload = self._redis_client.get(key)
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        elif not isinstance(payload, str):
            payload = str(payload)
        record = json.loads(payload)
        return self._transformer.from_record(record=record)

    def _run_key(self, run_id: str) -> str:
        return f"run:{run_id}"
