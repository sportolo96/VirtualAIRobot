from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, Response, jsonify, request
from pydantic import ValidationError

from src.application.commands.cancel_run_command import CancelRunCommand
from src.application.commands.create_run_command import CreateRunCommand
from src.application.presenters.run_presenter import RunPresenter
from src.application.presenters.step_presenter import StepPresenter
from src.application.queries.get_run_status_query import GetRunStatusQuery
from src.application.queries.list_run_steps_query import ListRunStepsQuery
from src.bootstrap.dependency_container import DependencyContainer
from src.interfaces.http.schemas import CreateRunRequestSchema


def create_runs_blueprint(container: DependencyContainer) -> Blueprint:
    """Create runs blueprint."""

    blueprint = Blueprint(name="runs", import_name=__name__)
    create_run_handler = container.create_create_run_handler()
    get_run_status_handler = container.create_get_run_status_handler()
    list_run_steps_handler = container.create_list_run_steps_handler()
    cancel_run_handler = container.create_cancel_run_handler()
    run_presenter = RunPresenter()
    step_presenter = StepPresenter()

    @blueprint.post("/v1/runs")
    def create_run() -> tuple[Response, int]:
        payload = request.get_json(silent=True) or {}
        try:
            data = CreateRunRequestSchema.model_validate(payload)
        except ValidationError as exc:
            return jsonify({"errors": exc.errors()}), 422

        command = CreateRunCommand(
            goal=data.goal,
            start_url=data.start_url,
            success_criteria=data.success_criteria.model_dump(),
            runtime=data.runtime.model_dump(),
            limits=data.limits.model_dump(),
            allowed_actions=data.allowed_actions,
            llm=data.llm.model_dump(),
        )
        run = create_run_handler.handle(command=command)
        response = {
            "run_id": run.run_id.value,
            "status": run.status.value,
        }
        return jsonify(response), 202

    @blueprint.get("/v1/runs/<run_id>")
    def get_run(run_id: str) -> tuple[Response, int]:
        run = get_run_status_handler.handle(query=GetRunStatusQuery(run_id=run_id))
        if run is None:
            return jsonify({"error": "Run not found"}), 404

        result = run_presenter.handle(run=run, now=datetime.now(tz=timezone.utc))
        return jsonify(result), 200

    @blueprint.get("/v1/runs/<run_id>/steps")
    def list_steps(run_id: str) -> tuple[Response, int]:
        steps = list_run_steps_handler.handle(query=ListRunStepsQuery(run_id=run_id))
        result = {
            "run_id": run_id,
            "steps": step_presenter.handle_many(steps=steps),
        }
        return jsonify(result), 200

    @blueprint.post("/v1/runs/<run_id>/cancel")
    def cancel_run(run_id: str) -> tuple[Response, int]:
        run = cancel_run_handler.handle(command=CancelRunCommand(run_id=run_id))
        if run is None:
            return jsonify({"error": "Run not found"}), 404
        return jsonify({"run_id": run_id, "status": "cancel_requested"}), 202

    return blueprint
