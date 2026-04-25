from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field

from src.application.ports.evaluator import Evaluator
from src.infrastructure.ai.providers.responses_client import ResponsesClient


class StepEvaluation(BaseModel):
    """Structured evaluator response."""

    progress: str = Field(min_length=1)
    goal_achieved: bool
    risk: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class EvaluatorPipeline(Evaluator):
    """LangChain template and pipeline based evaluator."""

    def __init__(
        self,
        template_path: Path,
        openai_client: ResponsesClient,
        default_model: str,
        model_invoke: Callable[[str, str], str] | None = None,
    ) -> None:
        template = template_path.read_text(encoding="utf-8")
        self._openai_client = openai_client
        self._default_model = default_model
        self._model_invoke = model_invoke
        self._parser = PydanticOutputParser(pydantic_object=StepEvaluation)
        self._prompt = PromptTemplate.from_template(template=template)

    def handle(
        self,
        goal: str,
        success_criteria: dict[str, Any],
        step_index: int,
        action: dict[str, Any],
        action_result: dict[str, Any],
        post_screenshot: str,
        model: str | None = None,
    ) -> dict[str, Any]:
        model_name = (model or self._default_model).strip()
        chain = (
            self._prompt
            | RunnableLambda(
                lambda prompt_value: self._invoke_model(
                    prompt_value=prompt_value,
                    model_name=model_name,
                    screenshot_path=post_screenshot,
                )
            )
            | self._parser
        )
        payload = {
            "goal": goal,
            "success_criteria": json.dumps(success_criteria),
            "step_index": step_index,
            "action": json.dumps(action),
            "action_result": json.dumps(action_result),
            "post_screenshot": post_screenshot,
            "format_instructions": self._parser.get_format_instructions(),
        }
        evaluation = chain.invoke(payload)
        return evaluation.model_dump()

    def _invoke_model(self, prompt_value: Any, model_name: str, screenshot_path: str) -> str:
        prompt_text = (
            prompt_value.to_string() if hasattr(prompt_value, "to_string") else str(prompt_value)
        )
        if self._model_invoke is not None:
            return self._model_invoke(prompt_text, model_name)
        return self._openai_client.complete_text_with_image(
            model=model_name,
            prompt=prompt_text,
            image_path=screenshot_path,
        )
