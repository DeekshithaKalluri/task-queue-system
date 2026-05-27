from flask import Flask, jsonify, render_template
import redis
import json
from worker import celery_app

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, db=2)
r_main = redis.Redis(host='localhost', port=6379, db=0)


def get_queue_lengths():
    return {
        'high':    r_main.llen('high'),
        'default': r_main.llen('default'),
        'low':     r_main.llen('low'),
    }


def get_dlq_entries():
    raw = r.lrange('dlq:failed_tasks', 0, 49)  # last 50 entries
    entries = []
    for item in raw:
        try:
            entries.append(json.loads(item))
        except Exception:
            pass
    return entries


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/stats')
def stats():
    inspect = celery_app.control.inspect()
    active = inspect.active() or {}
    reserved = inspect.reserved() or {}

    total_active = sum(len(v) for v in active.values())
    total_reserved = sum(len(v) for v in reserved.values())

    return jsonify({
        'queues': get_queue_lengths(),
        'active_tasks': total_active,
        'pending_tasks': total_reserved,
        'dlq_count': r.llen('dlq:failed_tasks'),
        'dlq_entries': get_dlq_entries(),
    })


@app.route('/api/requeue/<task_id>', methods=['POST'])
def requeue(task_id):
    """Find a DLQ entry by task_id and resubmit it."""
    entries = get_dlq_entries()
    for entry in entries:
        if entry.get('task_id') == task_id:
            celery_app.send_task(
                entry['task_name'],
                args=eval(entry['args']),
                queue='default'
            )
            return jsonify({'status': 'requeued', 'task_id': task_id})
    return jsonify({'status': 'not_found', 'task_id': task_id}), 404


if __name__ == '__main__':
    app.run(debug=True, port=5001)