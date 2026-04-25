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
    api_auth_enabled: bool
    api_auth_key: str
    webhook_enabled: bool
    webhook_timeout_sec: int
    webhook_max_retries: int
    webhook_retry_backoff_sec: float
    webhook_signing_secret: str
    webhook_dead_letter_dir: Path
    artifact_root: Path
    planner_template_path: Path
    evaluator_template_path: Path
    flask_host: str
    flask_port: int


def load_settings() -> Settings:
    """Load settings from environment."""

    project_root = Path(__file__).resolve().parents[3]

    auth_enabled_raw = os.getenv("API_AUTH_ENABLED", "false").strip().lower()
    api_auth_enabled = auth_enabled_raw in {"1", "true", "yes", "on"}
    webhook_enabled_raw = os.getenv("WEBHOOK_ENABLED", "false").strip().lower()
    webhook_enabled = webhook_enabled_raw in {"1", "true", "yes", "on"}
    return Settings(
        redis_url=os.getenv("REDIS_URL", "redis://redis:6379/0"),
        queue_name=os.getenv("QUEUE_NAME", "runs"),
        ai_provider=os.getenv("AI_PROVIDER", "openai"),
        ai_model=os.getenv("AI_MODEL", "gpt-5.4"),
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        api_auth_enabled=api_auth_enabled,
        api_auth_key=os.getenv("API_AUTH_KEY", ""),
        webhook_enabled=webhook_enabled,
        webhook_timeout_sec=int(os.getenv("WEBHOOK_TIMEOUT_SEC", "10")),
        webhook_max_retries=int(os.getenv("WEBHOOK_MAX_RETRIES", "3")),
        webhook_retry_backoff_sec=float(os.getenv("WEBHOOK_RETRY_BACKOFF_SEC", "1.0")),
        webhook_signing_secret=os.getenv("WEBHOOK_SIGNING_SECRET", ""),
        webhook_dead_letter_dir=Path(
            os.getenv("WEBHOOK_DEAD_LETTER_DIR", str(project_root / "artifacts" / "dead_letters"))
        ),
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
