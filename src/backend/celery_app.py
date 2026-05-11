import os
from pathlib import Path


def _filesystem_transport_options():
    broker_root = Path(os.getenv("ASYMTEK_CELERY_BROKER_DIR", "/tmp/asymtek-celery-broker"))
    queue_dir = broker_root / "queue"
    processed_dir = broker_root / "processed"
    for directory in (queue_dir, processed_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return {
        "data_folder_in": str(queue_dir),
        "data_folder_out": str(queue_dir),
        "processed_folder": str(processed_dir),
    }


def create_celery_app():
    from celery import Celery

    celery_app = Celery(
        "asymtek_machine",
        broker=os.getenv("ASYMTEK_CELERY_BROKER_URL", "filesystem://"),
        backend=os.getenv("ASYMTEK_CELERY_RESULT_BACKEND", "rpc://"),
        include=["src.backend.machine_tasks"],
    )
    celery_app.conf.update(
        broker_transport_options=_filesystem_transport_options(),
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        task_track_started=True,
        worker_prefetch_multiplier=1,
        task_acks_late=True,
    )
    return celery_app


app = create_celery_app()
