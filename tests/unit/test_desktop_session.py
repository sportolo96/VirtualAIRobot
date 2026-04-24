from __future__ import annotations

from typing import Any

from PIL import Image, ImageDraw

from src.infrastructure.runtime.desktop_session import DesktopSession


def test_normalize_to_viewport_crops_when_capture_is_larger() -> None:
    session = DesktopSession(display=":99", browser_binary="chromium")
    session._viewport_width = 100
    session._viewport_height = 50
    image = Image.new("RGB", (200, 120), (1, 2, 3))

    normalized = session._normalize_to_viewport(image=image, image_cls=Image)

    assert normalized.size == (100, 50)


def test_normalize_to_viewport_pads_when_capture_is_smaller() -> None:
    session = DesktopSession(display=":99", browser_binary="chromium")
    session._viewport_width = 100
    session._viewport_height = 50
    image = Image.new("RGB", (40, 20), (10, 20, 30))

    normalized = session._normalize_to_viewport(image=image, image_cls=Image)

    assert normalized.size == (100, 50)
    assert normalized.getpixel((0, 0)) == (10, 20, 30)
    assert normalized.getpixel((99, 49)) == (0, 0, 0)


def test_draw_cursor_overlay_marks_cursor_location() -> None:
    session = DesktopSession(display=":99", browser_binary="chromium")
    image = Image.new("RGB", (120, 80), (255, 255, 255))

    session._draw_cursor_overlay(image=image, cursor=(60, 40), image_draw_cls=ImageDraw)

    assert image.getpixel((48, 40)) == (255, 64, 64)
    assert image.getpixel((60, 28)) == (255, 64, 64)


def test_read_cursor_position_parses_xdotool_output(monkeypatch) -> None:
    class _Completed:
        returncode = 0
        stdout = "X=321\nY=222\nSCREEN=0\nWINDOW=123\n"
        stderr = ""

    captured_env: list[dict[str, str]] = []

    def _run_stub(cmd: list[str], **kwargs: Any) -> _Completed:
        _ = cmd
        captured_env.append(kwargs["env"])
        return _Completed()

    monkeypatch.setattr("subprocess.run", _run_stub)

    session = DesktopSession(display=":44", browser_binary="chromium")
    position = session._read_cursor_position()

    assert position == (321, 222)
    assert captured_env[0]["DISPLAY"] == ":44"
