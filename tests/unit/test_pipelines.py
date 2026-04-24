from __future__ import annotations

import json
from pathlib import Path

from src.infrastructure.ai.pipelines.evaluator_pipeline import EvaluatorPipeline
from src.infrastructure.ai.pipelines.planner_pipeline import PlannerPipeline
from src.infrastructure.ai.providers.openai_responses_client import OpenAIResponsesClient


def _template_path(name: str) -> Path:
    return (
        Path(__file__).resolve().parents[2] / "src" / "infrastructure" / "ai" / "templates" / name
    )


def _unused_client() -> OpenAIResponsesClient:
    return OpenAIResponsesClient(api_key="test-key")


def test_planner_pipeline_returns_done_on_step_two() -> None:
    def _model_invoke(prompt: str, model: str) -> str:
        _ = model
        action = "done" if "Step index: 2" in prompt else "wait"
        return json.dumps(
            {
                "action": action,
                "target": None,
                "value": None,
                "x": None,
                "y": None,
                "button": None,
                "seconds": None,
                "reason": "stub",
            }
        )

    planner = PlannerPipeline(
        template_path=_template_path("planner_prompt.txt"),
        openai_client=_unused_client(),
        default_model="gpt-5.4",
        model_invoke=_model_invoke,
    )

    decision = planner.handle(
        goal="Open profile",
        start_url="https://example.com",
        allowed_actions=["wait", "done", "failed"],
        step_index=2,
        pre_screenshot="/tmp/pre.png",
        last_evaluation="",
        model="gpt-5.4",
    )

    assert decision["action"] == "done"


def test_planner_pipeline_returns_click_for_click_like_prompt() -> None:
    def _model_invoke(prompt: str, model: str) -> str:
        _ = model
        action = "click" if "click" in prompt.lower() else "wait"
        return json.dumps(
            {
                "action": action,
                "target": "primary" if action == "click" else None,
                "value": None,
                "x": 640 if action == "click" else None,
                "y": 360 if action == "click" else None,
                "button": 1 if action == "click" else None,
                "seconds": None,
                "reason": "stub",
            }
        )

    planner = PlannerPipeline(
        template_path=_template_path("planner_prompt.txt"),
        openai_client=_unused_client(),
        default_model="gpt-5.4",
        model_invoke=_model_invoke,
    )

    decision = planner.handle(
        goal="click the primary button",
        start_url="https://example.com",
        allowed_actions=["click", "wait", "done", "failed"],
        step_index=1,
        pre_screenshot="/tmp/pre.png",
        last_evaluation="",
        model="gpt-5.4",
    )

    assert decision["action"] == "click"
    assert decision["target"] == "primary"


def test_evaluator_pipeline_maps_done_and_failed_actions() -> None:
    def _model_invoke(prompt: str, model: str) -> str:
        _ = model
        lowered = prompt.lower()
        if '"action": "failed"' in lowered:
            progress = "Run failed by AI decision"
            goal_achieved = False
        elif '"action": "done"' in lowered:
            progress = "Run completed by AI decision"
            goal_achieved = True
        else:
            progress = "Goal not reached yet"
            goal_achieved = False
        return json.dumps(
            {
                "progress": progress,
                "goal_achieved": goal_achieved,
                "risk": "high" if not goal_achieved else "low",
                "reason": "stub",
            }
        )

    evaluator = EvaluatorPipeline(
        template_path=_template_path("evaluator_prompt.txt"),
        openai_client=_unused_client(),
        default_model="gpt-5.4",
        model_invoke=_model_invoke,
    )

    done_eval = evaluator.handle(
        goal="Open profile",
        success_criteria={"type": "text_or_dom"},
        step_index=2,
        action={"action": "done"},
        action_result={"success": True},
        post_screenshot="/tmp/post.png",
        model="gpt-5.4",
    )
    failed_eval = evaluator.handle(
        goal="Open profile",
        success_criteria={"type": "text_or_dom"},
        step_index=2,
        action={"action": "failed"},
        action_result={"success": False},
        post_screenshot="/tmp/post.png",
        model="gpt-5.4",
    )

    assert done_eval["goal_achieved"] is True
    assert done_eval["progress"] == "Run completed by AI decision"
    assert failed_eval["goal_achieved"] is False
    assert failed_eval["progress"] == "Run failed by AI decision"
