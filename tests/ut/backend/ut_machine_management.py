import math
from types import SimpleNamespace

import pytest

from src.backend.machine_management import (
    ToolpathPoint,
    apply_xy_transform,
    build_jog_command,
    build_serial_config,
    generate_acl_from_layer,
    get_acl_command_delay,
    get_serial_preflight_error,
    get_aperture_area,
    fit_fiducial_transform,
    list_serial_ports,
    parse_acl_toolpath,
    query_machine_position,
    send_acl_line_and_wait,
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


def test_fit_fiducial_transform_maps_gerber_points_to_machine_xy():
    angle = math.radians(17)
    cosine, sine = math.cos(angle), math.sin(angle)
    offset_x, offset_y = 12.5, -7.25
    source = [(-8.0, 3.0), (11.0, -2.0), (4.0, 14.0)]
    fiducials = []
    for x, y in source:
        fiducials.append({
            "x": x,
            "y": y,
            "machine_x": cosine * x - sine * y + offset_x,
            "machine_y": sine * x + cosine * y + offset_y,
        })

    transform = fit_fiducial_transform(fiducials)

    assert transform["angle_rad"] == pytest.approx(angle)
    assert transform["offset_x_mm"] == pytest.approx(offset_x)
    assert transform["offset_y_mm"] == pytest.approx(offset_y)
    assert transform["rms_error_mm"] == pytest.approx(0.0, abs=1e-12)
    for point in fiducials:
        assert apply_xy_transform(point["x"], point["y"], transform) == pytest.approx(
            (point["machine_x"], point["machine_y"])
        )


def test_fit_fiducial_transform_with_two_fiducials():
    angle = math.radians(-0.25)
    cosine, sine = math.cos(angle), math.sin(angle)
    fiducials = []
    for x, y in ((129.54, 5.08), (20.0, 45.0)):
        fiducials.append({
            "x": x,
            "y": y,
            "machine_x": cosine * x - sine * y + 32.49,
            "machine_y": sine * x + cosine * y + 11.351,
        })

    transform = fit_fiducial_transform(fiducials)

    assert transform["angle_rad"] == pytest.approx(angle)
    assert transform["offset_x_mm"] == pytest.approx(32.49)
    assert transform["offset_y_mm"] == pytest.approx(11.351)
    assert transform["rms_error_mm"] == pytest.approx(0.0, abs=1e-12)


def test_fit_fiducial_transform_rejects_coincident_points():
    points = [
        {"x": 1, "y": 1, "machine_x": 2, "machine_y": 2},
        {"x": 1, "y": 1, "machine_x": 2, "machine_y": 2},
    ]

    with pytest.raises(ValueError, match="stable rotation"):
        fit_fiducial_transform(points)


def test_generate_acl_from_layer_applies_fiducial_translation():
    layer = SimpleNamespace(objects=[Flash(1.5, 2.0, RectangleAperture(2.0, 3.0))])
    transform = {
        "angle_rad": 0.0,
        "offset_x_mm": 5.0,
        "offset_y_mm": -3.0,
    }

    commands = generate_acl_from_layer(
        layer,
        settings={"STEPSXY_PER_MM": 10.0},
        xy_transform=transform,
    )

    assert "MA 65.000, -10.000;" in commands


def test_build_serial_config_uses_asymtek_acl_framing():
    config = build_serial_config({"SERIAL_PORT": "/dev/ttyS1", "BAUD_RATE": "4800"})

    assert config.port == "/dev/ttyS1"
    assert config.baudrate == 4800
    assert config.bytesize == 7
    assert config.parity == "E"
    assert config.stopbits == 2
    assert config.rtscts is True


def test_build_jog_command_uses_xy_steps():
    command = build_jog_command("X", -2.5, settings={"STEPSXY_PER_MM": 100})

    assert command == "MR -250.000, 0;"


def test_build_jog_command_uses_z_steps():
    command = build_jog_command("Z", 1.25, settings={"STEPSZ_PER_MM": 80})

    assert command == "RZ 100.000;"


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
        settings={"PROGRAM_STEP_DELAY_SEC": 0},
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


def test_acl_command_delay_includes_host_delay_and_acl_wait_time():
    delay = get_acl_command_delay("CD2; WA 1.500;", settings={"PROGRAM_STEP_DELAY_SEC": 0.25})

    assert delay == pytest.approx(1.75)


def test_send_acl_program_paces_between_commands(monkeypatch):
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
    sleeps = []
    monkeypatch.setattr(
        "src.backend.machine_management.open_serial_connection",
        lambda settings=None: serial_connection,
    )

    sent_commands = send_acl_program(
        ["CMD0", "CMD1"],
        settings={"PROGRAM_STEP_DELAY_SEC": 0.25},
        sleep_func=sleeps.append,
    )

    assert serial_connection.writes == [b"CMD0\r\n", b"CMD1\r\n"]
    assert sent_commands == [{"line_index": 0, "command": "CMD0"}, {"line_index": 1, "command": "CMD1"}]
    assert sleeps == pytest.approx([0.1, 0.1, 0.05])


def test_send_acl_program_stops_before_buffering_more_commands(monkeypatch):
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
    monkeypatch.setattr(
        "src.backend.machine_management.open_serial_connection",
        lambda settings=None: serial_connection,
    )

    sent_commands = send_acl_program(
        ["CMD0", "CMD1"],
        settings={"PROGRAM_STEP_DELAY_SEC": 0.25},
        control_callback=lambda line_index, command, sent_count: "stop" if sent_count else "run",
        sleep_func=lambda delay: None,
    )

    assert serial_connection.writes == [b"CMD0\r\n"]
    assert sent_commands == [{"line_index": 0, "command": "CMD0"}]


def test_query_machine_position_reads_actual_xy_and_z_as_mm():
    class SerialSpy:
        def __init__(self):
            self.writes = []
            self.responses = [b"250,500\r\n", b"125\r\n"]
            self.timeout = 1

        def write(self, data):
            self.writes.append(data)

        def readline(self):
            return self.responses.pop(0)

    serial_connection = SerialSpy()

    position = query_machine_position(
        serial_connection,
        settings={"STEPSXY_PER_MM": 100, "STEPSZ_PER_MM": 25},
    )

    assert serial_connection.writes == [b"OA;\r\n", b"OZ;\r\n"]
    assert position == {"x": 2.5, "y": 5.0, "z": 5.0}


def test_send_acl_line_and_wait_splits_multiple_acl_statements():
    class SerialSpy:
        def __init__(self):
            self.writes = []
            self.responses = [b"10,20\r\n", b"30\r\n", b"40,50\r\n", b"60\r\n"]
            self.timeout = 1

        def write(self, data):
            self.writes.append(data)

        def readline(self):
            return self.responses.pop(0)

    serial_connection = SerialSpy()

    position = send_acl_line_and_wait(
        serial_connection,
        "MA 10, 20; AZ 60;",
        settings={"STEPSXY_PER_MM": 10, "STEPSZ_PER_MM": 10},
    )

    assert serial_connection.writes == [
        b"MA 10, 20;\r\n",
        b"OA;\r\n",
        b"OZ;\r\n",
        b"AZ 60;\r\n",
        b"OA;\r\n",
        b"OZ;\r\n",
    ]
    assert position == {"x": 4.0, "y": 5.0, "z": 6.0}


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
