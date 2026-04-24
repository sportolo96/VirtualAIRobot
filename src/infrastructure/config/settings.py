from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Application settings."""

    redis_url: str
    queue_name: str
    ai_provider: str
    ai_model: str
    openai_api_key: str
    artifact_root: Path
    planner_template_path: Path
    evaluator_template_path: Path
    flask_host: str
    flask_port: int


def load_settings() -> Settings:
    """Load settings from environment."""

    project_root = Path(__file__).resolve().parents[3]
    return Settings(
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
        queue_name=os.getenv("QUEUE_NAME", "runs"),
        ai_provider=os.getenv("AI_PROVIDER", "openai"),
        ai_model=os.getenv("AI_MODEL", "gpt-5.4"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        artifact_root=Path(os.getenv("ARTIFACT_ROOT", str(project_root / "artifacts"))),
        planner_template_path=Path(
            os.getenv(
                "PLANNER_TEMPLATE_PATH",
                str(
                    project_root
                    / "src"
                    / "infrastructure"
                    / "ai"
                    / "templates"
                    / "planner_prompt.txt"
                ),
            )
        ),
        evaluator_template_path=Path(
            os.getenv(
                "EVALUATOR_TEMPLATE_PATH",
                str(
                    project_root
                    / "src"
                    / "infrastructure"
                    / "ai"
                    / "templates"
                    / "evaluator_prompt.txt"
                ),
            )
        ),
        flask_host=os.getenv("FLASK_HOST", "0.0.0.0"),
        flask_port=int(os.getenv("FLASK_PORT", "8000")),
    )
