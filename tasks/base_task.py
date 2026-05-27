import logging
from celery import Task
from worker import celery_app

logger = logging.getLogger(__name__)


class BaseTaskWithRetry(Task):
    """
    Custom base class for all tasks.
    Provides:
      - Exponential backoff retry (2^retry_number seconds)
      - Structured logging on failure
      - Dead-letter routing after max retries exhausted
    """
    abstract = True          # Celery won't register this as a real task
    max_retries = 5
    default_retry_delay = 2  # base seconds (will be overridden by backoff)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when the task has exceeded max_retries and truly failed."""
        logger.error(
            f"[DEAD LETTER] Task {self.name} | ID: {task_id} | "
            f"Args: {args} | Error: {exc}"
        )
        # Send to dead-letter queue for inspection
        celery_app.send_task(
            'tasks.dead_letter_handler',
            args=[self.name, task_id, str(args), str(exc)],
            queue='low'
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called every time a task is about to be retried."""
        logger.warning(
            f"[RETRY] Task {self.name} | ID: {task_id} | "
            f"Attempt {self.request.retries}/{self.max_retries} | "
            f"Reason: {exc}"
        )

    def on_success(self, retval, task_id, args, kwargs):
        """Called when task completes successfully."""
        logger.info(
            f"[SUCCESS] Task {self.name} | ID: {task_id} | Result: {retval}"
        )