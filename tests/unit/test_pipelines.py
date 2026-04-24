from __future__ import annotations

from src.infrastructure.ai.pipelines.evaluator_pipeline import EvaluatorPipeline
from src.infrastructure.ai.pipelines.planner_pipeline import PlannerPipeline


def test_planner_pipeline_returns_done_on_step_two() -> None:
    planner = PlannerPipeline(
        template_path=(
            __import__("pathlib").Path(__file__).resolve().parents[2]
            / "src"
            / "infrastructure"
            / "ai"
            / "templates"
            / "planner_prompt.txt"
        )
    )

    decision = planner.handle(
        goal="Open profile",
        start_url="https://example.com",
        allowed_actions=["wait", "done", "failed"],
        step_index=2,
        pre_screenshot="/tmp/pre.png",
        last_evaluation="",
    )

    assert decision["action"] == "done"


def test_planner_pipeline_returns_click_for_click_like_prompt() -> None:
    planner = PlannerPipeline(
        template_path=(
            __import__("pathlib").Path(__file__).resolve().parents[2]
            / "src"
            / "infrastructure"
            / "ai"
            / "templates"
            / "planner_prompt.txt"
        )
    )

    decision = planner.handle(
        goal="click the primary button",
        start_url="https://example.com",
        allowed_actions=["click", "wait", "done", "failed"],
        step_index=1,
        pre_screenshot="/tmp/pre.png",
        last_evaluation="",
    )

    assert decision["action"] == "click"
    assert decision["target"] == "primary"


def test_evaluator_pipeline_maps_done_and_failed_actions() -> None:
    template_path = (
        __import__("pathlib").Path(__file__).resolve().parents[2]
        / "src"
        / "infrastructure"
        / "ai"
        / "templates"
        / "evaluator_prompt.txt"
    )
    evaluator = EvaluatorPipeline(template_path=template_path)

    done_eval = evaluator.handle(
        goal="Open profile",
        success_criteria={"type": "text_or_dom"},
        step_index=2,
        action={"action": "done"},
        action_result={"success": True},
        post_screenshot="/tmp/post.png",
    )
    failed_eval = evaluator.handle(
        goal="Open profile",
        success_criteria={"type": "text_or_dom"},
        step_index=2,
        action={"action": "failed"},
        action_result={"success": False},
        post_screenshot="/tmp/post.png",
    )

    assert done_eval["goal_achieved"] is True
    assert done_eval["progress"] == "Run completed by AI decision"
    assert failed_eval["goal_achieved"] is False
    assert failed_eval["progress"] == "Run failed by AI decision"
