from __future__ import annotations

from redis import Redis
from rq import Connection, Worker

from src.infrastructure.config.settings import load_settings


if __name__ == "__main__":
    settings = load_settings()
    redis_client = Redis.from_url(settings.redis_url)

    with Connection(redis_client):
        worker = Worker([settings.queue_name])
        worker.work()
