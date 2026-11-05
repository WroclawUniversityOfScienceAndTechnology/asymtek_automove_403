import math
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.backend.machine_management import parse_acl_toolpath
from src.business_logic.models.engine_room_model import EngineRoomModel
from src.cfg import Configuration
from src.cfg.config_files_helper import ConfigFileHelper
from src.gui.view.engine_room_page import EngineRoomPage


class Variable:
    def __init__(self, value=""):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class RectangleAperture:
    w = 1
    h = 1


class Flash:
    aperture = RectangleAperture()

    def __init__(self, x, y):
        self.x = x
        self.y = y


@pytest.fixture
def alignment_page(monkeypatch, tmp_path):
    settings_path = tmp_path / "conf.ini"
    settings_path.write_text(Path(ConfigFileHelper.DEFAULT_SETTINGS_PATH).read_text())
    monkeypatch.setattr(ConfigFileHelper, "SETTINGS_PATH", str(settings_path))
    Configuration.set("MACHINE_ORIGIN", {"x": 12.5, "y": 30.25})
    monkeypatch.setattr("src.gui.view.engine_room_page.get_serial_preflight_error", lambda settings: None)
    layer = SimpleNamespace(objects=[Flash(30, 18), Flash(70, 25)])
    monkeypatch.setattr("gerbonara.GerberFile.open", Mock(return_value=layer))
    page = object.__new__(EngineRoomPage)
    page.subject = SimpleNamespace(dispose=lambda: None)
    page.finish = lambda: None
    page._render = Mock()
    page._refresh_execution_progress = lambda: None
    page.machine_settings = EngineRoomModel.get_machine_settings()
    page.machine_settings.update({"STEPSXY_PER_MM": 100, "STEPSZ_PER_MM": 10})
    page._read_machine_settings = lambda **kwargs: page.machine_settings.copy()
    page.machine_position = {"X": None, "Y": None, "Z": None}
    page.machine_status = "Idle"
    page.simulation_mode = False
    page.execution_lines = []
    page.gerber_path = None
    page.gerber_mirrored = False
    page._gerber_mirror_var = Variable(False)
    page.xy_transform = None
    page.xy_calibration_active = False
    page._calibration_move_callback = None
    page._xy_fiducial_dialog = None
    page.events = []
    page._emit = lambda name, payload: page.events.append((name, payload))
    page._generate_gerber_program("board.gbr")
    return page, settings_path


def _set_mirror(page, mirrored):
    page._gerber_mirror_var.set(mirrored)
    page._toggle_gerber_mirror()


def _complete(page, position):
    page.apply_machine_progress({"done": True, "status": "sent", "machine_position": position})


def _open_calibration(page, monkeypatch):
    def widget(*args, **kwargs):
        instance = Mock()
        instance.winfo_width.return_value = 600
        instance.winfo_height.return_value = 300
        instance.winfo_exists.return_value = True
        return instance

    parent = widget()
    parent.winfo_rootx.return_value = 0
    parent.winfo_rooty.return_value = 0
    entries, buttons, labels = [], {}, []
    monkeypatch.setattr("src.gui.view.engine_room_page.tk.StringVar", Variable)
    monkeypatch.setattr("src.gui.view.engine_room_page.tk.Toplevel", widget)
    for kind in ("Frame", "Combobox"):
        monkeypatch.setattr("src.gui.view.engine_room_page.ttk." + kind, widget)

    def entry(*args, **kwargs):
        entries.append(kwargs["textvariable"])
        return widget()

    def button(*args, **kwargs):
        buttons[kwargs["text"]] = kwargs["command"]
        return widget()

    def label(*args, **kwargs):
        labels.append(kwargs)
        return widget()

    monkeypatch.setattr("src.gui.view.engine_room_page.ttk.Entry", entry)
    monkeypatch.setattr("src.gui.view.engine_room_page.ttk.Button", button)
    monkeypatch.setattr("src.gui.view.engine_room_page.ttk.Label", label)
    page.open_xy_fiducial_calibration_dialog(parent=parent)
    return entries, buttons, labels


