from celery import Celery

def get_task_priority(queue_name: str) -> int:
    """Map queue name to a numeric priority (higher = more urgent)."""
    priorities = {
        'high':    9,
        'default': 5,
        'low':     1,
    }
    return priorities.get(queue_name, 5)


def route_task(task_name: str) -> dict:
    """
    Decide which queue a task goes to based on its name.
    Tasks ending in .high / .low get routed accordingly.
    Everything else goes to default.
    """
    if task_name.endswith('_high'):
        return {'queue': 'high', 'priority': get_task_priority('high')}
    elif task_name.endswith('_low'):
        return {'queue': 'low', 'priority': get_task_priority('low')}
    else:
        return {'queue': 'default', 'priority': get_task_priority('default')}


# Route map Celery reads automatically
task_routes = {
    'tasks.*_high': {'queue': 'high'},
    'tasks.*_low':  {'queue': 'low'},
    'tasks.*':      {'queue': 'default'},
}