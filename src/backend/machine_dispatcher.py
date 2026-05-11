from src.logger import Logger


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

    def get_task_progress(self, task_id):
        if not task_id:
            return None

        task_result = self._load_tasks().app.AsyncResult(task_id)
        info = task_result.info if isinstance(task_result.info, dict) else {}
        progress = {
            "task_id": task_id,
            "state": task_result.state,
            "done": task_result.ready(),
        }
        progress.update(info)

        result = task_result.result if task_result.ready() and isinstance(task_result.result, dict) else {}
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
