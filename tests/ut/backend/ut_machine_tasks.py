from src.backend.machine_tasks import jog_task, send_acl_command_task, send_acl_program_task


class SerialSpy:
    def __init__(self):
        self.writes = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def write(self, data):
        self.writes.append(data)


def test_send_acl_program_task_returns_error_for_missing_serial_port():
    result = send_acl_program_task.run(
        ["MA 0, 0;"],
        settings={"SERIAL_PORT": "/dev/asymtek-missing-test-port"},
    )

    assert result == {
        "status": "error",
        "error": "Serial port not found: /dev/asymtek-missing-test-port",
    }


def test_send_acl_program_task_publishes_small_progress_json(monkeypatch):
    updates = []

    def fake_send_acl_program(
        commands,
        settings=None,
        start_index=0,
        progress_callback=None,
        control_callback=None,
    ):
        progress_callback(1, commands[1], 1)
        return [{"line_index": 1, "command": commands[1]}]

    monkeypatch.setattr("src.backend.machine_tasks.get_serial_preflight_error", lambda settings=None: None)
    monkeypatch.setattr("src.backend.machine_tasks.send_acl_program", fake_send_acl_program)
    monkeypatch.setattr(
        send_acl_program_task,
        "update_state",
        lambda state, meta: updates.append({"state": state, "meta": meta}),
    )

    result = send_acl_program_task.run(["CMD0", "CMD1"], start_index=1)

    assert updates == [
        {
            "state": "PROGRESS",
            "meta": {
                "event": "program_progress",
                "status": "sending",
                "line_index": 1,
                "command": "CMD1",
                "sent_count": 1,
                "total_count": 2,
            },
        }
    ]
    assert result == {
        "event": "program_progress",
        "status": "sent",
        "sent_count": 1,
        "total_count": 2,
        "line_index": 1,
        "last_line_index": 1,
        "command": "CMD1",
    }


def test_send_acl_program_task_returns_stopped_when_control_requests_stop(monkeypatch):
    updates = []

    def fake_send_acl_program(
        commands,
        settings=None,
        start_index=0,
        progress_callback=None,
        control_callback=None,
    ):
        assert control_callback(0, commands[0], 0) == "stop"
        return []

    monkeypatch.setattr("src.backend.machine_tasks.get_serial_preflight_error", lambda settings=None: None)
    monkeypatch.setattr("src.backend.machine_tasks.send_acl_program", fake_send_acl_program)
    monkeypatch.setattr("src.backend.machine_tasks.set_machine_control", lambda task_id, status: None)
    monkeypatch.setattr("src.backend.machine_tasks.clear_machine_control", lambda task_id: None)
    monkeypatch.setattr("src.backend.machine_tasks.get_machine_control", lambda task_id: "stopped")
    monkeypatch.setattr(
        send_acl_program_task,
        "update_state",
        lambda state, meta: updates.append({"state": state, "meta": meta}),
    )

    result = send_acl_program_task.run(["CMD0"])

    assert updates == [
        {
            "state": "PROGRESS",
            "meta": {
                "event": "program_progress",
                "status": "stopped",
                "line_index": 0,
                "command": "CMD0",
                "sent_count": 0,
                "total_count": 1,
            },
        }
    ]
    assert result == {
        "event": "program_progress",
        "status": "stopped",
        "sent_count": 0,
        "total_count": 1,
        "line_index": 0,
        "last_line_index": 0,
        "command": None,
    }


def test_send_acl_command_task_writes_command_without_position_query(monkeypatch):
    serial_connection = SerialSpy()
    monkeypatch.setattr("src.backend.machine_tasks.get_serial_preflight_error", lambda settings=None: None)
    monkeypatch.setattr(
        "src.backend.machine_tasks.open_serial_connection",
        lambda settings=None: serial_connection,
    )

    result = send_acl_command_task.run("MA 10, 20;")

    assert serial_connection.writes == [b"MA 10, 20;\r\n"]
    assert result == {"status": "sent", "command": "MA 10, 20;"}


def test_jog_task_writes_jog_command_without_position_query(monkeypatch):
    serial_connection = SerialSpy()
    monkeypatch.setattr("src.backend.machine_tasks.get_serial_preflight_error", lambda settings=None: None)
    monkeypatch.setattr(
        "src.backend.machine_tasks.open_serial_connection",
        lambda settings=None: serial_connection,
    )

    result = jog_task.run("X", 1.0, settings={"STEPSXY_PER_MM": 100})

    assert serial_connection.writes == [b"MR 100.000, 0;\r\n"]
    assert result == {
        "status": "sent",
        "axis": "X",
        "distance_mm": 1.0,
        "command": "MR 100.000, 0;",
    }
