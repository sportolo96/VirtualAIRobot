from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field

from src.application.ports.evaluator import Evaluator


class StepEvaluation(BaseModel):
    """Structured evaluator response."""

    progress: str = Field(min_length=1)
    goal_achieved: bool
    risk: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class EvaluatorPipeline(Evaluator):
    """LangChain template and pipeline based evaluator."""

    def __init__(self, template_path: Path) -> None:
        template = template_path.read_text(encoding="utf-8")
        self._parser = PydanticOutputParser(pydantic_object=StepEvaluation)
        self._prompt = PromptTemplate.from_template(template=template)
        self._chain = self._prompt | RunnableLambda(self._model_stub) | self._parser

    def handle(
        self,
        goal: str,
        success_criteria: dict[str, Any],
        step_index: int,
        action: dict[str, Any],
        action_result: dict[str, Any],
        post_screenshot: str,
    ) -> dict[str, Any]:
        payload = {
            "goal": goal,
            "success_criteria": json.dumps(success_criteria),
            "step_index": step_index,
            "action": json.dumps(action),
            "action_result": json.dumps(action_result),
            "post_screenshot": post_screenshot,
            "format_instructions": self._parser.get_format_instructions(),
        }
        evaluation = self._chain.invoke(payload)
        return evaluation.model_dump()

    def _model_stub(self, prompt_value: Any) -> str:
        prompt_text = prompt_value.to_string() if hasattr(prompt_value, "to_string") else str(prompt_value)
        lowered = prompt_text.lower()
        goal_achieved = "step index: 2" in lowered or "step index: 3" in lowered
        risk = "low"
        reason = "Success criteria likely unmet"
        progress = "Goal not reached yet"

        if goal_achieved:
            reason = "Success criteria likely satisfied"
            progress = "Goal reached"

        return json.dumps(
            {
                "progress": progress,
                "goal_achieved": goal_achieved,
                "risk": risk,
                "reason": reason,
            }
        )
