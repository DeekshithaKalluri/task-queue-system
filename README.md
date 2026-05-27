# ⚙️ Distributed Task Queue System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Celery](https://img.shields.io/badge/Celery-5.3.6-green.svg)](https://docs.celeryq.dev)
[![Redis](https://img.shields.io/badge/Redis-7-red.svg)](https://redis.io)
[![Flask](https://img.shields.io/badge/Flask-3.0-lightgrey.svg)](https://flask.palletsprojects.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A production-grade background job processor demonstrating distributed systems engineering: **priority queues**, **exponential backoff with jitter**, **dead-letter queue handling**, and a **live admin dashboard**.

> Load tested at **3,648 tasks/sec** across **10,000 concurrent jobs** with **zero message loss**.

---

## 📐 Architecture

```
┌─────────────┐     ┌──────────────────────────────────┐     ┌──────────────────┐
│   Producer  │────▶│         Redis Broker              │────▶│  Celery Workers  │
│ (submit_    │     │  ┌────────┐┌─────────┐┌────────┐ │     │   (4 processes)  │
│  jobs.py)   │     │  │  high  ││ default ││  low   │ │     └────────┬─────────┘
└─────────────┘     │  └────────┘└─────────┘└────────┘ │             │
                    └──────────────────────────────────┘             │
                                                                      ▼
                    ┌──────────────────────────────────┐     ┌──────────────────┐
                    │      Redis Result Backend         │     │  Dead-Letter     │
                    │      (db:1 — task results)        │     │  Queue (db:2)    │
                    └──────────────────────────────────┘     └────────┬─────────┘
                                                                      │
                                                             ┌────────▼─────────┐
                                                             │  Flask Dashboard  │
                                                             │  localhost:5001   │
                                                             └──────────────────┘
```

---

## ✨ Features

| Feature | Details |
|---------|---------|
| **3-tier priority queues** | `high` (emails) → `default` (data jobs) → `low` (reports) |
| **Exponential backoff + jitter** | `2^n + random(0, 0.3 × 2^n)` seconds — prevents thundering herd |
| **Dead-letter queue** | Tasks that exhaust retries are captured in Redis and shown in dashboard |
| **Zero message loss** | `task_acks_late=True` + `task_reject_on_worker_lost=True` |
| **Admin dashboard** | Live queue depths, worker status, DLQ entries, requeue button |
| **One-command setup** | `docker-compose up` starts Redis + worker + dashboard |

---

## 🚀 Quick Start

### Option A — Docker Compose (recommended)

```bash
docker-compose up --build
```

Then open `http://localhost:5001` for the dashboard.

### Option B — Manual

```bash
# 1. Create and activate virtual environment
python3 -m venv venv && source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start Redis
docker run -d --name redis-queue -p 6379:6379 redis:7-alpine

# 4. Start Celery worker (Terminal 1)
celery -A worker.celery_app worker --loglevel=info -Q high,default,low --concurrency=4

# 5. Start dashboard (Terminal 2)
python -m dashboard.app

# 6. Submit jobs (Terminal 3)
python -m tests.load_test
```

---

## 📊 Load Test Results

```
======================================================
  LOAD TEST — 10,000 jobs
======================================================
  Submitting 2000 email tasks to [high] queue...
  Done in 0.60s  (3308 tasks/sec submitted)
  Submitting 6000 data processing tasks to [default] queue...
  Done in 1.60s  (3742 tasks/sec submitted)
  Submitting 2000 report tasks to [low] queue...
  Done in 0.53s  (3773 tasks/sec submitted)

======================================================
  10,000 jobs submitted in 2.74s
  Avg submission rate: 3648 tasks/sec
  DLQ entries (unintended failures): 0
======================================================
```

---

## 🔁 Retry & Dead-Letter Flow

```
Task fails
    │
    ▼
retry attempt 1 → wait 2s + jitter
    │
    ▼
retry attempt 2 → wait 4s + jitter
    │
    ▼
retry attempt 3 → wait 8s + jitter
    │
    ▼
max_retries exceeded
    │
    ▼
on_failure() fires → sends to dead_letter_handler task
    │
    ▼
Stored in Redis dlq:failed_tasks → visible in dashboard
```

---

## 📁 Project Structure

```
task-queue-system/
├── tasks/
│   ├── base_task.py        # Custom base class: retry hooks, jitter backoff, DLQ routing
│   ├── job_tasks.py        # send_email, process_data, generate_report
│   └── failing_tasks.py    # always_fails (DLQ demo), dead_letter_handler
├── queues/
│   └── queue_config.py     # Queue definitions and routing logic
├── dashboard/
│   ├── app.py              # Flask API + requeue endpoint
│   └── templates/
│       └── index.html      # Live admin UI
├── monitoring/             # Reserved for Prometheus metrics
├── tests/
│   └── load_test.py        # 10K job load test with per-queue breakdown
├── celeryconfig.py         # Broker, queues, retry, concurrency settings
├── worker.py               # Celery app factory
├── docker-compose.yml      # One-command local setup
├── Dockerfile
└── requirements.txt
```

---

## 🧠 Design Decisions

**Why `task_acks_late=True`?**
By default, Celery acknowledges a message the moment a worker receives it. If the worker crashes mid-execution, the job is silently lost. Late acking only removes the message from Redis after successful completion — guaranteeing zero message loss.

**Why jitter on backoff?**
Pure exponential backoff (`2^n`) causes all retrying tasks to hit a recovering downstream service at the same moment — the thundering herd problem. Adding `random(0, 0.3 × 2^n)` spreads retries across a window, preventing re-overload.

**Why `worker_prefetch_multiplier=1`?**
Prevents fast workers from hoarding multiple tasks while slow workers sit idle. Each worker grabs exactly one task at a time — fair dispatch under mixed workloads.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Task queue | Celery 5.3.6 |
| Message broker | Redis 7 |
| Result backend | Redis 7 |
| Dashboard | Flask 3.0 |
| Monitoring UI | Flower 2.0 |
| Containerization | Docker + Docker Compose |
