from __future__ import annotations

from pathlib import Path

import pytest

from src.infrastructure.actions.local_action_executor import LocalActionExecutor
from src.infrastructure.capture.filesystem_capture_adapter import FilesystemCaptureAdapter
from src.infrastructure.queue import rq_queue_client
from src.infrastructure.safety.default_safety_guard import DefaultSafetyGuard


def test_local_action_executor_accepts_supported_actions() -> None:
    executor = LocalActionExecutor()
    result = executor.handle(
        action={"action": "done", "target": None, "value": None}, start_url="https://example.com"
    )

    assert result["success"] is True
    assert result["action"] == "done"


def test_local_action_executor_rejects_unknown_action() -> None:
    executor = LocalActionExecutor()
    with pytest.raises(ValueError, match="Unsupported action"):
        executor.handle(action={"action": "unknown"}, start_url="https://example.com")


def test_default_safety_guard_validates_allowed_actions() -> None:
    guard = DefaultSafetyGuard()
    guard.handle(allowed_actions=["wait", "done"], requested_action="done")

    with pytest.raises(ValueError, match="not in allowed_actions"):
        guard.handle(allowed_actions=["wait"], requested_action="click")


def test_filesystem_capture_adapter_writes_png(tmp_path: Path) -> None:
    adapter = FilesystemCaptureAdapter(artifact_root=tmp_path)

    output = adapter.handle(run_id="run_1", step_index=1, phase="pre")

    output_path = Path(output)
    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"\x89PNG")


def test_rq_queue_client_enqueues_job(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class QueueStub:
        def __init__(self, name: str, connection: object) -> None:
            captured["name"] = name
            captured["connection"] = connection

        def enqueue(self, job_path: str, run_id: str) -> None:
            captured["job_path"] = job_path
            captured["run_id"] = run_id

    monkeypatch.setattr(rq_queue_client, "Queue", QueueStub)

    connection = object()
    client = rq_queue_client.RqQueueClient(
        redis_client=connection, queue_name="runs", job_path="jobs.process"
    )
    client.enqueue_process_run(run_id="run_123")

    assert captured == {
        "name": "runs",
        "connection": connection,
        "job_path": "jobs.process",
        "run_id": "run_123",
    }
