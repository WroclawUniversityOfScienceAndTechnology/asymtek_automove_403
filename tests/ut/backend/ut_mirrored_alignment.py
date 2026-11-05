import math
from types import SimpleNamespace

import pytest

from src.backend.machine_management import (
    fit_fiducial_transform,
    generate_acl_from_layer,
    map_gerber_point,
    mirror_gerber_point,
    parse_acl_toolpath,
)


class RectangleAperture:
    w = 1
    h = 1


class Flash:
    aperture = RectangleAperture()

    def __init__(self, x, y):
        self.x = x
        self.y = y


def _dispense_coordinates(layer, **kwargs):
    commands = generate_acl_from_layer(layer, settings={"STEPSXY_PER_MM": 100}, **kwargs)
    points = parse_acl_toolpath(commands, settings={"STEPSXY_PER_MM": 100})
    return commands, [(point.x_mm, point.y_mm) for point in points if point.dispensing]


def _placed_point(x, y, angle, shift_x, shift_y, mirrored):
    x = -x if mirrored else x
    return (
        math.cos(angle) * x - math.sin(angle) * y + shift_x,
        math.sin(angle) * x + math.cos(angle) * y + shift_y,
    )


def test_mirror_keeps_holder_zero_fixed():
    assert mirror_gerber_point(0, 0, mirror_x=True) == (0, 0)
    assert mirror_gerber_point(12.5, 30.25, mirror_x=True) == (-12.5, 30.25)
    assert mirror_gerber_point(12.5, 30.25, mirror_x=False) == (12.5, 30.25)


def test_mirrored_pad_coordinates_do_not_depend_on_layer_extents():
    layer = SimpleNamespace(objects=[Flash(20, 10), Flash(40, 15)])
    _commands, before = _dispense_coordinates(layer, mirror_x=True)
    layer.objects.append(Flash(300, 200))
    commands, after = _dispense_coordinates(layer, mirror_x=True)

    assert before == [(-20, 10), (-40, 15)]
    assert after[:2] == before
    assert after[2] == (-300, 200)
    assert all("SO" not in command for command in commands)


@pytest.mark.parametrize("mirrored", [False, True])
@pytest.mark.parametrize("angle", [0, math.radians(3.2), math.radians(-1.5)])
def test_two_fiducials_align_pads_in_holder_frame(mirrored, angle):
    shift_x, shift_y = 110, 6
    fiducials = []
    for x, y in [(20, 10), (80, 40)]:
        source_x, source_y = mirror_gerber_point(x, y, mirror_x=mirrored)
        measured_x, measured_y = _placed_point(x, y, angle, shift_x, shift_y, mirrored)
        fiducials.append({"x": source_x, "y": source_y, "machine_x": measured_x, "machine_y": measured_y})
    transform = fit_fiducial_transform(fiducials)
    layer = SimpleNamespace(objects=[Flash(30, 18), Flash(70, 25)])

    commands, pads = _dispense_coordinates(layer, mirror_x=mirrored, xy_transform=transform)

    assert transform["angle_rad"] == pytest.approx(angle)
    assert transform["offset_x_mm"] == pytest.approx(shift_x)
    assert transform["offset_y_mm"] == pytest.approx(shift_y)
    for pad, (x, y) in zip(pads, [(30, 18), (70, 25)]):
        expected = _placed_point(x, y, angle, shift_x, shift_y, mirrored)
        assert pad == pytest.approx(expected, abs=2e-5)
        assert map_gerber_point("unused.gbr", x, y, xy_transform=transform, mirror_x=mirrored) == pytest.approx(expected)
    points = parse_acl_toolpath(commands, settings={"STEPSXY_PER_MM": 100})
    assert (points[-1].x_mm, points[-1].y_mm) == pytest.approx((0, 0), abs=2e-5)
    assert all("SO" not in command for command in commands)


def test_mirrored_bed_correction_uses_measured_holder_coordinates():
    layer = SimpleNamespace(objects=[Flash(2, 1)])
    settings = {
        "STEPSXY_PER_MM": 10,
        "STEPSZ_PER_MM": 10,
        "Z_SAFE_HEIGHT": 5,
        "Z_OFFSET_PER_SEC": 0,
        "Z_BED_POINTS": [
            {"x": x, "y": y, "z_steps": 2 * x + 3 * y}
            for x, y in [(0, 0), (10, 0), (0, 10), (10, 10)]
        ],
    }
    transform = {"angle_rad": 0, "offset_x_mm": 10, "offset_y_mm": 2}

    commands = generate_acl_from_layer(layer, settings=settings, xy_transform=transform, mirror_x=True)

    # Pad (2, 1) lands at holder (8, 3): correction = 25 steps, safe Z = -50.
    assert "MA 80.000, 30.000;" in commands
    assert "MZ 75.000; OA; OZ;" in commands
