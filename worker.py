from celery import Celery

def create_app() -> Celery:
    app = Celery('task_queue_system')
    app.config_from_object('celeryconfig')
    return app

celery_app = create_app()

# Explicitly import tasks so Celery registers them
import tasks.job_tasks
import tasks.failing_tasks

if __name__ == '__main__':
    celery_app.start()