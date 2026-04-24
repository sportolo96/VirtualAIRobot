from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field

from src.application.ports.planner import Planner


class PlannerDecision(BaseModel):
    """Structured planner decision."""

    action: str = Field(min_length=1)
    target: Optional[str] = None
    value: Optional[str] = None
    reason: str = Field(min_length=1)


class PlannerPipeline(Planner):
    """LangChain template and pipeline based planner."""

    def __init__(self, template_path: Path) -> None:
        template = template_path.read_text(encoding="utf-8")
        self._parser = PydanticOutputParser(pydantic_object=PlannerDecision)
        self._prompt = PromptTemplate.from_template(template=template)
        self._chain = self._prompt | RunnableLambda(self._model_stub) | self._parser

    def handle(
        self,
        goal: str,
        start_url: str,
        allowed_actions: list[str],
        step_index: int,
        pre_screenshot: str,
        last_evaluation: str | None,
    ) -> dict[str, Any]:
        payload = {
            "goal": goal,
            "start_url": start_url,
            "allowed_actions": ", ".join(allowed_actions),
            "step_index": step_index,
            "pre_screenshot": pre_screenshot,
            "last_evaluation": last_evaluation or "",
            "format_instructions": self._parser.get_format_instructions(),
        }
        decision = self._chain.invoke(payload)
        return decision.model_dump()

    def _model_stub(self, prompt_value: Any) -> str:
        prompt_text = (
            prompt_value.to_string() if hasattr(prompt_value, "to_string") else str(prompt_value)
        )
        lowered = prompt_text.lower()
        action = "wait"
        target: Optional[str] = None
        value: Optional[str] = None

        if "terminal action policy" in lowered and (
            "step index: 2" in lowered or "step index: 3" in lowered
        ):
            action = "done"
        elif "click" in lowered:
            action = "click"
            target = "primary"
        elif "type" in lowered:
            action = "type"
            target = "input"
            value = "demo"
        elif "scroll" in lowered:
            action = "scroll"
            target = "down"

        return json.dumps(
            {
                "action": action,
                "target": target,
                "value": value,
                "reason": "Template-driven planner baseline decision",
            }
        )
