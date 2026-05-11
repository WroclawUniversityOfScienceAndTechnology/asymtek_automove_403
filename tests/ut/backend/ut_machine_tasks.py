from src.backend.machine_tasks import send_acl_program_task


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

    def fake_send_acl_program(commands, settings=None, start_index=0, progress_callback=None):
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
