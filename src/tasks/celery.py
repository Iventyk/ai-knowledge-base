from celery import Celery

from src.core.config import settings


celery_app = Celery("ai_knowledge_base", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_track_started = True
celery_app.conf.result_expires = 3600
