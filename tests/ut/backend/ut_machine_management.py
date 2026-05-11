from types import SimpleNamespace

import pytest

from src.backend.machine_management import (
    ToolpathPoint,
    build_jog_command,
    build_serial_config,
    generate_acl_from_layer,
    get_serial_preflight_error,
    get_aperture_area,
    list_serial_ports,
    parse_acl_toolpath,
    send_acl_program,
)


class CircleAperture:
    def __init__(self, diameter):
        self.diameter = diameter


class RectangleAperture:
    def __init__(self, width, height):
        self.w = width
        self.h = height


class Flash:
    def __init__(self, x, y, aperture):
        self.x = x
        self.y = y
        self.aperture = aperture


def test_get_aperture_area_for_circle():
    assert get_aperture_area(CircleAperture(2.0)) == pytest.approx(3.141592653589793)


def test_generate_acl_from_layer_uses_machine_settings():
    layer = SimpleNamespace(objects=[Flash(1.5, 2.0, RectangleAperture(2.0, 3.0))])
    settings = {
        "TIME_PER_SQMM": 0.5,
        "Z_OFFSET_PER_SEC": 0.25,
        "Z_SAFE_HEIGHT": 50.0,
        "STEPSXY_PER_MM": 10.0,
        "STEPSZ_PER_MM": 20.0,
    }

    commands = generate_acl_from_layer(layer, settings=settings)

    assert commands == [
        "MA 0, 0; AZ 50.000;",
        "MA 15.000, 20.000;",
        "AZ -15.000;",
        "CD2;",
        "WA 3.000;",
        "CD0;",
        "AZ 50.000;",
        "MA 0, 0; AZ 50.000;",
    ]


def test_build_serial_config_uses_asymtek_acl_framing():
    config = build_serial_config({"SERIAL_PORT": "/dev/ttyS1", "BAUD_RATE": "4800"})

    assert config.port == "/dev/ttyS1"
    assert config.baudrate == 4800
    assert config.bytesize == 7
    assert config.parity == "O"
    assert config.stopbits == 2
    assert config.rtscts is True


def test_build_jog_command_uses_xy_steps():
    command = build_jog_command("X", -2.5, settings={"STEPSXY_PER_MM": 100})

    assert command == "MR -250.000, 0;"


def test_serial_preflight_reports_missing_posix_port():
    error = get_serial_preflight_error({"SERIAL_PORT": "/dev/asymtek-missing-test-port"})

    assert error == "Serial port not found: /dev/asymtek-missing-test-port"


def test_list_serial_ports_returns_device_names(monkeypatch):
    ports = [
        SimpleNamespace(device="COM3"),
        SimpleNamespace(device="/dev/ttyUSB0"),
    ]
    monkeypatch.setattr("serial.tools.list_ports.comports", lambda: ports)

    assert list_serial_ports() == ["COM3", "/dev/ttyUSB0"]


def test_send_acl_program_reports_progress_for_each_sent_command(monkeypatch):
    class SerialSpy:
        def __init__(self):
            self.writes = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            return False

        def write(self, data):
            self.writes.append(data)

    serial_connection = SerialSpy()
    progress = []
    monkeypatch.setattr(
        "src.backend.machine_management.open_serial_connection",
        lambda settings=None: serial_connection,
    )

    sent_commands = send_acl_program(
        ["CMD0", "CMD1", "CMD2"],
        start_index=1,
        progress_callback=lambda line_index, command, sent_count: progress.append(
            {
                "line_index": line_index,
                "command": command,
                "sent_count": sent_count,
            }
        ),
    )

    assert serial_connection.writes == [b"CMD1\r\n", b"CMD2\r\n"]
    assert sent_commands == [
        {"line_index": 1, "command": "CMD1"},
        {"line_index": 2, "command": "CMD2"},
    ]
    assert progress == [
        {"line_index": 1, "command": "CMD1", "sent_count": 1},
        {"line_index": 2, "command": "CMD2", "sent_count": 2},
    ]


def test_parse_acl_toolpath_converts_acl_steps_to_mm_and_marks_dispense_points():
    commands = [
        "MA 0, 0; AZ 50.000;",
        "MA 150.000, 200.000;",
        "AZ -15.000;",
        "CD2;",
        "WA 3.000;",
        "CD0;",
        "MA 0, 0; AZ 50.000;",
    ]

    points = parse_acl_toolpath(commands, settings={"STEPSXY_PER_MM": 10})

    assert points == [
        ToolpathPoint(0.0, 0.0, 0),
        ToolpathPoint(15.0, 20.0, 1, dispensing=True),
        ToolpathPoint(0.0, 0.0, 6),
    ]


def test_parse_acl_toolpath_supports_relative_xy_moves():
    commands = [
        "MA 100, 200;",
        "MR -50, 25;",
    ]

    points = parse_acl_toolpath(commands, settings={"STEPSXY_PER_MM": 10})

    assert points == [
        ToolpathPoint(10.0, 20.0, 0),
        ToolpathPoint(5.0, 22.5, 1),
    ]
