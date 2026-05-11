from src.backend.celery_app import app
from src.backend.machine_management import (
    build_jog_command,
    get_serial_preflight_error,
    open_serial_connection,
    send_acl_command,
    send_acl_program,
)


def _serial_error_result(exc):
    return {
        "status": "error",
        "error": str(exc),
    }


def _program_progress_payload(line_index, command, sent_count, total_count):
    return {
        "event": "program_progress",
        "status": "sending",
        "line_index": line_index,
        "command": command,
        "sent_count": sent_count,
        "total_count": total_count,
    }


@app.task(bind=True, name="machine.send_acl_program")
def send_acl_program_task(self, commands, settings=None, start_index=0):
    serial_error = get_serial_preflight_error(settings)
    if serial_error:
        return _serial_error_result(serial_error)
    try:
        total_count = len(commands)

        def publish_progress(line_index, command, sent_count):
            self.update_state(
                state="PROGRESS",
                meta=_program_progress_payload(line_index, command, sent_count, total_count),
            )

        sent_commands = send_acl_program(
            commands,
            settings=settings,
            start_index=start_index,
            progress_callback=publish_progress,
        )
    except Exception as exc:  # pylint: disable=W0718
        return _serial_error_result(exc)
    last_command = sent_commands[-1] if sent_commands else {"line_index": start_index, "command": None}
    return {
        "event": "program_progress",
        "status": "sent",
        "sent_count": len(sent_commands),
        "total_count": len(commands),
        "line_index": last_command["line_index"],
        "last_line_index": last_command["line_index"],
        "command": last_command["command"],
    }


@app.task(name="machine.send_acl_command")
def send_acl_command_task(command, settings=None):
    serial_error = get_serial_preflight_error(settings)
    if serial_error:
        return _serial_error_result(serial_error)
    try:
        with open_serial_connection(settings=settings) as serial_connection:
            send_acl_command(serial_connection, command)
    except Exception as exc:  # pylint: disable=W0718
        return _serial_error_result(exc)
    return {
        "status": "sent",
        "command": command,
    }


@app.task(name="machine.jog")
def jog_task(axis, distance_mm, settings=None):
    command = build_jog_command(axis, distance_mm, settings=settings)
    serial_error = get_serial_preflight_error(settings)
    if serial_error:
        result = _serial_error_result(serial_error)
        result["command"] = command
        return result
    try:
        with open_serial_connection(settings=settings) as serial_connection:
            send_acl_command(serial_connection, command)
    except Exception as exc:  # pylint: disable=W0718
        result = _serial_error_result(exc)
        result["command"] = command
        return result
    return {
        "status": "sent",
        "axis": axis,
        "distance_mm": distance_mm,
        "command": command,
    }
