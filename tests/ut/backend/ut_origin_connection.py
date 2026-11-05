from unittest.mock import Mock

import pytest

from src.backend.machine_dispatcher import MachineTaskDispatcher
from src.backend.machine_management import (
    AclMachineError,
    build_machine_origin_command,
    open_serial_connection,
    send_acl_command,
)
from src.cfg import ConfigVerificator


class SerialSpy:
    def __init__(self, responses):
        self.responses = list(responses)
        self.writes = []
        self.timeout = 1
        self.closed = False

    def write(self, data):
        self.writes.append(data)

    def readline(self):
        return self.responses.pop(0)

    def close(self):
        self.closed = True


def test_connect_and_reconnect_restore_origin_before_other_commands(monkeypatch):
    connections = [SerialSpy([b"100,200\r\n", b"10\r\n"]) for _ in range(2)]
    monkeypatch.setattr("serial.Serial", Mock(side_effect=connections))
    settings = {"MACHINE_ORIGIN": {"x": 12.5, "y": 30.25}, "STEPSXY_PER_MM": 100}

    for expected in connections:
        connection = open_serial_connection(settings)
        send_acl_command(connection, "MA 0, 0;")
        assert connection is expected
        assert connection.writes == [b"SO 1250, 3025; OA; OZ;\r\n", b"MA 0, 0;\r\n"]
        assert connection.responses == []


@pytest.mark.parametrize("responses", [[b"?1\r\n"], [b""]])
def test_failed_origin_restore_closes_connection_and_aborts(monkeypatch, responses):
    connection = SerialSpy(responses)
    monkeypatch.setattr("serial.Serial", Mock(return_value=connection))

    with pytest.raises(AclMachineError):
        restored = open_serial_connection({"MACHINE_ORIGIN": {"x": 1, "y": 2}, "STEPSXY_PER_MM": 100})
        send_acl_command(restored, "MA 0, 0;")

    assert connection.closed
    assert connection.writes == [b"SO 100, 200; OA; OZ;\r\n"]


@pytest.mark.parametrize(
    "origin",
    [None, {}, {"x": True, "y": 0}, {"x": -1, "y": 0}, {"x": float("nan"), "y": 0},
     {"x": 0, "y": float("inf")}, {"x": 400, "y": 0}],
)
def test_invalid_origin_is_rejected_before_serial_port_is_opened(monkeypatch, origin):
    serial_factory = Mock()
    monkeypatch.setattr("serial.Serial", serial_factory)

    with pytest.raises(ValueError):
        open_serial_connection({"MACHINE_ORIGIN": origin, "STEPSXY_PER_MM": 100})

    serial_factory.assert_not_called()


@pytest.mark.parametrize("scale", [0, -1, float("nan"), float("inf")])
def test_origin_rejects_invalid_step_scale(scale):
    with pytest.raises(ValueError):
        build_machine_origin_command({"x": 1, "y": 2}, {"STEPSXY_PER_MM": scale})


def test_origin_command_converts_mm_to_integer_acl_steps():
    assert build_machine_origin_command({"x": 12.5, "y": 30.25}, {"STEPSXY_PER_MM": 100}) == "SO 1250, 3025;"
    assert build_machine_origin_command({"x": 0, "y": 327.67}, {"STEPSXY_PER_MM": 100}) == "SO 0, 32767;"


@pytest.mark.parametrize("method, prefix", [("init_machine", "in;"), ("home_machine", "fh;")])
def test_machine_reset_commands_reapply_saved_origin(method, prefix):
    dispatcher = MachineTaskDispatcher()
    dispatcher._tasks = Mock()
    settings = {"MACHINE_ORIGIN": {"x": 12.5, "y": 30.25}, "STEPSXY_PER_MM": 100}

    getattr(dispatcher, method)({"settings": settings})

    dispatcher._tasks.send_acl_command_task.delay.assert_called_once_with(
        prefix + " SO 1250, 3025; OA; OZ;", settings=settings
    )


@pytest.mark.parametrize("origin", [None, {}, {"x": True, "y": 1}, {"x": -1, "y": 0},
                                    {"x": float("nan"), "y": 1}, {"x": 0, "y": float("inf")}])
def test_config_rejects_invalid_saved_origin(origin):
    assert not ConfigVerificator.verify("MACHINE_ORIGIN", origin)
