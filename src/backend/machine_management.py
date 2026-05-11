import math
import os
import re
import time
from dataclasses import dataclass


# ==========================================
# USTAWIENIA MASZYNY ASYMTEK (ACL) I PASTY
# ==========================================
TIME_PER_SQMM = 1.0  # [sekundy/mm2] Czas wlaczenia zaworu na 1 mm2 powierzchni
Z_OFFSET_PER_SEC = 0.2  # [mm/sekunde] Wysokosc igly nad plytka na 1 s podawania
Z_SAFE_HEIGHT = 100.0  # [mm] Wysokosc bezpieczna przelotu igly
STEPSXY_PER_MM = 100  # [kroki/mm] Ilosc krokow na mm XY
STEPSZ_PER_MM = 100  # [kroki/mm] Ilosc krokow na mm Z
PROGRAM_STEP_DELAY_SEC = 0.25  # [sekundy] Host-side pause between ACL program lines


DEFAULT_MACHINE_SETTINGS = {
    "TIME_PER_SQMM": TIME_PER_SQMM,
    "Z_OFFSET_PER_SEC": Z_OFFSET_PER_SEC,
    "Z_SAFE_HEIGHT": Z_SAFE_HEIGHT,
    "STEPSXY_PER_MM": STEPSXY_PER_MM,
    "STEPSZ_PER_MM": STEPSZ_PER_MM,
    "SERIAL_PORT": "/dev/ttyUSB0",
    "BAUD_RATE": 9600,
    "COMMAND_TIMEOUT_SEC": 30.0,
    "PROGRAM_STEP_DELAY_SEC": PROGRAM_STEP_DELAY_SEC,
}


@dataclass(frozen=True)
class SerialConfig:
    port: str = "/dev/ttyUSB0"
    baudrate: int = 9600
    timeout: float = 1.0
    write_timeout: float = 1.0
    bytesize: int = 7
    parity: str = "E"
    stopbits: int = 2
    rtscts: bool = True


@dataclass(frozen=True)
class ToolpathPoint:
    x_mm: float
    y_mm: float
    line_index: int
    dispensing: bool = False


class AclMachineError(RuntimeError):
    """Raised when the ACL controller reports an error or misses a response."""


_XY_MOVE_RE = re.compile(
    r"^(M[AR])\s+"
    r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*,\s*"
    r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"
)
_WA_RE = re.compile(
    r"^WA\s+"
    r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*;$",
    re.IGNORECASE,
)


def get_aperture_area(aperture):
    """Oblicza pole powierzchni narzedzia (apertury) w mm2."""
    shape_name = type(aperture).__name__
    if shape_name == "CircleAperture":
        diameter = getattr(aperture, "diameter", getattr(aperture, "d", 0))
        radius = diameter / 2.0
        return math.pi * (radius**2)
    if shape_name == "RectangleAperture":
        return aperture.w * aperture.h
    if shape_name == "ObroundAperture":
        width = aperture.w
        height = aperture.h
        radius = min(width, height) / 2.0
        if width > height:
            return (width - height) * height + math.pi * (radius**2)
        return width * (height - width) + math.pi * (radius**2)
    return 0.0


def normalize_machine_settings(settings=None):
    normalized_settings = DEFAULT_MACHINE_SETTINGS.copy()
    if settings:
        for key in (
            "TIME_PER_SQMM",
            "Z_OFFSET_PER_SEC",
            "Z_SAFE_HEIGHT",
            "STEPSXY_PER_MM",
            "STEPSZ_PER_MM",
            "COMMAND_TIMEOUT_SEC",
            "PROGRAM_STEP_DELAY_SEC",
        ):
            if key in settings:
                normalized_settings[key] = float(settings[key])
        if "SERIAL_PORT" in settings:
            normalized_settings["SERIAL_PORT"] = str(settings["SERIAL_PORT"])
        if "BAUD_RATE" in settings:
            normalized_settings["BAUD_RATE"] = int(float(settings["BAUD_RATE"]))
    return normalized_settings


def build_serial_config(settings=None):
    machine_settings = normalize_machine_settings(settings)
    return SerialConfig(
        port=machine_settings["SERIAL_PORT"],
        baudrate=machine_settings["BAUD_RATE"],
        timeout=machine_settings["COMMAND_TIMEOUT_SEC"],
    )


def list_serial_ports():
    """Return serial device names detected on the current computer."""
    try:
        from serial.tools import list_ports
    except ImportError:
        return []

    return [port.device for port in list_ports.comports()]


