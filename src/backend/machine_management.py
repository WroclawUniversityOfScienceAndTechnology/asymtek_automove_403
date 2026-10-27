import math
import os
import re
import time
from bisect import bisect_right
from dataclasses import dataclass


# ==========================================
# USTAWIENIA MASZYNY ASYMTEK (ACL) I PASTY
# ==========================================
TIME_PER_SQMM = 1.0  # [sekundy/mm2] Czas wlaczenia zaworu na 1 mm2 powierzchni
Z_OFFSET_PER_SEC = 0.2  # [mm/sekunde] Wysokosc igly nad plytka na 1 s podawania
Z_SAFE_HEIGHT = 5  # [mm] Wysokosc bezpieczna przelotu igly
STEPSXY_PER_MM = 39.37  # [kroki/mm] Ilosc krokow na mm XY
STEPSZ_PER_MM = 10  # [kroki/mm] Ilosc krokow na mm Z
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


def generate_acl_from_layer(layer, settings=None, xy_transform=None):
    """
    Generate ACL commands using relative positioning after the initial XY move.
    With fiducial calibration, the first XY move is absolute so the program can
    start from the machine position left by the calibration workflow.
    Z-axis logic is adjusted natively to match the physical motor direction
    (negative Z values move the head UP, positive Z values move it DOWN).
    """
    machine_settings = normalize_machine_settings(settings)
    time_per_sqmm = machine_settings["TIME_PER_SQMM"]
    z_offset_per_sec = machine_settings["Z_OFFSET_PER_SEC"]
    z_safe_height = machine_settings["Z_SAFE_HEIGHT"]
    stepsxy_per_mm = machine_settings["STEPSXY_PER_MM"]
    stepsz_per_mm = machine_settings["STEPSZ_PER_MM"]
    bed_points = (settings or {}).get("Z_BED_POINTS", [])
    reference_z = bed_points[0].get("z_steps", 0) if bed_points else 0
    bed_grid = {}
    for point in bed_points:
        try:
            px, py = float(point["x"]), float(point["y"])
            correction = float(point["z_steps"]) - float(reference_z)
        except (KeyError, TypeError, ValueError):
            continue
        bed_grid[(px, py)] = correction
    bed_xs = sorted({x for x, _ in bed_grid})
    bed_ys = sorted({y for _, y in bed_grid})

    def _linear_interval(coordinates, value):
        """Choose an adjacent pair, extending the edge pair beyond the sample area."""
        if len(coordinates) < 2:
            return None
        lower = bisect_right(coordinates, value) - 1
        lower = min(max(lower, 0), len(coordinates) - 2)
        return coordinates[lower], coordinates[lower + 1]

    def bed_correction(x_mm, y_mm):
        x_interval = _linear_interval(bed_xs, x_mm)
        y_interval = _linear_interval(bed_ys, y_mm)
        if x_interval is None or y_interval is None:
            return 0.0
        x0, x1 = x_interval
        y0, y1 = y_interval
        corners = ((x0, y0), (x1, y0), (x0, y1), (x1, y1))
        if any(corner not in bed_grid for corner in corners):
            return 0.0
        tx = (x_mm - x0) / (x1 - x0)
        ty = (y_mm - y0) / (y1 - y0)
        z00, z10, z01, z11 = (bed_grid[corner] for corner in corners)
        lower = z00 + (z10 - z00) * tx
        upper = z01 + (z11 - z01) * tx
        return lower + (upper - lower) * ty

    commands = []

    # Virtual starting positions (assuming 0,0,0 on the board)
    current_x = 0.0
    current_y = 0.0
    first_xy_move = True
    current_z = 0.0

    # 1. SAFETY: First, raise the needle from 0,0,0 to the safe height
    # Added '-' because physical Z-axis is inverted (negative goes UP)
    target_z_safe = -z_safe_height * stepsz_per_mm

    dz_init = target_z_safe - current_z
    if dz_init != 0:
        commands.append(f"MZ {dz_init:.3f};")
        current_z = target_z_safe

    # Gerber object order follows file layout, which can cause long, erratic
    # traversals. Greedily choose the nearest remaining dispense point, starting
    # from the assumed machine origin. The original order breaks distance ties.
    flashes = [
        obj
        for obj in layer.objects
        if type(obj).__name__ == "Flash" and get_aperture_area(obj.aperture) > 0
    ]
    ordered_flashes = []
    nearest_x = 0.0
    nearest_y = 0.0
    while flashes:
        next_index = min(
            range(len(flashes)),
            key=lambda index: (
                (flashes[index].x - nearest_x) ** 2
                + (flashes[index].y - nearest_y) ** 2,
                index,
            ),
        )
        obj = flashes.pop(next_index)
        ordered_flashes.append(obj)
        nearest_x = obj.x
        nearest_y = obj.y

    # The command-generation loop below updates current_x/current_y in steps.
    current_x = 0.0
    current_y = 0.0
    previous_rotated_x_mm = None
    previous_rotated_y_mm = None

    for obj in ordered_flashes:
        area = get_aperture_area(obj.aperture)

        # Apply the translation to the first absolute point only. Subsequent
        # relative moves use rotated Gerber deltas, so the translation cannot
        # accumulate or affect the distance between pads.
        if xy_transform:
            rotated_x_mm, rotated_y_mm = _rotate_xy(obj.x, obj.y, xy_transform)
            if first_xy_move:
                target_x = (rotated_x_mm + float(xy_transform["offset_x_mm"])) * stepsxy_per_mm
                target_y = (rotated_y_mm + float(xy_transform["offset_y_mm"])) * stepsxy_per_mm
                commands.append(f"MR {target_x:.3f}, {target_y:.3f};")
                current_x, current_y = target_x, target_y
            else:
                dx = (rotated_x_mm - previous_rotated_x_mm) * stepsxy_per_mm
                dy = (rotated_y_mm - previous_rotated_y_mm) * stepsxy_per_mm
                if dx != 0 or dy != 0:
                    commands.append(f"MR {dx:.3f}, {dy:.3f};")
                current_x += dx
                current_y += dy
            previous_rotated_x_mm, previous_rotated_y_mm = rotated_x_mm, rotated_y_mm
            first_xy_move = False
        else:
            target_x = obj.x * stepsxy_per_mm
            target_y = obj.y * stepsxy_per_mm
            dx = target_x - current_x
            dy = target_y - current_y
            if dx != 0 or dy != 0:
                commands.append(f"MR {dx:.3f}, {dy:.3f};")
            current_x, current_y = target_x, target_y
            first_xy_move = False
        dispense_time_sec = area * time_per_sqmm

        # Dispensing height
        # (Positive value because Z is inverted, so positive moves DOWN towards the board)
        target_z_dispense = dispense_time_sec * z_offset_per_sec * stepsz_per_mm + bed_correction(obj.x, obj.y)

        # 3. Relative Z lower (MZ) to dispensing height
        dz_down = target_z_dispense - current_z
        if dz_down != 0:
            commands.append(f"MZ {dz_down:.3f}; OA; OZ;")

        current_z = target_z_dispense

        # 4. Dispensing
        commands.append("CD2;")
        commands.append(f"WA {dispense_time_sec:.3f};")
        commands.append("CD0; OA; OZ;")

        # 5. Relative Z raise (MZ) to safe height
        dz_up = target_z_safe - current_z
        if dz_up != 0:
            commands.append(f"MZ {dz_up:.3f}; OA; OZ;")

        current_z = target_z_safe

    # 6. Optional: return to the Origin (0,0) in XY axes after finishing work
    dx_home = 0.0 - current_x
    dy_home = 0.0 - current_y
    if dx_home != 0 or dy_home != 0:
        commands.append(f"MR {dx_home:.3f}, {dy_home:.3f};")

    # Note: The Z axis is intentionally left at target_z_safe.
    # We do not lower it back to 0,0,0 so the needle does not hit
    # the board or freshly applied solder paste after returning to the start point.

    return commands


