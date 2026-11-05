from unittest.mock import Mock

import pytest

from src.backend.machine_dispatcher import MachineTaskDispatcher
from src.backend.machine_management import (
    build_machine_origin_command,
    open_serial_connection,
    send_acl_command,
)
from src.backend.machine_tasks import initialize_machine_task
from src.cfg import ConfigVerificator


class SerialSpy:
    def __init__(self, responses):
        self.responses = list(responses)
        self.writes = []
        self.timeout = 1
        self.closed = False
        self.trace = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False

    def write(self, data):
        self.writes.append(data)
        self.trace.append(("write", data))

    def readline(self):
        response = self.responses.pop(0) if self.responses else b""
        self.trace.append(("read", response))
        return response

    def close(self):
        self.closed = True


def test_connect_and_reconnect_do_not_send_origin(monkeypatch):
    connections = [SerialSpy([]) for _ in range(2)]
    monkeypatch.setattr("serial.Serial", Mock(side_effect=connections))
    settings = {"MACHINE_ORIGIN": {"x": 12.5, "y": 30.25}, "STEPSXY_PER_MM": 100}

    for expected in connections:
        connection = open_serial_connection(settings)
        assert connection is expected
        assert connection.writes == []
        send_acl_command(connection, "OA; OZ;")
        assert connection.writes == [b"OA; OZ;\r\n"]
        connection.close()


def test_init_waits_for_confirmation_before_sending_saved_origin(monkeypatch):
    responses = [b"100,200\r\n", b"10\r\n", b"100,200\r\n", b"10\r\n"]
    connection = SerialSpy(responses)
    monkeypatch.setattr("serial.Serial", Mock(return_value=connection))
    monkeypatch.setattr("src.backend.machine_tasks.get_serial_preflight_error", lambda settings: None)

    result = initialize_machine_task.run(
        {"MACHINE_ORIGIN": {"x": 12.5, "y": 30.25}, "STEPSXY_PER_MM": 100, "STEPSZ_PER_MM": 10}
    )

    assert connection.trace == [
        ("write", b"in; OA; OZ;\r\n"),
        ("read", responses[0]),
        ("read", responses[1]),
        ("write", b"SO 1250, 3025; OA; OZ;\r\n"),
        ("read", responses[2]),
        ("read", responses[3]),
    ]
    assert result == {
        "event": "machine_initialized",
        "status": "sent",
        "machine_position": {"x": 1.0, "y": 2.0, "z": 1.0},
    }
    assert connection.closed


@pytest.mark.parametrize(
    "responses",
    [[b"?1\r\n"], [b""], [b"100,200\r\n", b""], [b"nan,200\r\n", b"10\r\n"], [b"invalid\r\n"]],
)
def test_init_failure_or_timeout_does_not_send_origin(monkeypatch, responses):
    connection = SerialSpy(responses)
    monkeypatch.setattr("serial.Serial", Mock(return_value=connection))
    monkeypatch.setattr("src.backend.machine_tasks.get_serial_preflight_error", lambda settings: None)

    result = initialize_machine_task.run({"MACHINE_ORIGIN": {"x": 1, "y": 2}, "STEPSXY_PER_MM": 100})

    assert result["status"] == "error"
    assert result["error"].startswith("Initialization failed:")
    assert connection.writes == [b"in; OA; OZ;\r\n"]
    assert connection.closed


def test_origin_restore_failure_does_not_report_successful_init(monkeypatch):
    connection = SerialSpy([b"100,200\r\n", b"10\r\n", b"?1\r\n"])
    monkeypatch.setattr("serial.Serial", Mock(return_value=connection))
    monkeypatch.setattr("src.backend.machine_tasks.get_serial_preflight_error", lambda settings: None)

    result = initialize_machine_task.run({"MACHINE_ORIGIN": {"x": 1, "y": 2}, "STEPSXY_PER_MM": 100})

    assert result["status"] == "error"
    assert result["error"].startswith("Origin restore failed:")
    assert connection.writes == [b"in; OA; OZ;\r\n", b"SO 100, 200; OA; OZ;\r\n"]
    assert connection.closed


def test_init_handles_missing_serial_port_without_sending_commands(monkeypatch):
    serial_factory = Mock()
    monkeypatch.setattr("serial.Serial", serial_factory)

    result = initialize_machine_task.run({"SERIAL_PORT": "/dev/asymtek-missing-test-port"})

    assert result["status"] == "error"
    serial_factory.assert_not_called()


@pytest.mark.parametrize(
    "origin",
    [None, {}, {"x": True, "y": 0}, {"x": -1, "y": 0}, {"x": float("nan"), "y": 0},
     {"x": 0, "y": float("inf")}, {"x": 400, "y": 0}],
)
def test_invalid_origin_is_rejected_before_initialization(monkeypatch, origin):
    serial_factory = Mock()
    monkeypatch.setattr("serial.Serial", serial_factory)
    monkeypatch.setattr("src.backend.machine_tasks.get_serial_preflight_error", lambda settings: None)

    result = initialize_machine_task.run({"MACHINE_ORIGIN": origin, "STEPSXY_PER_MM": 100})

    assert result["status"] == "error"
    serial_factory.assert_not_called()


@pytest.mark.parametrize("scale", [0, -1, float("nan"), float("inf")])
def test_origin_rejects_invalid_step_scale(scale):
    with pytest.raises(ValueError):
        build_machine_origin_command({"x": 1, "y": 2}, {"STEPSXY_PER_MM": scale})


def test_origin_command_converts_mm_to_integer_acl_steps():
    assert build_machine_origin_command({"x": 12.5, "y": 30.25}, {"STEPSXY_PER_MM": 100}) == "SO 1250, 3025;"
    assert build_machine_origin_command({"x": 0, "y": 327.67}, {"STEPSXY_PER_MM": 100}) == "SO 0, 32767;"


def test_init_queues_the_confirmed_initialization_task():
    dispatcher = MachineTaskDispatcher()
    dispatcher._tasks = Mock()
    settings = {"MACHINE_ORIGIN": {"x": 12.5, "y": 30.25}, "STEPSXY_PER_MM": 100}

    dispatcher.init_machine({"settings": settings})

    dispatcher._tasks.initialize_machine_task.delay.assert_called_once_with(settings=settings)
    dispatcher._tasks.send_acl_command_task.delay.assert_not_called()


def test_home_does_not_send_origin():
    dispatcher = MachineTaskDispatcher()
    dispatcher._tasks = Mock()
    settings = {"MACHINE_ORIGIN": {"x": 12.5, "y": 30.25}, "STEPSXY_PER_MM": 100}

    dispatcher.home_machine({"settings": settings})

    dispatcher._tasks.send_acl_command_task.delay.assert_called_once_with(
        "fh; OA; OZ;", settings=settings
    )


@pytest.mark.parametrize("origin", [None, {}, {"x": True, "y": 1}, {"x": -1, "y": 0},
                                    {"x": float("nan"), "y": 1}, {"x": 0, "y": float("inf")}])
def test_config_rejects_invalid_saved_origin(origin):
    assert not ConfigVerificator.verify("MACHINE_ORIGIN", origin)
