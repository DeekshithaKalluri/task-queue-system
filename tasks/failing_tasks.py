import logging
from worker import celery_app
from tasks.base_task import BaseTaskWithRetry

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    base=BaseTaskWithRetry,
    name='tasks.always_fails',
    queue='default',
    max_retries=3
)
def always_fails(self, job_id: str) -> None:
    """
    A task that always fails — used to demonstrate:
    1. Exponential backoff retry (3 attempts)
    2. on_failure() firing after exhausting retries
    3. Dead-letter queue receiving the failed job
    """
    logger.info(f"Attempting job {job_id} (will fail)...")
    countdown = self.get_backoff_with_jitter()
    raise self.retry(
        exc=RuntimeError(f"Intentional failure for job {job_id}"),
        countdown=countdown
    )


@celery_app.task(
    bind=True,
    base=BaseTaskWithRetry,
    name='tasks.dead_letter_handler',
    queue='low'
)
def dead_letter_handler(self, task_name: str, task_id: str,
                        args: str, error: str) -> dict:
    """
    Receives tasks that have exhausted all retries.
    In production: write to DB, alert on-call, or trigger a compensating action.
    Here: logs and stores in Redis for dashboard inspection.
    """
    import redis
    import json
    from datetime import datetime

    logger.error(
        f"[DLQ RECEIVED] Task: {task_name} | ID: {task_id} | Error: {error}"
    )

    # Store in Redis under a 'dlq:' key for the dashboard to read
    r = redis.Redis(host='localhost', port=6379, db=2)
    entry = {
        "task_name": task_name,
        "task_id": task_id,
        "args": args,
        "error": error,
        "received_at": datetime.utcnow().isoformat()
    }
    r.lpush('dlq:failed_tasks', json.dumps(entry))
    r.ltrim('dlq:failed_tasks', 0, 999)  # keep max 1000 entries

    return {"dlq_status": "recorded", "task_id": task_id}