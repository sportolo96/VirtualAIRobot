from __future__ import annotations

from typing import Any

from src.application.ports.action_executor import ActionExecutor


class LocalActionExecutor(ActionExecutor):
    """Local deterministic action executor baseline."""

    def handle(self, action: dict[str, Any], start_url: str) -> dict[str, Any]:
        action_name = str(action.get("action", ""))
        target = action.get("target")
        value = action.get("value")

        if action_name not in {"move", "click", "scroll", "type", "key", "wait", "done", "failed"}:
            raise ValueError(f"Unsupported action: {action_name}")

        return {
            "success": True,
            "action": action_name,
            "target": target,
            "value": value,
            "url": start_url,
        }
