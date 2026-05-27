# Distributed Task Queue System

A production-grade background job processor built with **Celery + Redis**, featuring priority scheduling, exponential backoff retry, dead-letter queue handling, and a live admin dashboard.

## Architecture

Producer → Redis Broker → Celery Workers (x4) → Redis Result Backend
↓
Priority Queues: high / default / low
↓
Dead-Letter Queue (Redis db:2) → Admin Dashboard

## Features

- **3-tier priority queues** — high (emails), default (data jobs), low (reports)
- **Exponential backoff retry** — 2^n seconds between retries (2s, 4s, 8s, 16s, 32s)
- **Dead-letter queue** — exhausted tasks captured, stored, inspectable via dashboard
- **Zero message loss** — `task_acks_late=True` ensures no job lost on worker crash
- **Admin dashboard** — Flask UI showing live queue depths, worker status, DLQ entries
- **Load tested** — 10,000 jobs submitted at 3,648 tasks/sec

## Stack

| Component | Technology |
|-----------|-----------|
| Task queue | Celery 5.3.6 |
| Broker / backend | Redis 7 (Docker) |
| Dashboard | Flask 3.0 |
| Monitoring | Flower 2.0 |

## Running Locally

```bash
# 1. Start Redis
docker run -d --name redis-queue -p 6379:6379 redis:7-alpine

# 2. Start worker
celery -A worker.celery_app worker --loglevel=info -Q high,default,low --concurrency=4

# 3. Start dashboard
python -m dashboard.app

# 4. Submit jobs
python -m tests.load_test
```

## Project Structure

tasks/          Task definitions (email, data, reports, DLQ handler)
queues/         Queue config and priority routing
dashboard/      Flask admin UI
monitoring/     Dead-letter queue logic
tests/          Load test (10K jobs)
celeryconfig.py Celery + Redis configuration
worker.py       Celery app entry point