def generate_acl_from_gerber(gerber_path, settings=None, xy_transform=None):
    """
    Open a Gerber file and return generated ACL commands.

    gerbonara is imported here instead of at module import time so the rest of
    the application can still load even if the Gerber parser is not installed.
    """
    from gerbonara import GerberFile

    layer = GerberFile.open(gerber_path)
    return generate_acl_from_layer(layer, settings=settings, xy_transform=xy_transform)


def _rotate_xy(x_mm, y_mm, transform):
    """Rotate a Gerber coordinate without applying its XY translation."""
    angle = float(transform["angle_rad"])
    cosine, sine = math.cos(angle), math.sin(angle)
    return cosine * x_mm - sine * y_mm, sine * x_mm + cosine * y_mm


def apply_xy_transform(x_mm, y_mm, transform):
    """Map a Gerber coordinate to machine XY using rotation and translation."""
    rotated_x, rotated_y = _rotate_xy(x_mm, y_mm, transform)
    return (
        rotated_x + float(transform["offset_x_mm"]),
        rotated_y + float(transform["offset_y_mm"]),
    )


def fit_fiducial_transform(fiducials):
    """Fit a rigid transform mapping Gerber fiducials to machine coordinates."""
    if len(fiducials) < 2:
        raise ValueError("At least two fiducials are required")
    try:
        source = [(float(point["x"]), float(point["y"])) for point in fiducials]
        target = [(float(point["machine_x"]), float(point["machine_y"])) for point in fiducials]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Each fiducial needs finite Gerber and machine XY coordinates") from exc
    if not all(math.isfinite(value) for pair in source + target for value in pair):
        raise ValueError("Fiducial coordinates must be finite numbers")

    source_x = sum(point[0] for point in source) / len(source)
    source_y = sum(point[1] for point in source) / len(source)
    target_x = sum(point[0] for point in target) / len(target)
    target_y = sum(point[1] for point in target) / len(target)
    dot = cross = 0.0
    source_spread = target_spread = 0.0
    for (sx, sy), (tx, ty) in zip(source, target):
        sx, sy = sx - source_x, sy - source_y
        tx, ty = tx - target_x, ty - target_y
        dot += sx * tx + sy * ty
        cross += sx * ty - sy * tx
        source_spread += sx * sx + sy * sy
        target_spread += tx * tx + ty * ty
    if source_spread < 1e-12 or target_spread < 1e-12 or math.hypot(dot, cross) < 1e-12:
        raise ValueError("Fiducial positions do not define a stable rotation")
    angle = math.atan2(cross, dot)
    cosine, sine = math.cos(angle), math.sin(angle)
    offset_x = target_x - (cosine * source_x - sine * source_y)
    offset_y = target_y - (sine * source_x + cosine * source_y)
    squared_error = 0.0
    for (source_px, source_py), (target_px, target_py) in zip(source, target):
        predicted_x = cosine * source_px - sine * source_py + offset_x
        predicted_y = sine * source_px + cosine * source_py + offset_y
        squared_error += (predicted_x - target_px) ** 2 + (predicted_y - target_py) ** 2
    return {
        "angle_rad": angle,
        "offset_x_mm": offset_x,
        "offset_y_mm": offset_y,
        "rms_error_mm": math.sqrt(squared_error / len(fiducials)),
    }


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


