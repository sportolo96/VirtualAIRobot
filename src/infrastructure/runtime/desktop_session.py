from __future__ import annotations

import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


class DesktopSession:
    """OS-level desktop session backed by Xvfb and a real browser process."""

    def __init__(self, display: str | None = None, browser_binary: str | None = None) -> None:
        self._display: str = display if display is not None else (os.getenv("DISPLAY") or ":99")
        self._browser_binary: str = (
            browser_binary if browser_binary is not None else (os.getenv("BROWSER_BINARY") or "")
        )
        self._xvfb_process: subprocess.Popen[bytes] | None = None
        self._browser_process: subprocess.Popen[bytes] | None = None
        self._viewport_width = 0
        self._viewport_height = 0

    def start(self, width: int, height: int, start_url: str) -> None:
        self._viewport_width = int(width)
        self._viewport_height = int(height)
        self._start_xvfb(width=width, height=height)
        self._start_browser(width=width, height=height, start_url=start_url)
        time.sleep(0.8)

    def capture(self, output_path: Path) -> None:
        import mss
        from PIL import Image, ImageDraw

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with mss.mss(display=self._display) as capture_session:
            monitor = (
                capture_session.monitors[1]
                if len(capture_session.monitors) > 1
                else capture_session.monitors[0]
            )
            screenshot = capture_session.grab(monitor)
            image = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
            image = self._normalize_to_viewport(image=image, image_cls=Image)
            cursor = self._read_cursor_position()
            if cursor is not None:
                self._draw_cursor_overlay(image=image, cursor=cursor, image_draw_cls=ImageDraw)
            image.save(output_path, format="PNG")

    def stop(self) -> None:
        self._terminate(self._browser_process)
        self._terminate(self._xvfb_process)
        self._browser_process = None
        self._xvfb_process = None

    def _start_xvfb(self, width: int, height: int) -> None:
        env = os.environ.copy()
        env["DISPLAY"] = self._display
        self._xvfb_process = subprocess.Popen(
            [
                "Xvfb",
                self._display,
                "-screen",
                "0",
                f"{width}x{height}x24",
                "-ac",
                "-nolisten",
                "tcp",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        time.sleep(0.4)
        if self._xvfb_process.poll() is not None:
            raise RuntimeError("Unable to start Xvfb desktop session")

    def _start_browser(self, width: int, height: int, start_url: str) -> None:
        browser_binary = self._resolve_browser_binary()
        browser_name = Path(browser_binary).name.lower()
        browser_args: list[str]

        if "chrom" in browser_name:
            browser_args = [
                browser_binary,
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--new-window",
                f"--window-size={width},{height}",
                start_url,
            ]
        elif "firefox" in browser_name:
            browser_args = [browser_binary, "--new-window", start_url]
        else:
            browser_args = [browser_binary, start_url]

        env = os.environ.copy()
        env["DISPLAY"] = self._display
        self._browser_process = subprocess.Popen(
            browser_args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        time.sleep(0.4)
        if self._browser_process.poll() is not None:
            raise RuntimeError(f"Unable to start browser process: {browser_binary}")

    def _resolve_browser_binary(self) -> str:
        if self._browser_binary:
            resolved = shutil.which(self._browser_binary)
            if resolved is not None:
                return resolved
            if Path(self._browser_binary).exists():
                return self._browser_binary
            raise RuntimeError(f"Configured browser binary is not available: {self._browser_binary}")

        for candidate in ("chromium", "chromium-browser", "google-chrome", "firefox"):
            resolved = shutil.which(candidate)
            if resolved is not None:
                return resolved

        raise RuntimeError("No supported browser binary found for OS runtime screenshots")

    def _normalize_to_viewport(self, image: Any, image_cls: Any) -> Any:
        expected_width = self._viewport_width if self._viewport_width > 0 else int(image.width)
        expected_height = self._viewport_height if self._viewport_height > 0 else int(image.height)
        if int(image.width) == expected_width and int(image.height) == expected_height:
            return image
        if int(image.width) >= expected_width and int(image.height) >= expected_height:
            return image.crop((0, 0, expected_width, expected_height))
        canvas = image_cls.new("RGB", (expected_width, expected_height), (0, 0, 0))
        canvas.paste(image, (0, 0))
        return canvas

    def _read_cursor_position(self) -> tuple[int, int] | None:
        env = os.environ.copy()
        env["DISPLAY"] = self._display
        completed = subprocess.run(
            ["xdotool", "getmouselocation", "--shell"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        if completed.returncode != 0:
            return None
        x_match = re.search(r"^X=(\d+)$", completed.stdout, flags=re.MULTILINE)
        y_match = re.search(r"^Y=(\d+)$", completed.stdout, flags=re.MULTILINE)
        if x_match is None or y_match is None:
            return None
        return int(x_match.group(1)), int(y_match.group(1))

    def _draw_cursor_overlay(self, image: Any, cursor: tuple[int, int], image_draw_cls: Any) -> None:
        width = int(image.width)
        height = int(image.height)
        x = max(0, min(int(cursor[0]), max(0, width - 1)))
        y = max(0, min(int(cursor[1]), max(0, height - 1)))
        draw = image_draw_cls.Draw(image)
        radius = 8
        draw.ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            outline=(255, 64, 64),
            width=2,
        )
        draw.line([(x - 12, y), (x + 12, y)], fill=(255, 64, 64), width=1)
        draw.line([(x, y - 12), (x, y + 12)], fill=(255, 64, 64), width=1)

    def _terminate(self, process: subprocess.Popen[bytes] | None) -> None:
        if process is None:
            return
        if process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
