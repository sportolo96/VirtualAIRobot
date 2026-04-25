from __future__ import annotations

from redis import Redis

from src.application.handlers.cancel_run_handler import CancelRunHandler
from src.application.handlers.create_run_handler import CreateRunHandler
from src.application.handlers.get_run_status_handler import GetRunStatusHandler
from src.application.handlers.list_run_steps_handler import ListRunStepsHandler
from src.application.handlers.process_run_handler import ProcessRunHandler
from src.domain.services.run_execution_service import RunExecutionService
from src.infrastructure.actions.local_action_executor import LocalActionExecutor
from src.infrastructure.ai.pipelines.evaluator_pipeline import EvaluatorPipeline
from src.infrastructure.ai.pipelines.planner_pipeline import PlannerPipeline
from src.infrastructure.ai.providers.openai_responses_client import OpenAIResponsesClient
from src.infrastructure.capture.filesystem_capture_adapter import FilesystemCaptureAdapter
from src.infrastructure.config.settings import Settings
from src.infrastructure.notifications.no_op_completion_notifier import NoOpCompletionNotifier
from src.infrastructure.notifications.webhook_completion_notifier import WebhookCompletionNotifier
from src.infrastructure.queue.rq_queue_client import RqQueueClient
from src.infrastructure.repositories.redis_run_repository import RedisRunRepository
from src.infrastructure.repositories.redis_step_repository import RedisStepRepository
from src.infrastructure.safety.default_safety_guard import DefaultSafetyGuard
from src.infrastructure.transformers.run_transformer import RunTransformer
from src.infrastructure.transformers.step_transformer import StepTransformer


class DependencyContainer:
    """Application dependency container."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._redis_client = Redis.from_url(settings.redis_url)
        self._run_repository = RedisRunRepository(
            redis_client=self._redis_client,
            transformer=RunTransformer(),
        )
        self._step_repository = RedisStepRepository(
            redis_client=self._redis_client,
            transformer=StepTransformer(),
        )
        self._queue_client = RqQueueClient(
            redis_client=self._redis_client,
            queue_name=settings.queue_name,
            job_path="src.interfaces.worker.jobs.process_run_job",
        )
        self._openai_client = OpenAIResponsesClient(api_key=settings.openai_api_key)
        self._planner = PlannerPipeline(
            template_path=settings.planner_template_path,
            openai_client=self._openai_client,
            default_model=settings.ai_model,
        )
        self._evaluator = EvaluatorPipeline(
            template_path=settings.evaluator_template_path,
            openai_client=self._openai_client,
            default_model=settings.ai_model,
        )
        self._capture_adapter = FilesystemCaptureAdapter(artifact_root=settings.artifact_root)
        self._action_executor = LocalActionExecutor()
        self._safety_guard = DefaultSafetyGuard()
        self._completion_notifier = (
            WebhookCompletionNotifier(
                timeout_sec=settings.webhook_timeout_sec,
                max_retries=settings.webhook_max_retries,
                retry_backoff_sec=settings.webhook_retry_backoff_sec,
                dead_letter_dir=settings.webhook_dead_letter_dir,
                signing_secret=settings.webhook_signing_secret,
            )
            if settings.webhook_enabled
            else NoOpCompletionNotifier()
        )

    def assert_ai_runtime_ready(self) -> None:
        """Ensure AI runtime prerequisites are configured before enqueueing runs."""

        provider = self._settings.ai_provider.strip().lower()
        if provider != "openai":
            raise RuntimeError(f"AI provider '{self._settings.ai_provider}' is not supported")

        api_key = self._settings.openai_api_key.strip()
        if not api_key or api_key == "your_real_key_here":
            raise RuntimeError(
                "AI runtime is not configured. Set OPENAI_API_KEY to start runs."
            )

        try:
            self._openai_client.health_check(model=self._settings.ai_model)
        except Exception as exc:
            raise RuntimeError(f"AI runtime connectivity check failed: {exc}") from exc

    def create_create_run_handler(self) -> CreateRunHandler:
        return CreateRunHandler(
            run_repository=self._run_repository,
            queue_client=self._queue_client,
        )

    def create_get_run_status_handler(self) -> GetRunStatusHandler:
        return GetRunStatusHandler(run_repository=self._run_repository)

    def create_list_run_steps_handler(self) -> ListRunStepsHandler:
        return ListRunStepsHandler(step_repository=self._step_repository)

    def create_cancel_run_handler(self) -> CancelRunHandler:
        return CancelRunHandler(run_repository=self._run_repository)

    def create_process_run_handler(self) -> ProcessRunHandler:
        execution_service = RunExecutionService(
            run_repository=self._run_repository,
            step_repository=self._step_repository,
            planner=self._planner,
            evaluator=self._evaluator,
            capture_adapter=self._capture_adapter,
            action_executor=self._action_executor,
            safety_guard=self._safety_guard,
            completion_notifier=self._completion_notifier,
        )
        return ProcessRunHandler(run_execution_service=execution_service)

    @property
    def redis_client(self) -> Redis:
        return self._redis_client