def read_machine_position(serial_connection, settings=None):
    """Read XY and Z position values from the serial buffer."""
    machine_settings = normalize_machine_settings(settings)
    timeout = machine_settings["COMMAND_TIMEOUT_SEC"]

    x_steps, y_steps = _parse_acl_numbers(read_acl_response(serial_connection, timeout=timeout), 2)
    z_steps = _parse_acl_numbers(read_acl_response(serial_connection, timeout=timeout), 1)[0]

    return {
        "x": x_steps / machine_settings["STEPSXY_PER_MM"],
        "y": y_steps / machine_settings["STEPSXY_PER_MM"],
        "z": z_steps / machine_settings["STEPSZ_PER_MM"],
    }

def query_machine_position(serial_connection, settings=None):
    """
    Query current machine position through ACL output commands.
    """
    try:
        serial_connection.reset_input_buffer()
    except Exception:
        pass

    send_acl_command(serial_connection, "OA; OZ;")
    return read_machine_position(serial_connection, settings=settings)


def send_acl_command_and_wait(serial_connection, command, settings=None):
    send_acl_command(serial_connection, command)
    if "OA;" in command and "OZ;" in command:
        return read_machine_position(serial_connection, settings=settings)
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
    Uses an advanced handshake that prevents protocol desynchronization.
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

            machine_position = None

            # Nowa logika odczytująca pozycję w przerwie
            if "OA;" in command and "OZ;" in command:
                original_timeout = serial_connection.timeout
                try:
                    serial_connection.timeout = 5.0
                    machine_position = read_machine_position(serial_connection, settings=machine_settings)
                except Exception:
                    try:
                        serial_connection.reset_input_buffer()
                        serial_connection.reset_output_buffer()
                    except Exception:
                        pass
                    sleep_func(machine_settings["PROGRAM_STEP_DELAY_SEC"])
                finally:
                    serial_connection.timeout = original_timeout
            elif "MR" in command or "MZ" in command:
                # Zachowanie kompatybilności dla starszych programów w razie braku połączonych komend
                original_timeout = serial_connection.timeout
                try:
                    serial_connection.timeout = 5.0
                    machine_position = query_machine_position(serial_connection, settings=machine_settings)
                except Exception:
                    try:
                        serial_connection.reset_input_buffer()
                        serial_connection.reset_output_buffer()
                    except Exception:
                        pass
                    sleep_func(machine_settings["PROGRAM_STEP_DELAY_SEC"])
                finally:
                    serial_connection.timeout = original_timeout

            if progress_callback is not None:
                try:
                    progress_callback(line_index, command, len(sent_commands), machine_position=machine_position)
                except TypeError:
                    progress_callback(line_index, command, len(sent_commands))

            if line_index < last_line_index:
                if not ("MR" in command or "MZ" in command):
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
        return f"MR {x_distance:.3f}, 0; OA; OZ;"
    if axis == "Y":
        y_distance = distance_mm * machine_settings["STEPSXY_PER_MM"]
        return f"MR 0, {y_distance:.3f}; OA; OZ;"
    if axis == "Z":
        z_distance = distance_mm * machine_settings["STEPSZ_PER_MM"]
        print("dist z ", z_distance)
        return f"MZ {z_distance:.3f}; OA; OZ;"
    raise ValueError("Unsupported jog axis: {}".format(axis))
