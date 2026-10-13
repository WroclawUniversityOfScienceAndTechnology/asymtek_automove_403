import os
from pathlib import Path
import tempfile


def _broker_root():
    default_root = Path(tempfile.gettempdir()) / "asymtek-celery-broker"
    return Path(os.getenv("ASYMTEK_CELERY_BROKER_DIR", str(default_root)))


def _filesystem_transport_options():
    broker_root = _broker_root()
    queue_dir = broker_root / "queue"
    processed_dir = broker_root / "processed"
    for directory in (queue_dir, processed_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return {
        "data_folder_in": str(queue_dir),
        "data_folder_out": str(queue_dir),
        "processed_folder": str(processed_dir),
    }


def _filesystem_result_backend():
    """Keep task results out of the filesystem broker's shared queue."""
    broker_root = _broker_root()
    results_dir = broker_root / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    return "file://" + results_dir.as_posix()


def create_celery_app():
    from celery import Celery

    celery_app = Celery(
        "asymtek_machine",
        broker=os.getenv("ASYMTEK_CELERY_BROKER_URL", "filesystem://"),
        backend=os.getenv("ASYMTEK_CELERY_RESULT_BACKEND", _filesystem_result_backend()),
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
        result_expires=86400,
    )
    return celery_app


app = create_celery_app()
