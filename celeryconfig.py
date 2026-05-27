from kombu import Queue, Exchange

# --- Broker & Backend ---
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/1'

# --- Serialization ---
task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'UTC'
enable_utc = True

# --- Queue Definitions ---
# Three priority levels: high (0), default (1), low (2)
default_exchange = Exchange('tasks', type='direct')

task_queues = (
    Queue('high',    default_exchange, routing_key='high',    queue_arguments={'x-max-priority': 10}),
    Queue('default', default_exchange, routing_key='default', queue_arguments={'x-max-priority': 10}),
    Queue('low',     default_exchange, routing_key='low',     queue_arguments={'x-max-priority': 10}),
)

task_default_queue = 'default'
task_default_exchange = 'tasks'
task_default_routing_key = 'default'

# --- Retry / Reliability ---
task_acks_late = True           # only ack after task completes (no message loss on crash)
task_reject_on_worker_lost = True  # requeue if worker dies mid-task
task_track_started = True

# --- Concurrency ---
worker_prefetch_multiplier = 1  # fair dispatch — don't grab more than 1 task ahead
worker_max_tasks_per_child = 100  # recycle worker after 100 tasks (prevents memory leaks)

# --- Result Expiry ---
result_expires = 3600  # keep results in Redis for 1 hour