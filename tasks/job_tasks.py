import time
import random
import logging
from worker import celery_app
from tasks.base_task import BaseTaskWithRetry

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    base=BaseTaskWithRetry,
    name='tasks.send_email',
    queue='high',
    max_retries=5
)
def send_email(self, recipient: str, subject: str, body: str) -> dict:
    """
    Simulates sending an email.
    HIGH priority queue — user-facing, must be fast.
    """
    logger.info(f"Sending email to {recipient} | Subject: {subject}")
    try:
        # Simulate occasional network hiccup (20% chance)
        if random.random() < 0.2:
            raise ConnectionError(f"SMTP server unreachable for {recipient}")

        time.sleep(random.uniform(0.1, 0.5))  # simulate network delay
        return {"status": "sent", "recipient": recipient, "subject": subject}

    except Exception as exc:
        # Exponential backoff: 2^retry seconds (2, 4, 8, 16, 32)
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(
    bind=True,
    base=BaseTaskWithRetry,
    name='tasks.process_data',
    queue='default',
    max_retries=3
)
def process_data(self, dataset_id: str, operation: str) -> dict:
    """
    Simulates a data processing job.
    DEFAULT priority queue — background work.
    """
    logger.info(f"Processing dataset {dataset_id} | Operation: {operation}")
    try:
        if random.random() < 0.15:
            raise ValueError(f"Corrupt data in dataset {dataset_id}")

        time.sleep(random.uniform(0.5, 1.5))  # heavier work
        rows_processed = random.randint(1000, 50000)
        return {
            "status": "processed",
            "dataset_id": dataset_id,
            "operation": operation,
            "rows": rows_processed
        }

    except Exception as exc:
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)


@celery_app.task(
    bind=True,
    base=BaseTaskWithRetry,
    name='tasks.generate_report',
    queue='low',
    max_retries=3
)
def generate_report(self, report_type: str, date_range: str) -> dict:
    """
    Simulates generating a report (PDF/CSV export).
    LOW priority queue — can wait.
    """
    logger.info(f"Generating {report_type} report | Range: {date_range}")
    try:
        if random.random() < 0.1:
            raise TimeoutError(f"Report generation timed out for {report_type}")

        time.sleep(random.uniform(1.0, 3.0))  # heavy operation
        return {
            "status": "generated",
            "report_type": report_type,
            "date_range": date_range,
            "file": f"{report_type}_{date_range}.pdf"
        }

    except Exception as exc:
        countdown = 2 ** self.request.retries
        raise self.retry(exc=exc, countdown=countdown)