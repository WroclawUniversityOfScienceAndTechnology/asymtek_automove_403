from pathlib import Path
from types import SimpleNamespace

import pytest

from src.backend.machine_management import (
    DISPENSE_LARGE_PAD_AREA_MM2,
    DISPENSE_SMALL_PAD_AREA_MM2,
    _gerber_dispense_operations,
    calculate_dispense_time,
    generate_acl_from_layer,
)
from src.business_logic.models.engine_room_model import EngineRoomModel
from src.cfg import Configuration, ConfigVerificator
from src.cfg.config_files_helper import ConfigFileHelper
from src.cfg.config_wrapper import ConfigWrapper


class RectangleAperture:
    def __init__(self, width, height):
        self.w, self.h = width, height


class CircleAperture:
    diameter = 0.5


class Flash:
    x, y = 1, 2

    def __init__(self, width, height):
        self.aperture = RectangleAperture(width, height)


class Region:
    outline = [(0, 0), (1.45, 0), (1.45, 0.90), (0, 0.90), (0, 0)]


class Line:
    x1, y1, x2, y2 = 0, 0, 2, 0
    aperture = CircleAperture()


@pytest.mark.parametrize("area", [0, 0.01, DISPENSE_SMALL_PAD_AREA_MM2 / 2, DISPENSE_SMALL_PAD_AREA_MM2])
def test_small_pad_timing_is_unchanged(area):
    assert calculate_dispense_time(area, {"TIME_PER_SQMM": 0.5}) == pytest.approx(area * 0.5)


def test_reference_0805_pad_gets_three_times_previous_duration():
    assert DISPENSE_SMALL_PAD_AREA_MM2 == pytest.approx(0.063)
    assert DISPENSE_LARGE_PAD_AREA_MM2 == pytest.approx(1.305)
    duration = calculate_dispense_time(DISPENSE_LARGE_PAD_AREA_MM2, {"TIME_PER_SQMM": 0.5})
    assert duration == pytest.approx(DISPENSE_LARGE_PAD_AREA_MM2 * 0.5 * 3)


def test_intermediate_pad_uses_progressive_nonlinear_duration():
    midpoint = (DISPENSE_SMALL_PAD_AREA_MM2 + DISPENSE_LARGE_PAD_AREA_MM2) / 2
    assert calculate_dispense_time(midpoint) == pytest.approx(midpoint * 2)
    lower = (DISPENSE_SMALL_PAD_AREA_MM2 + midpoint) / 2
    upper = (midpoint + DISPENSE_LARGE_PAD_AREA_MM2) / 2
    assert calculate_dispense_time(upper) - calculate_dispense_time(midpoint) > (
        calculate_dispense_time(midpoint) - calculate_dispense_time(lower)
    )


@pytest.mark.parametrize("area", [0.01, 0.063, 0.5, 1.305, 10, 100])
def test_multiplier_one_restores_linear_timing(area):
    assert calculate_dispense_time(area, {"TIME_PER_SQMM": 0.75, "DISPENSE_LARGE_PAD_MULTIPLIER": 1}) == pytest.approx(area * 0.75)


def test_large_pad_boost_is_bounded_and_adjustable():
    settings = {"DISPENSE_LARGE_PAD_MULTIPLIER": 2.5}
    assert calculate_dispense_time(10, settings) == pytest.approx(25)
    assert calculate_dispense_time(DISPENSE_LARGE_PAD_AREA_MM2, settings) == pytest.approx(DISPENSE_LARGE_PAD_AREA_MM2 * 2.5)


@pytest.mark.parametrize("area", [True, -1, float("nan"), float("inf"), "1.0"])
def test_invalid_pad_area_is_rejected(area):
    with pytest.raises(ValueError, match="Pad area"):
        calculate_dispense_time(area)


@pytest.mark.parametrize("boost", [0, 0.5, float("nan"), float("inf")])
def test_invalid_boost_is_rejected(boost):
    assert not ConfigVerificator.verify("DISPENSE_LARGE_PAD_MULTIPLIER", boost)
    with pytest.raises(ValueError, match="DISPENSE_LARGE_PAD_MULTIPLIER"):
        calculate_dispense_time(1, {"DISPENSE_LARGE_PAD_MULTIPLIER": boost})


@pytest.mark.parametrize("rate", [0, -1, float("nan"), float("inf")])
def test_invalid_rate_is_rejected(rate):
    with pytest.raises(ValueError, match="TIME_PER_SQMM"):
        calculate_dispense_time(1, {"TIME_PER_SQMM": rate})


@pytest.mark.parametrize("operation", [Flash(0.90, 1.45), Region(), Line()])
def test_generated_dwell_applies_curve_to_flashes_regions_and_strokes(operation):
    layer = SimpleNamespace(objects=[operation])
    area = _gerber_dispense_operations(layer)[0][2]
    expected_time = calculate_dispense_time(area)

    commands = generate_acl_from_layer(layer)

    assert "WA {:.3f};".format(expected_time) in commands
    assert expected_time > area


def test_timing_boost_does_not_change_xy_or_nozzle_height():
    layer = SimpleNamespace(objects=[Flash(0.90, 1.45)])
    linear = generate_acl_from_layer(layer, {"DISPENSE_LARGE_PAD_MULTIPLIER": 1})
    nonlinear = generate_acl_from_layer(layer, {"DISPENSE_LARGE_PAD_MULTIPLIER": 3})

    assert [line for line in linear if not line.startswith("WA ")] == [
        line for line in nonlinear if not line.startswith("WA ")
    ]
    assert "WA 1.305;" in linear
    assert "WA 3.915;" in nonlinear


def test_existing_config_gets_default_boost_and_preserves_operator_changes(monkeypatch, tmp_path):
    settings_path = tmp_path / "conf.ini"
    text = Path(ConfigFileHelper.DEFAULT_SETTINGS_PATH).read_text()
    settings_path.write_text(text.replace("DISPENSE_LARGE_PAD_MULTIPLIER = 3.0\n", ""))
    monkeypatch.setattr(ConfigFileHelper, "SETTINGS_PATH", str(settings_path))

    assert EngineRoomModel.get_machine_settings()["DISPENSE_LARGE_PAD_MULTIPLIER"] == 3
    ConfigWrapper.update_settings(str(settings_path), ConfigFileHelper.DEFAULT_SETTINGS_PATH)
    Configuration.check_config()
    Configuration.set("DISPENSE_LARGE_PAD_MULTIPLIER", 2)
    ConfigWrapper.update_settings(str(settings_path), ConfigFileHelper.DEFAULT_SETTINGS_PATH)
    settings = EngineRoomModel.get_machine_settings()

    assert settings["DISPENSE_LARGE_PAD_MULTIPLIER"] == 2
    assert calculate_dispense_time(DISPENSE_LARGE_PAD_AREA_MM2, settings) == pytest.approx(DISPENSE_LARGE_PAD_AREA_MM2 * 2)
