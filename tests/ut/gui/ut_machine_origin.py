from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.business_logic.models.engine_room_model import EngineRoomModel
from src.cfg import Configuration
from src.cfg.config_files_helper import ConfigFileHelper
from src.gui.view.engine_room_page import EngineRoomPage


@pytest.fixture
def origin_page(monkeypatch, tmp_path):
    settings_path = tmp_path / "conf.ini"
    settings_path.write_text(Path(ConfigFileHelper.DEFAULT_SETTINGS_PATH).read_text())
    monkeypatch.setattr(ConfigFileHelper, "SETTINGS_PATH", str(settings_path))
    monkeypatch.setattr("src.gui.view.engine_room_page.get_serial_preflight_error", lambda settings: None)
    page = object.__new__(EngineRoomPage)
    page.subject = SimpleNamespace(dispose=lambda: None)
    page.finish = lambda: None
    page._render = lambda: None
    page._refresh_execution_progress = lambda: None
    page.machine_settings = EngineRoomModel.get_machine_settings()
    page.machine_settings.update({"STEPSXY_PER_MM": 100, "STEPSZ_PER_MM": 10})
    page._read_machine_settings = lambda **kwargs: page.machine_settings.copy()
    page.machine_position = {"X": None, "Y": None, "Z": None}
    page.machine_status = "Idle"
    page.simulation_mode = False
    page.execution_lines = []
    page._calibration_move_callback = None
    page._program_origin_dialog = None
    page.events = []
    page._emit = lambda name, payload: page.events.append((name, payload))
    return page


def _complete(page, status="sent", position=None, **kwargs):
    page.apply_machine_progress({"done": True, "status": status, "machine_position": position, **kwargs})


def test_set_origin_captures_absolute_position_and_persists_after_machine_reply(origin_page):
    page = origin_page
    page._set_origin(None)

    assert page.events[-1][1]["command"] == "OA; OZ;"
    _complete(page, position={"x": 12.5, "y": 30.25, "z": 5})

    assert page.events[-1][1]["command"] == "SO 1250, 3025; OA; OZ;"
    assert Configuration.get("MACHINE_ORIGIN") == {"x": 0.0, "y": 0.0}
    _complete(page, position={"x": 12.5, "y": 30.25, "z": 5})

    assert EngineRoomModel.get_machine_settings()["MACHINE_ORIGIN"] == {"x": 12.5, "y": 30.25}
    assert page.machine_settings["MACHINE_ORIGIN"] == {"x": 12.5, "y": 30.25}
    assert page.machine_status == "Machine origin set and saved"


def test_machine_error_preserves_previous_saved_origin(origin_page):
    page = origin_page
    Configuration.set("MACHINE_ORIGIN", {"x": 1, "y": 2})
    page.machine_settings["MACHINE_ORIGIN"] = {"x": 1, "y": 2}
    completed = Mock()

    page._save_and_set_machine_origin({"x": 10, "y": 20}, page.machine_settings, completed)
    _complete(page, status="error", error="No response")

    assert Configuration.get("MACHINE_ORIGIN") == {"x": 1, "y": 2}
    assert page.machine_settings["MACHINE_ORIGIN"] == {"x": 1, "y": 2}
    completed.assert_called_once_with(False, "Origin failed: No response")


def test_local_save_error_is_reported(origin_page, monkeypatch):
    page = origin_page
    monkeypatch.setattr(Configuration, "set", Mock(side_effect=OSError("Disk full")))
    completed = Mock()
    page._save_and_set_machine_origin({"x": 10, "y": 20}, page.machine_settings, completed)
    _complete(page)

    completed.assert_called_once_with(False, "Machine origin set, but local save failed: Disk full")
    assert page.machine_settings["MACHINE_ORIGIN"] == {"x": 0, "y": 0}


def test_go_origin_restores_saved_origin_then_lifts_z_and_moves(origin_page):
    page = origin_page
    page.machine_settings["MACHINE_ORIGIN"] = {"x": 12.5, "y": 30.25}
    page._go_machine_origin(None)

    assert len(page.events) == 1
    assert page.events[0][1]["command"] == "SO 1250, 3025; OA; OZ;"
    _complete(page, position={"z": 8})

    assert page.events[1][1]["command"] == "MZ -50.000; MA 0, 0; OA; OZ;"
    _complete(page)
    assert page.machine_status == "At machine origin"


