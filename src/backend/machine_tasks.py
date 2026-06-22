import time

from src.backend.celery_app import app
from src.backend.machine_control import (
    CONTROL_PAUSED,
    CONTROL_RUNNING,
    CONTROL_STOPPED,
    clear_machine_control,
    get_machine_control,
    set_machine_control,
)
from src.backend.machine_management import (
    build_jog_command,
    get_serial_preflight_error,
    open_serial_connection,
    send_acl_command,
    send_acl_program,
    send_acl_command_and_wait,
    query_machine_position,
    read_machine_position,
)


def _serial_error_result(exc):
    return {
        "status": "error",
        "error": str(exc),
    }


def _program_progress_payload(line_index, command, sent_count, total_count, status="sending", machine_position=None):
    return {
        "event": "program_progress",
        "status": status,
        "line_index": line_index,
        "command": command,
        "sent_count": sent_count,
        "total_count": total_count,
        "machine_position": machine_position,
    }


@app.task(bind=True, name="machine.send_acl_program")
def send_acl_program_task(self, commands, settings=None, start_index=0):
    serial_error = get_serial_preflight_error(settings)
    if serial_error:
        return _serial_error_result(serial_error)
    task_id = self.request.id or "direct-{}".format(id(self))
    if get_machine_control(task_id) == CONTROL_RUNNING:
        set_machine_control(task_id, CONTROL_RUNNING)
    run_status = {"status": "sent"}
    try:
        total_count = len(commands)

        def publish_progress(line_index, command, sent_count, status="sending", machine_position=None):
            self.update_state(
                state="PROGRESS",
                meta=_program_progress_payload(
                    line_index, command, sent_count, total_count, status=status, machine_position=machine_position),
            )

        def apply_program_control(line_index, command, sent_count):
            control_status = get_machine_control(task_id)
            if control_status == CONTROL_STOPPED:
                run_status["status"] = "stopped"
                publish_progress(line_index, command, sent_count, status="stopped")
                return "stop"
            if control_status == CONTROL_PAUSED:
                run_status["status"] = "paused"
                publish_progress(line_index, command, sent_count, status="paused")
                while True:
                    time.sleep(0.1)
                    control_status = get_machine_control(task_id)
                    if control_status == CONTROL_STOPPED:
                        run_status["status"] = "stopped"
                        publish_progress(line_index, command, sent_count, status="stopped")
                        return "stop"
                    if control_status != CONTROL_PAUSED:
                        run_status["status"] = "sent"
                        return "run"
            return "run"

        sent_commands = send_acl_program(
            commands,
            settings=settings,
            start_index=start_index,
            progress_callback=publish_progress,
            control_callback=apply_program_control,
        )
    except Exception as exc:  # pylint: disable=W0718
        return _serial_error_result(exc)
    finally:
        clear_machine_control(task_id)

    machine_position = None
    try:
        with open_serial_connection(settings=settings) as serial_connection:
            machine_position = query_machine_position(serial_connection, settings=settings)
    except Exception:
        pass

    last_command = sent_commands[-1] if sent_commands else {"line_index": start_index, "command": None}
    return {
        "event": "program_progress",
        "status": run_status["status"],
        "sent_count": len(sent_commands),
        "total_count": len(commands),
        "line_index": last_command["line_index"],
        "last_line_index": last_command["line_index"],
        "command": last_command["command"],
        "machine_position": machine_position,
    }


@app.task(name="machine.send_acl_command")
def send_acl_command_task(command, settings=None):
    serial_error = get_serial_preflight_error(settings)
    if serial_error:
        return _serial_error_result(serial_error)
    machine_position = None
    try:
        with open_serial_connection(settings=settings) as serial_connection:
            send_acl_command(serial_connection, command)
            if "OA;" in command and "OZ;" in command:
                machine_position = read_machine_position(serial_connection, settings=settings)
            else:
                machine_position = query_machine_position(serial_connection, settings=settings)
    except Exception as exc:  # pylint: disable=W0718
        return _serial_error_result(exc)
    return {
        "status": "sent",
        "command": command,
        "machine_position": machine_position,
    }

@app.task(name="machine.jog")
def jog_task(axis, distance_mm, settings=None):
    command = build_jog_command(axis, distance_mm, settings=settings)
    serial_error = get_serial_preflight_error(settings)
    if serial_error:
        result = _serial_error_result(serial_error)
        result["command"] = command
        return result
    machine_position = None
    try:
        with open_serial_connection(settings=settings) as serial_connection:
            send_acl_command(serial_connection, command)
            if "OA;" in command and "OZ;" in command:
                machine_position = read_machine_position(serial_connection, settings=settings)
            else:
                machine_position = query_machine_position(serial_connection, settings=settings)
    except Exception as exc:  # pylint: disable=W0718
        result = _serial_error_result(exc)
        result["command"] = command
        return result
    return {
        "status": "sent",
        "axis": axis,
        "distance_mm": distance_mm,
        "command": command,
        "machine_position": machine_position,
    }


@app.task(name="machine.get_position")
def get_position_task(settings=None):
    serial_error = get_serial_preflight_error(settings)
    if serial_error:
        return {"status": "poll_error", "error": serial_error}

    try:
        with open_serial_connection(settings=settings) as serial_connection:
            machine_position = query_machine_position(serial_connection, settings=settings)
            return {
                "status": "poll_success",
                "machine_position": machine_position,
            }
    except Exception as exc:
        return {"status": "poll_error", "error": str(exc)}