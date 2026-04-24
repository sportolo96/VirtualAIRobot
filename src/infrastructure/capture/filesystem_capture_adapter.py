from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from src.application.ports.capture_adapter import CaptureAdapter
from src.infrastructure.runtime.desktop_session import DesktopSession


class DesktopSessionProtocol(Protocol):
    """Desktop session contract."""

    def start(self, width: int, height: int, start_url: str) -> None:
        raise NotImplementedError

    def capture(self, output_path: Path) -> None:
        raise NotImplementedError

    def stop(self) -> None:
        raise NotImplementedError


class FilesystemCaptureAdapter(CaptureAdapter):
    """Filesystem-backed OS-level screenshot capture adapter."""

    def __init__(
        self,
        artifact_root: Path,
        session_factory: Callable[[], DesktopSessionProtocol] | None = None,
    ) -> None:
        self._artifact_root = artifact_root
        self._session_factory = session_factory or DesktopSession
        self._sessions: dict[str, DesktopSessionProtocol] = {}

    def prepare_run(self, run_id: str, runtime: dict[str, Any], start_url: str) -> None:
        viewport = runtime.get("viewport", {})
        width = int(viewport.get("width", 1080))
        height = int(viewport.get("height", 1920))

        if width <= 0 or height <= 0:
            raise RuntimeError("Runtime viewport width and height must be positive")

        session = self._session_factory()
        session.start(width=width, height=height, start_url=start_url)
        self._sessions[run_id] = session

    def finalize_run(self, run_id: str) -> None:
        session = self._sessions.pop(run_id, None)
        if session is not None:
            session.stop()

    def handle(self, run_id: str, step_index: int, phase: str) -> str:
        session = self._sessions.get(run_id)
        if session is None:
            raise RuntimeError("Desktop session is not initialized for run")

        run_dir = self._artifact_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        file_path = run_dir / f"step_{step_index:03d}_{phase}.png"
        session.capture(output_path=file_path)
        return file_path.as_posix()