def generate_acl_from_layer(layer, settings=None):
    """
    Generate ACL commands from an already loaded Gerber layer.

    The GUI uses this after selecting a Gerber file so generated commands can be
    shown and stepped through one by one before they are sent to the machine.
    """
    machine_settings = normalize_machine_settings(settings)
    time_per_sqmm = machine_settings["TIME_PER_SQMM"]
    z_offset_per_sec = machine_settings["Z_OFFSET_PER_SEC"]
    z_safe_height = machine_settings["Z_SAFE_HEIGHT"]
    stepsxy_per_mm = machine_settings["STEPSXY_PER_MM"]
    stepsz_per_mm = machine_settings["STEPSZ_PER_MM"]

    commands = [f"MA 0, 0; AZ {z_safe_height:.3f};"]

    for obj in layer.objects:
        if type(obj).__name__ != "Flash":
            continue

        area = get_aperture_area(obj.aperture)
        if area <= 0:
            continue

        x = obj.x * stepsxy_per_mm
        y = obj.y * stepsxy_per_mm
        dispense_time_sec = area * time_per_sqmm
        z_dispense_height = -dispense_time_sec * z_offset_per_sec * stepsz_per_mm

        commands.append(f"MA {x:.3f}, {y:.3f};")
        commands.append(f"AZ {z_dispense_height:.3f};")
        commands.append("CD2;")
        commands.append(f"WA {dispense_time_sec:.3f};")
        commands.append("CD0;")
        commands.append(f"AZ {z_safe_height:.3f};")

    commands.append(f"MA 0, 0; AZ {z_safe_height:.3f};")
    return commands


def generate_acl_from_gerber(gerber_path, settings=None):
    """
    Open a Gerber file and return generated ACL commands.

    gerbonara is imported here instead of at module import time so the rest of
    the application can still load even if the Gerber parser is not installed.
    """
    from gerbonara import GerberFile

    layer = GerberFile.open(gerber_path)
    return generate_acl_from_layer(layer, settings=settings)


def parse_acl_toolpath(commands, settings=None):
    """Extract XY toolpath points from ACL absolute/relative move commands."""
    machine_settings = normalize_machine_settings(settings)
    stepsxy_per_mm = machine_settings["STEPSXY_PER_MM"]
    if stepsxy_per_mm == 0:
        return []

    points = []
    current_x_mm = 0.0
    current_y_mm = 0.0

    for line_index, command in enumerate(commands):
        for statement in command.split(";"):
            statement = statement.strip()
            if not statement:
                continue

            move_match = _XY_MOVE_RE.match(statement)
            if move_match:
                move_type = move_match.group(1)
                x_mm = float(move_match.group(2)) / stepsxy_per_mm
                y_mm = float(move_match.group(3)) / stepsxy_per_mm
                if move_type == "MR":
                    current_x_mm += x_mm
                    current_y_mm += y_mm
                else:
                    current_x_mm = x_mm
                    current_y_mm = y_mm
                points.append(ToolpathPoint(current_x_mm, current_y_mm, line_index))
            elif statement.upper().startswith("CD2") and points:
                last_point = points[-1]
                points[-1] = ToolpathPoint(
                    last_point.x_mm,
                    last_point.y_mm,
                    last_point.line_index,
                    dispensing=True,
                )

    return points


def send_acl_command(serial_connection, command):
    """Send one ACL command to an opened serial connection."""
    serial_connection.write((command + "\r\n").encode("ascii"))


def open_serial_connection(settings=None):
    """
    Open serial communication for the Asymtek ACL controller.

    Required framing:
    - 7 data bits
    - RTS/CTS hardware flow control
    - 2 stop bits
    - even parity
    """
    import serial

    config = build_serial_config(settings=settings)
    return serial.Serial(
        port=config.port,
        baudrate=config.baudrate,
        bytesize=serial.SEVENBITS,
        parity=config.parity,
        stopbits=serial.STOPBITS_TWO,
        rtscts=config.rtscts,
        timeout=config.timeout,
        write_timeout=config.write_timeout,
    )


def get_serial_preflight_error(settings=None):
    config = build_serial_config(settings=settings)
    if not config.port:
        return "Serial port is empty"
    if os.name == "posix" and not os.path.exists(config.port):
        return "Serial port not found: {}".format(config.port)
    return None


def split_acl_commands(command):
    """Split an ACL text line into semicolon-terminated commands."""
    return [statement.strip() + ";" for statement in command.split(";") if statement.strip()]


def get_acl_command_delay(command, settings=None):
    """Return the host-side delay to apply after sending one ACL program line."""
    machine_settings = normalize_machine_settings(settings)
    delay_sec = max(machine_settings["PROGRAM_STEP_DELAY_SEC"], 0.0)
    for acl_command in split_acl_commands(command):
        wait_match = _WA_RE.match(acl_command)
        if wait_match:
            delay_sec += max(float(wait_match.group(1)), 0.0)
    return delay_sec