@pytest.mark.parametrize("angle", [0, math.radians(2.5)])
def test_mirrored_two_fiducial_workflow_keeps_holder_origin(alignment_page, monkeypatch, angle):
    page, config_path = alignment_page
    original_config = config_path.read_text()
    _set_mirror(page, True)
    entries, buttons, _labels = _open_calibration(page, monkeypatch)

    for x, y in [(20, 10), (80, 40)]:
        entries[0].set(str(x))
        entries[1].set(str(y))
        buttons["Save fiducial"]()
        assert page.events[-1][1]["command"] == "OC; OZ;"
        machine_x = math.cos(angle) * -x - math.sin(angle) * y + 110
        machine_y = math.sin(angle) * -x + math.cos(angle) * y + 5
        _complete(page, {"x": machine_x, "y": machine_y, "z": 0})

    assert page.xy_transform["angle_rad"] == pytest.approx(angle)
    assert page.xy_transform["offset_x_mm"] == pytest.approx(110)
    assert page.xy_transform["offset_y_mm"] == pytest.approx(5)
    pads = [point for point in parse_acl_toolpath(page.execution_lines, page.machine_settings) if point.dispensing]
    for pad, (x, y) in zip(pads, [(30, 18), (70, 25)]):
        assert (pad.x_mm, pad.y_mm) == pytest.approx(
            (math.cos(angle) * -x - math.sin(angle) * y + 110,
             math.sin(angle) * -x + math.cos(angle) * y + 5), abs=2e-5
        )
    assert [payload["command"] for _name, payload in page.events] == ["OC; OZ;", "OC; OZ;"]
    assert page.machine_settings["MACHINE_ORIGIN"] == {"x": 12.5, "y": 30.25}
    assert Configuration.get("MACHINE_ORIGIN") == {"x": 12.5, "y": 30.25}
    assert config_path.read_text() == original_config
    assert page._can_send_to_machine()
    buttons["Save fiducial"]()
    assert len(page.events) == 2


def test_mirror_toggle_discards_previous_side_calibration(alignment_page):
    page, config_path = alignment_page
    original_config = config_path.read_text()
    page.xy_transform = {"angle_rad": 0, "offset_x_mm": 4, "offset_y_mm": 5}

    _set_mirror(page, True)

    assert page.xy_transform is None
    assert page.events == []
    page.xy_transform = {"angle_rad": 0, "offset_x_mm": 110, "offset_y_mm": 5}
    _set_mirror(page, False)
    assert page.xy_transform is None
    assert config_path.read_text() == original_config


def test_mirror_calibration_does_not_move_to_an_unknown_reflected_position(alignment_page, monkeypatch):
    page, _config_path = alignment_page
    _set_mirror(page, True)
    entries, buttons, _labels = _open_calibration(page, monkeypatch)
    entries[0].set("20")
    entries[1].set("10")

    buttons["Locate fiducial manually"]()

    assert page.events == []
    buttons["Save fiducial"]()
    assert page.events[-1][1]["command"] == "OC; OZ;"


def test_top_side_still_approaches_fiducial_with_safe_z_lift(alignment_page, monkeypatch):
    page, _config_path = alignment_page
    entries, buttons, _labels = _open_calibration(page, monkeypatch)
    entries[0].set("20")
    entries[1].set("10")

    buttons["Go to fiducial"]()
    assert page.events[-1][1]["command"] == "OC; OZ;"
    _complete(page, {"x": 1, "y": 2, "z": 0})

    assert page.events[-1][1]["command"] == "MZ -50.000; MA 2000.000, 1000.000;"


def test_mirrored_machine_execution_waits_for_fiducials(alignment_page):
    page, _config_path = alignment_page
    _set_mirror(page, True)

    assert not page._can_send_to_machine()
    assert page.machine_status == "Measure mirrored fiducials"
    page.simulation_mode = True
    assert page._can_send_to_machine()


def test_duplicate_fiducial_can_be_corrected_without_changing_origin(alignment_page, monkeypatch):
    page, config_path = alignment_page
    original_config = config_path.read_text()
    _set_mirror(page, True)
    entries, buttons, labels = _open_calibration(page, monkeypatch)
    for _ in range(2):
        entries[0].set("20")
        entries[1].set("10")
        buttons["Save fiducial"]()
        _complete(page, {"x": 90, "y": 15, "z": 0})

    assert page.xy_transform is None
    assert any("could not be calculated" in item["textvariable"].get()
               for item in labels if "textvariable" in item)
    entries[0].set("80")
    entries[1].set("40")
    buttons["Save fiducial"]()
    _complete(page, {"x": 30, "y": 45, "z": 0})

    assert page.xy_transform["offset_x_mm"] == pytest.approx(110)
    assert config_path.read_text() == original_config