def test_go_origin_does_not_move_after_restore_failure(origin_page):
    page = origin_page
    page._go_machine_origin(None)
    _complete(page, status="error", error="ACL error")

    assert len(page.events) == 1
    assert page.machine_status == "Machine error: ACL error"


@pytest.mark.parametrize("position", [{}, {"z": None}, {"z": float("nan")}])
def test_go_origin_requires_valid_z_before_moving(origin_page, position):
    page = origin_page
    page._go_machine_origin(None)
    _complete(page, position=position)

    assert len(page.events) == 1
    assert page.machine_status == "Origin move failed: Z unavailable"


@pytest.mark.parametrize("origin", [{"x": float("nan"), "y": 0}, {"x": -1, "y": 0}, {"x": 0, "y": 400}])
def test_invalid_origin_is_not_sent_or_saved(origin_page, origin):
    page = origin_page
    page._save_and_set_machine_origin(origin, page.machine_settings)

    assert page.events == []
    assert Configuration.get("MACHINE_ORIGIN") == {"x": 0, "y": 0}
    assert page.machine_status.startswith("Origin failed:")


@pytest.mark.parametrize("action", ["_set_origin", "_go_machine_origin"])
def test_origin_buttons_do_not_send_machine_commands_in_simulation(origin_page, action):
    page = origin_page
    page.simulation_mode = True
    getattr(page, action)(None)

    assert page.events == []
    assert Configuration.get("MACHINE_ORIGIN") == {"x": 0, "y": 0}


def _open_popup(page, monkeypatch):
    class Variable:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    def widget(*args, **kwargs):
        instance = Mock()
        instance.winfo_width.return_value = 600
        instance.winfo_height.return_value = 200
        return instance

    parent = Mock()
    parent.winfo_width.return_value = 800
    parent.winfo_height.return_value = 600
    parent.winfo_rootx.return_value = 0
    parent.winfo_rooty.return_value = 0
    entries, buttons = [], {}
    monkeypatch.setattr("src.gui.view.engine_room_page.tk.StringVar", Variable)
    monkeypatch.setattr("src.gui.view.engine_room_page.tk.Toplevel", widget)
    for kind in ("Frame", "Label"):
        monkeypatch.setattr("src.gui.view.engine_room_page.ttk." + kind, widget)

    def entry(*args, **kwargs):
        entries.append(kwargs["textvariable"])
        return widget()

    def button(*args, **kwargs):
        buttons[kwargs["text"]] = kwargs["command"]
        return widget()

    monkeypatch.setattr("src.gui.view.engine_room_page.ttk.Entry", entry)
    monkeypatch.setattr("src.gui.view.engine_room_page.ttk.Button", button)
    page.open_program_origin_dialog(parent=parent)
    return entries, buttons


def test_popup_loads_saved_origin_and_saves_manual_edits_without_gerber(origin_page, monkeypatch):
    page = origin_page
    Configuration.set("MACHINE_ORIGIN", {"x": 1.25, "y": 2.5})
    page.machine_settings = EngineRoomModel.get_machine_settings()
    page.machine_settings["STEPSXY_PER_MM"] = 100
    entries, buttons = _open_popup(page, monkeypatch)

    assert [entry.get() for entry in entries] == ["1.25", "2.5"]
    assert set(buttons) == {"Save and send to machine", "Close"}
    entries[0].set("12,5")
    entries[1].set("30.25")
    buttons["Save and send to machine"]()

    assert page.events[-1][1]["command"] == "SO 1250, 3025; OA; OZ;"
    buttons["Save and send to machine"]()
    assert len(page.events) == 1
    _complete(page)
    assert Configuration.get("MACHINE_ORIGIN") == {"x": 12.5, "y": 30.25}
    buttons["Close"]()

    entries, _buttons = _open_popup(page, monkeypatch)
    assert [entry.get() for entry in entries] == ["12.5", "30.25"]


def test_closing_popup_while_sending_still_persists_origin(origin_page, monkeypatch):
    page = origin_page
    entries, buttons = _open_popup(page, monkeypatch)
    entries[0].set("10")
    entries[1].set("20")
    buttons["Save and send to machine"]()
    buttons["Close"]()
    _complete(page)

    assert Configuration.get("MACHINE_ORIGIN") == {"x": 10, "y": 20}