def read_acl_response(serial_connection, timeout=None):
    """Read one ACL output response terminated by the controller output terminator."""
    previous_timeout = getattr(serial_connection, "timeout", None)
    if timeout is not None and hasattr(serial_connection, "timeout"):
        serial_connection.timeout = timeout
    try:
        raw_response = serial_connection.readline()
    finally:
        if timeout is not None and hasattr(serial_connection, "timeout"):
            serial_connection.timeout = previous_timeout

    if not raw_response:
        raise AclMachineError("Timed out waiting for ACL response")
    response = raw_response.decode("ascii", errors="replace").strip()
    if response.startswith("?"):
        raise AclMachineError("ACL exceptional condition: {}".format(response))
    return response


def _parse_acl_numbers(response, expected_count):
    parts = [part.strip() for part in response.split(",")]
    if len(parts) != expected_count:
        raise AclMachineError("Unexpected ACL response: {}".format(response))
    try:
        return [float(part) for part in parts]
    except ValueError as exc:
        raise AclMachineError("Invalid ACL numeric response: {}".format(response)) from exc


def query_machine_position(serial_connection, settings=None):
    """
    Query current machine position through ACL output commands.

    Per the ACL manual, OA outputs actual XY position and waits until prior
    physical action finishes. OZ outputs the Z counter. Both values are reported
    by the machine in motor counts, so this returns millimeters for the UI.
    """
    machine_settings = normalize_machine_settings(settings)
    timeout = machine_settings["COMMAND_TIMEOUT_SEC"]

    send_acl_command(serial_connection, "OA;")
    x_steps, y_steps = _parse_acl_numbers(read_acl_response(serial_connection, timeout=timeout), 2)
    send_acl_command(serial_connection, "OZ;")
    z_steps = _parse_acl_numbers(read_acl_response(serial_connection, timeout=timeout), 1)[0]

    return {
        "x": x_steps / machine_settings["STEPSXY_PER_MM"],
        "y": y_steps / machine_settings["STEPSXY_PER_MM"],
        "z": z_steps / machine_settings["STEPSZ_PER_MM"],
    }


def send_acl_command_and_wait(serial_connection, command, settings=None):
    """
    Send one ACL command, wait until it is physically complete, and return position.

    ACL has an input buffer, so a host cannot assume that a write has completed
    the move. A following OA/OZ output request provides the completion barrier.
    """
    send_acl_command(serial_connection, command)
    return query_machine_position(serial_connection, settings=settings)


def send_acl_line_and_wait(serial_connection, command, settings=None):
    """Send every ACL statement in a line, waiting and sampling after each."""
    position = None
    for acl_command in split_acl_commands(command):
        position = send_acl_command_and_wait(serial_connection, acl_command, settings=settings)
    return position


def _program_control_requests_stop(control_callback, line_index, command, sent_count):
    if control_callback is None:
        return False
    return control_callback(line_index, command, sent_count) == "stop"


def _sleep_after_acl_command(delay_sec, sleep_func, control_callback, line_index, command, sent_count):
    remaining_sec = delay_sec
    while remaining_sec > 0:
        if _program_control_requests_stop(control_callback, line_index, command, sent_count):
            return True
        sleep_step_sec = min(0.1, remaining_sec)
        sleep_func(sleep_step_sec)
        remaining_sec -= sleep_step_sec
    return False


def send_acl_program(
    commands,
    settings=None,
    start_index=0,
    progress_callback=None,
    control_callback=None,
    sleep_func=time.sleep,
):
    """
    Send ACL commands to the machine from start_index to the end.

    This function is designed to run in a Celery worker, not in the Tk thread.
    control_callback may return "stop" to end the program before the next write.
    """
    sent_commands = []
    machine_settings = normalize_machine_settings(settings)
    last_line_index = len(commands) - 1
    with open_serial_connection(settings=settings) as serial_connection:
        for line_index, command in enumerate(commands[start_index:], start=start_index):
            if _program_control_requests_stop(control_callback, line_index, command, len(sent_commands)):
                break
            send_acl_command(serial_connection, command)
            sent_commands.append({"line_index": line_index, "command": command})
            if progress_callback is not None:
                progress_callback(line_index, command, len(sent_commands))
            if line_index < last_line_index:
                delay_sec = get_acl_command_delay(command, settings=machine_settings)
                if _sleep_after_acl_command(
                    delay_sec,
                    sleep_func,
                    control_callback,
                    line_index,
                    command,
                    len(sent_commands),
                ):
                    break
    return sent_commands


def build_jog_command(axis, distance_mm, settings=None):
    machine_settings = normalize_machine_settings(settings)
    if axis == "X":
        x_distance = distance_mm * machine_settings["STEPSXY_PER_MM"]
        return f"MR {x_distance:.3f}, 0;"
    if axis == "Y":
        y_distance = distance_mm * machine_settings["STEPSXY_PER_MM"]
        return f"MR 0, {y_distance:.3f};"
    if axis == "Z":
        z_distance = distance_mm * machine_settings["STEPSZ_PER_MM"]
        return f"RZ {z_distance:.3f};"
    raise ValueError("Unsupported jog axis: {}".format(axis))
