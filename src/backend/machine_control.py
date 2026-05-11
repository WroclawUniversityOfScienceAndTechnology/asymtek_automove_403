import json
import os
from pathlib import Path


CONTROL_RUNNING = "running"
CONTROL_PAUSED = "paused"
CONTROL_STOPPED = "stopped"


def _control_dir():
    return Path(os.getenv("ASYMTEK_MACHINE_CONTROL_DIR", "/tmp/asymtek-machine-control"))


def _control_path(task_id):
    return _control_dir() / "{}.json".format(task_id)


def set_machine_control(task_id, status):
    if not task_id:
        return
    control_dir = _control_dir()
    control_dir.mkdir(parents=True, exist_ok=True)
    _control_path(task_id).write_text(json.dumps({"status": status}), encoding="utf-8")


def get_machine_control(task_id):
    if not task_id:
        return CONTROL_RUNNING
    try:
        payload = json.loads(_control_path(task_id).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return CONTROL_RUNNING
    return payload.get("status", CONTROL_RUNNING)


def clear_machine_control(task_id):
    if not task_id:
        return
    try:
        _control_path(task_id).unlink()
    except FileNotFoundError:
        pass
