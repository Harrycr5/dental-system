from celery import Celery
from kombu import Queue

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "dental",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[],
)

celery_app.conf.update(
    task_default_queue="default",
    task_queues=(Queue("default"), Queue("notifications"), Queue("reminders")),
    task_routes={
        "notifications.*": {"queue": "notifications"},
        "reminders.*": {"queue": "reminders"},
    },
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_ignore_result=not settings.celery_result_backend_enabled,
    result_expires=3600,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=settings.celery_task_soft_time_limit,
    task_time_limit=settings.celery_task_time_limit,
    broker_connection_retry_on_startup=True,
    broker_transport_options={"visibility_timeout": 3600},
    beat_schedule={},
)


@celery_app.task(name="system.ping")
def ping() -> str:
    return "pong"
