from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery = Celery(
    "noticesense",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Ensure the tasks module is imported so the worker registers the task.
celery.autodiscover_tasks(["app.tasks"])

from app.tasks import processing  # noqa: E402,F401
