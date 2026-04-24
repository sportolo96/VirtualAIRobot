from __future__ import annotations

import re
import subprocess
import time
from typing import Any

from src.application.ports.action_executor import ActionExecutor


class LocalActionExecutor(ActionExecutor):
    """OS-level action executor using xdotool."""

    def handle(
        self,
        action: dict[str, Any],
        start_url: str,
        runtime: dict[str, Any],
    ) -> dict[str, Any]:
        action_name = str(action.get("action", ""))
        target = action.get("target")
        value = action.get("value")

        if action_name not in {"move", "click", "scroll", "type", "key", "wait", "done", "failed"}:
            raise ValueError(f"Unsupported action: {action_name}")

        if action_name == "move":
            x, y = self._resolve_point(action=action, runtime=runtime)
            self._run_xdotool(["mousemove", str(x), str(y)])
        elif action_name == "click":
            x, y = self._resolve_point(action=action, runtime=runtime)
            button = int(action.get("button", 1))
            clicks = max(1, int(action.get("clicks", 1)))
            self._run_xdotool(["mousemove", str(x), str(y)])
            for _ in range(clicks):
                self._run_xdotool(["click", str(button)])
        elif action_name == "scroll":
            amount = max(1, int(action.get("amount", 1)))
            direction = str(action.get("direction", target or value or "down")).lower()
            scroll_button = "4" if direction == "up" else "5"
            for _ in range(amount):
                self._run_xdotool(["click", scroll_button])
        elif action_name == "type":
            text = str(value or "")
            if not text:
                raise ValueError("Action 'type' requires value text")
            self._run_xdotool(["type", "--delay", "1", text])
        elif action_name == "key":
            key_name = str(value or target or "")
            if not key_name:
                raise ValueError("Action 'key' requires value or target key")
            self._run_xdotool(["key", key_name])
        elif action_name == "wait":
            seconds = float(action.get("seconds", 1))
            if seconds < 0:
                raise ValueError("Action 'wait' seconds cannot be negative")
            time.sleep(seconds)

        return {
            "success": True,
            "action": action_name,
            "target": target,
            "value": value,
            "url": start_url,
        }

    def _resolve_point(self, action: dict[str, Any], runtime: dict[str, Any]) -> tuple[int, int]:
        x = action.get("x")
        y = action.get("y")
        if isinstance(x, (int, float)) and isinstance(y, (int, float)):
            return int(x), int(y)

        target = str(action.get("target", ""))
        match = re.fullmatch(r"\s*(\d+)\s*,\s*(\d+)\s*", target)
        if match:
            return int(match.group(1)), int(match.group(2))

        viewport = runtime.get("viewport", {})
        width = max(1, int(viewport.get("width", 1080)))
        height = max(1, int(viewport.get("height", 1920)))
        return width // 2, height // 2

    def _run_xdotool(self, args: list[str]) -> None:
        completed = subprocess.run(
            ["xdotool", *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"xdotool failed: {completed.stderr.strip()}")
