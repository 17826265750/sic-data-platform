"""
Celery Application Configuration
"""
from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    "sic_data_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,

    # Task execution limits
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time per worker
    worker_max_tasks_per_child=50,  # Prevent memory leaks

    # Result backend settings
    result_expires=86400,  # Results expire after 1 day

    # Task routing
    task_routes={
        "workers.tasks.processing_tasks.*": {"queue": "processing"},
    },

    # Beat scheduler (for periodic tasks if needed)
    beat_schedule={},

    # Task annotations
    task_annotations={
        "*": {"rate_limit": "10/m"},
    },
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["workers.tasks"])