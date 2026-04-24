from __future__ import annotations

from pydantic import BaseModel, Field


class SuccessCriteriaSchema(BaseModel):
    """Success criteria schema."""

    type: str
    must_include: list[str] = Field(default_factory=list)
    must_not_include: list[str] = Field(default_factory=list)


class RuntimeSchema(BaseModel):
    """Runtime schema."""

    mode: str = "container_desktop"
    viewport: dict[str, int] = Field(default_factory=lambda: {"width": 1080, "height": 1920})


class LimitsSchema(BaseModel):
    """Limits schema."""

    max_steps: int = 40
    time_budget_sec: int = 300
    max_retries_per_step: int = 2


class LlmSchema(BaseModel):
    """LLM schema."""

    planner_model: str = "chatgpt-5.4"
    evaluator_model: str = "chatgpt-5.4"


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
    llm: LlmSchema = Field(default_factory=LlmSchema)
