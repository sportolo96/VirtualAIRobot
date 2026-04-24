from __future__ import annotations

from src.application.ports.safety_guard import SafetyGuard


class DefaultSafetyGuard(SafetyGuard):
    """Default safety guard implementation."""

    def handle(self, allowed_actions: list[str], requested_action: str) -> None:
        if requested_action not in allowed_actions:
            raise ValueError(f"Action '{requested_action}' is not in allowed_actions")
