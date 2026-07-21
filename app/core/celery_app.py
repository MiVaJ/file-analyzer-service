from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "file_analyzer",
    broker=settings.rabbitmq_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=settings.timezone,
    enable_utc=False,
)
