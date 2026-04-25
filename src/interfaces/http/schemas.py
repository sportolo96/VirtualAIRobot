from __future__ import annotations

import os
from typing import Optional

from pydantic import BaseModel, Field


class SuccessCriteriaSchema(BaseModel):
    """Success criteria schema."""

    type: str
    must_include: list[str] = Field(default_factory=list)
    must_not_include: list[str] = Field(default_factory=list)


class RuntimeSchema(BaseModel):
    """Runtime schema."""

    mode: str = "container_desktop"
    viewport: dict[str, int] = Field(
        default_factory=lambda: {
            "width": int(os.getenv("DEFAULT_VIEWPORT_WIDTH", "1080")),
            "height": int(os.getenv("DEFAULT_VIEWPORT_HEIGHT", "1920")),
        }
    )


class LimitsSchema(BaseModel):
    """Limits schema."""

    max_steps: int = 40
    time_budget_sec: int = 300
    max_retries_per_step: int = 2


class CallbacksSchema(BaseModel):
    """Callbacks schema."""

    completion_url: Optional[str] = None
    headers: dict[str, str] = Field(default_factory=dict)


class CreateRunRequestSchema(BaseModel):
    """Create run request schema."""

    goal: str
    start_url: str
    success_criteria: SuccessCriteriaSchema
    runtime: RuntimeSchema
    limits: LimitsSchema
    allowed_actions: list[str] = Field(
        default_factory=lambda: ["move", "click", "scroll", "type", "key", "wait", "done", "failed"]
    )
    callbacks: CallbacksSchema = Field(default_factory=CallbacksSchema)
