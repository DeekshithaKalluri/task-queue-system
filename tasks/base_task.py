import logging
import random
from celery import Task
from worker import celery_app

logger = logging.getLogger(__name__)


class BaseTaskWithRetry(Task):
    abstract = True
    max_retries = 5
    default_retry_delay = 2

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error({
            "event": "task_failed",
            "task": self.name,
            "task_id": task_id,
            "args": str(args),
            "error": str(exc)
        })
        celery_app.send_task(
            'tasks.dead_letter_handler',
            args=[self.name, task_id, str(args), str(exc)],
            queue='low'
        )

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        logger.warning({
            "event": "task_retry",
            "task": self.name,
            "task_id": task_id,
            "attempt": self.request.retries,
            "max": self.max_retries,
            "reason": str(exc)
        })

    def on_success(self, retval, task_id, args, kwargs):
        logger.info({
            "event": "task_success",
            "task": self.name,
            "task_id": task_id,
            "result": str(retval)
        })

    def get_backoff_with_jitter(self, base=2):
        """Exponential backoff + jitter to prevent thundering herd."""
        exp = base ** self.request.retries
        jitter = random.uniform(0, exp * 0.3)  # up to 30% jitter
        return round(exp + jitter, 2)