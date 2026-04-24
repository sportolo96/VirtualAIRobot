from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field

from src.application.ports.planner import Planner
from src.infrastructure.ai.providers.openai_responses_client import OpenAIResponsesClient


class PlannerDecision(BaseModel):
    """Structured planner decision."""

    action: str = Field(min_length=1)
    target: Optional[str] = None
    value: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    button: Optional[int] = None
    seconds: Optional[float] = None
    reason: str = Field(min_length=1)


class PlannerPipeline(Planner):
    """LangChain template and pipeline based planner."""

    def __init__(
        self,
        template_path: Path,
        openai_client: OpenAIResponsesClient,
        default_model: str,
        model_invoke: Callable[[str, str], str] | None = None,
    ) -> None:
        template = template_path.read_text(encoding="utf-8")
        self._openai_client = openai_client
        self._default_model = default_model
        self._model_invoke = model_invoke
        self._parser = PydanticOutputParser(pydantic_object=PlannerDecision)
        self._prompt = PromptTemplate.from_template(template=template)

    def handle(
        self,
        goal: str,
        start_url: str,
        allowed_actions: list[str],
        step_index: int,
        pre_screenshot: str,
        last_evaluation: str | None,
        model: str | None = None,
    ) -> dict[str, Any]:
        model_name = (model or self._default_model).strip()
        chain = (
            self._prompt
            | RunnableLambda(
                lambda prompt_value: self._invoke_model(
                    prompt_value=prompt_value,
                    model_name=model_name,
                    screenshot_path=pre_screenshot,
                )
            )
            | self._parser
        )
        payload = {
            "goal": goal,
            "start_url": start_url,
            "allowed_actions": ", ".join(allowed_actions),
            "step_index": step_index,
            "pre_screenshot": pre_screenshot,
            "last_evaluation": last_evaluation or "",
            "format_instructions": self._parser.get_format_instructions(),
        }
        decision = chain.invoke(payload)
        return decision.model_dump()

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
