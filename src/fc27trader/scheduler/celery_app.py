from celery import Celery

from fc27trader.settings import get_settings

from .schedules import build_beat_schedule

settings = get_settings()
app = Celery("fc27trader", broker=settings.redis_url, backend=settings.redis_url)
app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    beat_schedule=build_beat_schedule(),
)
app.autodiscover_tasks(["fc27trader.scheduler"])
