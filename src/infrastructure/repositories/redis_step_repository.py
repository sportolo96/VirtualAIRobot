from __future__ import annotations

import json

from redis import Redis

from src.domain.entities.step import Step
from src.domain.repositories.step_repository import StepRepository
from src.domain.value_objects.run_id import RunId
from src.infrastructure.transformers.step_transformer import StepTransformer


class RedisStepRepository(StepRepository):
    """Redis-backed step repository."""

    def __init__(self, redis_client: Redis, transformer: StepTransformer) -> None:
        self._redis_client = redis_client
        self._transformer = transformer

    def add(self, step: Step) -> None:
        key = self._steps_key(run_id=step.run_id.value)
        record = self._transformer.to_record(step=step)
        self._redis_client.rpush(key, json.dumps(record))

    def list_by_run_id(self, run_id: RunId) -> list[Step]:
        key = self._steps_key(run_id=run_id.value)
        payloads = self._redis_client.lrange(key, 0, -1)
        steps: list[Step] = []
        for payload in payloads:
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            record = json.loads(payload)
            steps.append(self._transformer.from_record(record=record))
        return steps

    def _steps_key(self, run_id: str) -> str:
        return f"run:{run_id}:steps"
