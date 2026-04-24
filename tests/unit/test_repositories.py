from __future__ import annotations

from datetime import datetime, timezone

from src.domain.entities.step import Step
from src.domain.value_objects.run_id import RunId
from src.infrastructure.repositories.in_memory_run_repository import InMemoryRunRepository
from src.infrastructure.repositories.in_memory_step_repository import InMemoryStepRepository
from src.infrastructure.repositories.redis_run_repository import RedisRunRepository
from src.infrastructure.repositories.redis_step_repository import RedisStepRepository
from src.infrastructure.transformers.run_transformer import RunTransformer
from src.infrastructure.transformers.step_transformer import StepTransformer


class FakeRedis:
    """Minimal in-memory Redis stub for repository tests."""

    def __init__(self) -> None:
        self.values: dict[str, str | bytes] = {}
        self.lists: dict[str, list[str]] = {}

    def set(self, key: str, value: str) -> None:
        self.values[key] = value

    def get(self, key: str):
        return self.values.get(key)

    def rpush(self, key: str, value: str) -> None:
        self.lists.setdefault(key, []).append(value)

    def lrange(self, key: str, start: int, end: int):
        items = self.lists.get(key, [])
        if end == -1:
            return items[start:]
        return items[start : end + 1]


def test_in_memory_run_repository_save_and_get(run_factory) -> None:
    repository = InMemoryRunRepository()
    run = run_factory()

    repository.save(run=run)
    loaded = repository.get(run_id=run.run_id)

    assert loaded is run


def test_in_memory_step_repository_add_and_list(run_factory) -> None:
    repository = InMemoryStepRepository()
    run = run_factory()
    step = Step(
        run_id=run.run_id,
        index=1,
        action={"action": "wait"},
        action_result={"success": True},
        evaluation={"progress": "ok", "goal_achieved": False, "risk": "low", "reason": "test"},
        pre_screenshot="/tmp/pre.png",
        post_screenshot="/tmp/post.png",
        created_at=datetime.now(tz=timezone.utc),
    )

    repository.add(step=step)
    loaded = repository.list_by_run_id(run_id=run.run_id)

    assert len(loaded) == 1
    assert loaded[0].index == 1


def test_redis_run_repository_save_and_get(run_factory) -> None:
    fake_redis = FakeRedis()
    repository = RedisRunRepository(redis_client=fake_redis, transformer=RunTransformer())
    run = run_factory()

    repository.save(run=run)
    loaded = repository.get(run_id=run.run_id)

    assert loaded is not None
    assert loaded.run_id.value == run.run_id.value


def test_redis_run_repository_handles_bytes_payload(run_factory) -> None:
    fake_redis = FakeRedis()
    repository = RedisRunRepository(redis_client=fake_redis, transformer=RunTransformer())
    run = run_factory()

    repository.save(run=run)
    key = f"run:{run.run_id.value}"
    existing = fake_redis.values[key]
    if isinstance(existing, str):
        fake_redis.values[key] = existing.encode("utf-8")

    loaded = repository.get(run_id=RunId(value=run.run_id.value))

    assert loaded is not None
    assert loaded.run_id.value == run.run_id.value


def test_redis_step_repository_add_and_list(run_factory) -> None:
    fake_redis = FakeRedis()
    repository = RedisStepRepository(redis_client=fake_redis, transformer=StepTransformer())
    run = run_factory()
    step = Step(
        run_id=run.run_id,
        index=2,
        action={"action": "done"},
        action_result={"success": True, "terminal_action": "done"},
        evaluation={"progress": "done", "goal_achieved": True, "risk": "low", "reason": "ok"},
        pre_screenshot="/tmp/pre.png",
        post_screenshot="/tmp/post.png",
        created_at=datetime.now(tz=timezone.utc),
    )

    repository.add(step=step)
    loaded = repository.list_by_run_id(run_id=run.run_id)

    assert len(loaded) == 1
    assert loaded[0].action["action"] == "done"
