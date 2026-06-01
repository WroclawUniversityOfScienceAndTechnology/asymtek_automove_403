from src.logger import Logger
from src.backend.machine_control import CONTROL_PAUSED, CONTROL_RUNNING, CONTROL_STOPPED, set_machine_control


class MachineTaskDispatcher:
    def __init__(self):
        self._tasks = None

    def _load_tasks(self):
        if self._tasks is None:
            from src.backend import machine_tasks

            self._tasks = machine_tasks
        return self._tasks

    def start_program(self, payload):
        commands = payload.get("execution_lines") or []
        if not commands:
            Logger().log_warning("Machine start ignored: no ACL commands loaded")
            return None

        task = self._load_tasks().send_acl_program_task.delay(
            commands,
            settings=payload.get("settings", {}),
            start_index=payload.get("line_index", 0),
        )
        Logger().log_info("Machine program task queued: " + task.id)
        return task.id

    def pause_program(self, task_id):
        if not task_id:
            return None
        set_machine_control(task_id, CONTROL_PAUSED)
        Logger().log_info("Machine program pause requested: " + task_id)
        return task_id

    def resume_program(self, task_id):
        if not task_id:
            return None
        set_machine_control(task_id, CONTROL_RUNNING)
        Logger().log_info("Machine program resume requested: " + task_id)
        return task_id

    def stop_program(self, task_id):
        if not task_id:
            return None
        set_machine_control(task_id, CONTROL_STOPPED)
        Logger().log_info("Machine program stop requested: " + task_id)
        return task_id

    def get_task_progress(self, task_id):
        if not task_id:
            return None

        task_result = self._load_tasks().app.AsyncResult(task_id)

        progress = {
            "task_id": task_id,
            "state": task_result.state,
            "done": task_result.ready(),
        }

        # 1. Pobieramy status tylko raz, aby uniknąć problemów ze współbieżnością (race condition)
        raw_info = task_result.info
        info = raw_info if isinstance(raw_info, dict) else {}
        progress.update(info)

        # 2. Pobieramy wynik zadania również tylko raz
        raw_result = task_result.result
        result = raw_result if task_result.ready() and isinstance(raw_result, dict) else {}
        progress.update(result)

        return progress

    def send_current_command(self, payload):
        command = payload.get("command")
        if not command:
            Logger().log_warning("Machine command ignored: empty command")
            return None

        task = self._load_tasks().send_acl_command_task.delay(command, settings=payload.get("settings", {}))
        Logger().log_info("Machine command task queued: " + task.id)
        return task.id

    def jog(self, payload):
        axis = payload.get("axis")
        distance_mm = payload.get("distance_mm")
        if axis is None or distance_mm is None:
            Logger().log_warning("Machine jog ignored: missing axis or distance")
            return None

        task = self._load_tasks().jog_task.delay(axis, distance_mm, settings=payload.get("settings", {}))
        Logger().log_info("Machine jog task queued: " + task.id)
        return task.id

    def trigger_get_position(self, payload):
        from src.backend.machine_tasks import get_position_task
        settings = payload.get("settings")
        async_result = get_position_task.delay(settings=settings)
        return async_result.id
