from __future__ import annotations

from pathlib import Path

from src.application.ports.capture_adapter import CaptureAdapter


class FilesystemCaptureAdapter(CaptureAdapter):
    """Filesystem-backed screenshot capture adapter."""

    def __init__(self, artifact_root: Path) -> None:
        self._artifact_root = artifact_root

    def handle(self, run_id: str, step_index: int, phase: str) -> str:
        run_dir = self._artifact_root / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        file_path = run_dir / f"step_{step_index:03d}_{phase}.png"
        png_bytes = bytes(
            [
                137,
                80,
                78,
                71,
                13,
                10,
                26,
                10,
                0,
                0,
                0,
                13,
                73,
                72,
                68,
                82,
                0,
                0,
                0,
                1,
                0,
                0,
                0,
                1,
                8,
                2,
                0,
                0,
                0,
                144,
                119,
                83,
                222,
                0,
                0,
                0,
                12,
                73,
                68,
                65,
                84,
                8,
                29,
                99,
                248,
                15,
                4,
                0,
                9,
                251,
                3,
                253,
                160,
                73,
                117,
                197,
                0,
                0,
                0,
                0,
                73,
                69,
                78,
                68,
                174,
                66,
                96,
                130,
            ]
        )
        file_path.write_bytes(png_bytes)
        return file_path.as_posix()
