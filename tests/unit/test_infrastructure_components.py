from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.infrastructure.actions.local_action_executor import LocalActionExecutor
from src.infrastructure.capture.filesystem_capture_adapter import FilesystemCaptureAdapter
from src.infrastructure.queue import rq_queue_client
from src.infrastructure.safety.default_safety_guard import DefaultSafetyGuard


def test_local_action_executor_accepts_supported_actions() -> None:
    executor = LocalActionExecutor()
    result = executor.handle(
        action={"action": "done", "target": None, "value": None},
        start_url="https://example.com",
        runtime={"viewport": {"width": 1280, "height": 720}},
    )

    assert result["success"] is True
    assert result["action"] == "done"


def test_local_action_executor_rejects_unknown_action() -> None:
    executor = LocalActionExecutor()
    with pytest.raises(ValueError, match="Unsupported action"):
        executor.handle(
            action={"action": "unknown"},
            start_url="https://example.com",
            runtime={"viewport": {"width": 1280, "height": 720}},
        )


def test_local_action_executor_click_runs_xdotool(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    class CompletedStub:
        returncode = 0
        stdout = ""
        stderr = ""

    def _run_stub(cmd: list[str], **kwargs: Any) -> CompletedStub:
        _ = kwargs
        calls.append(cmd)
        return CompletedStub()

    monkeypatch.setattr("subprocess.run", _run_stub)

    executor = LocalActionExecutor()
    result = executor.handle(
        action={"action": "click", "x": 100, "y": 200, "button": 1},
        start_url="https://example.com",
        runtime={"viewport": {"width": 1280, "height": 720}},
    )

    assert result["success"] is True
    assert calls[0] == ["xdotool", "mousemove", "100", "200"]
    assert calls[1] == ["xdotool", "click", "1"]


def test_default_safety_guard_validates_allowed_actions() -> None:
    guard = DefaultSafetyGuard()
    guard.handle(allowed_actions=["wait", "done"], requested_action="done")

    with pytest.raises(ValueError, match="not in allowed_actions"):
        guard.handle(allowed_actions=["wait"], requested_action="click")


def test_filesystem_capture_adapter_captures_after_prepare(tmp_path: Path) -> None:
    captured: dict[str, object] = {}

    class SessionStub:
        def start(self, width: int, height: int, start_url: str) -> None:
            captured["width"] = width
            captured["height"] = height
            captured["start_url"] = start_url

        def capture(self, output_path: Path) -> None:
            output_path.write_bytes(b"\x89PNG\r\n\x1a\nstub")
            captured["output_path"] = output_path

        def stop(self) -> None:
            captured["stopped"] = True

    adapter = FilesystemCaptureAdapter(
        artifact_root=tmp_path,
        session_factory=lambda: SessionStub(),
    )

    adapter.prepare_run(
        run_id="run_1",
        runtime={"mode": "container_desktop", "viewport": {"width": 1280, "height": 720}},
        start_url="https://444.hu",
    )
    output = adapter.handle(run_id="run_1", step_index=1, phase="pre")
    adapter.finalize_run(run_id="run_1")

    output_path = Path(output)
    assert output_path.exists()
    assert output_path.read_bytes().startswith(b"\x89PNG")
    assert captured["width"] == 1280
    assert captured["height"] == 720
    assert captured["start_url"] == "https://444.hu"
    assert captured["output_path"] == output_path
    assert captured["stopped"] is True


def test_filesystem_capture_adapter_requires_prepared_session(tmp_path: Path) -> None:
    class UnusedSessionStub:
        def start(self, width: int, height: int, start_url: str) -> None:
            _ = (width, height, start_url)

        def capture(self, output_path: Path) -> None:
            output_path.write_bytes(b"")

        def stop(self) -> None:
            return

    adapter = FilesystemCaptureAdapter(
        artifact_root=tmp_path,
        session_factory=lambda: UnusedSessionStub(),
    )

    with pytest.raises(RuntimeError, match="Desktop session is not initialized"):
        adapter.handle(run_id="run_1", step_index=1, phase="pre")


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
