from src.gui.view.engine_room_page import EngineRoomPage


class _Disposable:
    def dispose(self):
        pass


def _page_shell():
    page = object.__new__(EngineRoomPage)
    page.subject = _Disposable()
    page.canvas_items = []
    page._embedded_widgets = []
    page._serial_settings_dialog = None
    page._simulation_after_id = None
    page.active_file = "No Gerber loaded"
    page.machine_progress = {}
    page.machine_position = {"X": None, "Y": None, "Z": None}
    page.machine_settings = {}
    EngineRoomPage._clear_dynamic_render_refs(page)  # pylint: disable=protected-access
    return page


def _simulation_page(status, current_line):
    page = _page_shell()
    page.simulation_mode = True
    page.machine_status = status
    page.current_line = current_line
    page.started_from = None

    page._can_send_to_machine = lambda: True  # pylint: disable=protected-access
    page._start_simulation = lambda start_index: setattr(
        page, "started_from", start_index
    )  # pylint: disable=protected-access
    page._current_command_payload = lambda: {"line_index": page.current_line}  # pylint: disable=protected-access
    return page


def test_start_process_resumes_paused_simulation_from_current_line():
    page = _simulation_page(status="Paused", current_line=4)

    payload = EngineRoomPage._start_process(page, None)  # pylint: disable=protected-access

    assert page.started_from == 4
    assert payload == {"line_index": 4}


def test_start_process_starts_new_simulation_from_first_line():
    page = _simulation_page(status="Ready", current_line=4)

    EngineRoomPage._start_process(page, None)  # pylint: disable=protected-access

    assert page.started_from == 0


def test_apply_machine_progress_correlates_frontend_by_line_index():
    page = _page_shell()
    page.execution_lines = ["CMD0", "CMD1", "CMD2", "CMD3"]
    page.current_line = 0
    page.selected_line = 0
    page.progress_percent = 0
    page.machine_status = "Running"
    page._render = lambda: None  # pylint: disable=protected-access

    page.apply_machine_progress(
        {
            "task_id": "task-1",
            "state": "PROGRESS",
            "status": "sending",
            "line_index": 2,
            "command": "CMD2",
            "sent_count": 3,
            "total_count": 4,
        }
    )

    assert page.current_line == 2
    assert page.selected_line == 2
    assert page.progress_percent == 66
    assert page.machine_status == "Sending"
    assert page._machine_progress_summary() == "Machine report: PROGRESS line 3 sent 3/4"


def test_simulation_tick_refreshes_existing_widgets_without_full_render():
    page = _page_shell()
    page.execution_lines = ["CMD0", "CMD1", "CMD2"]
    page.machine_status = "Simulating"
    page.current_line = 0
    page.selected_line = 0
    page.progress_percent = 0
    refreshed = []
    scheduled = []
    page._render = lambda: (_ for _ in ()).throw(AssertionError("full render should not run"))
    page._refresh_execution_progress = lambda: refreshed.append(page.current_line)
    page._schedule_simulation_tick = lambda: scheduled.append(True)

    EngineRoomPage._simulation_tick(page)  # pylint: disable=protected-access

    assert page.current_line == 1
    assert page.selected_line == 1
    assert page.progress_percent == 50
    assert refreshed == [1]
    assert scheduled == [True]


def test_process_setup_panel_adds_z_jog_buttons():
    page = _page_shell()
    page.default_font = ""
    page.machine_setting_fields = []
    page.machine_settings = {"jog_distance_mm": 1.0}
    page._machine_setting_entries = {}  # pylint: disable=protected-access
    buttons = []

    page._panel = lambda *args, **kwargs: None  # pylint: disable=protected-access
    page._text = lambda *args, **kwargs: None  # pylint: disable=protected-access
    page._rect = lambda *args, **kwargs: None  # pylint: disable=protected-access
    page._entry = lambda *args, **kwargs: None  # pylint: disable=protected-access
    page._jog = lambda axis, direction: {"axis": axis, "direction": direction}  # pylint: disable=protected-access

    def record_button(x, y, width, height, text, event_name, **kwargs):
        buttons.append(
            {
                "text": text,
                "event_name": event_name,
                "callback": kwargs["callback"],
            }
        )

    page._button = record_button  # pylint: disable=protected-access

    EngineRoomPage._add_process_setup_panel(page)  # pylint: disable=protected-access

    z_plus = next(button for button in buttons if button["event_name"] == "machine_jog_z_plus")
    z_minus = next(button for button in buttons if button["event_name"] == "machine_jog_z_minus")
    assert z_plus["text"] == "Z+"
    assert z_plus["callback"](None) == {"axis": "Z", "direction": 1}
    assert z_minus["text"] == "Z-"
    assert z_minus["callback"](None) == {"axis": "Z", "direction": -1}


def test_z_jog_payload_uses_configured_distance():
    page = _page_shell()
    page.simulation_mode = True
    page.machine_status = "Ready"
    page.machine_settings = {"jog_distance_mm": 1.25}
    page._machine_setting_entries = {}  # pylint: disable=protected-access
    page._render = lambda: None  # pylint: disable=protected-access

    payload = EngineRoomPage._jog(page, "Z", -1)  # pylint: disable=protected-access

    assert payload == {
        "axis": "Z",
        "distance_mm": -1.25,
        "settings": {"jog_distance_mm": 1.25},
        "simulation_mode": True,
    }


def test_process_setup_panel_adds_machine_position_row():
    page = _page_shell()
    page.default_font = ""
    page.machine_setting_fields = []
    page.machine_settings = {"jog_distance_mm": 1.0}
    page.machine_position = {"X": 1.2345, "Y": -2, "Z": None}
    page._machine_setting_entries = {}  # pylint: disable=protected-access
    text_values = []

    def record_text(x, y, text, **kwargs):
        text_values.append(text)
        return "text-{}".format(len(text_values))

    page._panel = lambda *args, **kwargs: None  # pylint: disable=protected-access
    page._text = record_text  # pylint: disable=protected-access
    page._rect = lambda *args, **kwargs: None  # pylint: disable=protected-access
    page._entry = lambda *args, **kwargs: None  # pylint: disable=protected-access
    page._button = lambda *args, **kwargs: None  # pylint: disable=protected-access

    EngineRoomPage._add_process_setup_panel(page)  # pylint: disable=protected-access

    assert "Current position" in text_values
    assert "1.234" in text_values
    assert "-2.000" in text_values
    assert "--" in text_values


def test_apply_machine_progress_updates_machine_position_from_json():
    page = _page_shell()
    page.execution_lines = []
    page.current_line = 0
    page.selected_line = 0
    page.progress_percent = 0
    page.machine_status = "Running"
    refreshed = []
    page._refresh_execution_progress = lambda: refreshed.append(True)  # pylint: disable=protected-access

    page.apply_machine_progress(
        {
            "state": "PROGRESS",
            "status": "sending",
            "position": {"x": 10.125, "y": -3.5, "z": 0.25},
        }
    )

    assert page.machine_position == {"X": 10.125, "Y": -3.5, "Z": 0.25}
    assert refreshed == [True]


def test_apply_machine_progress_reflects_paused_and_stopped_status():
    page = _page_shell()
    page.execution_lines = ["CMD0", "CMD1", "CMD2"]
    page.current_line = 0
    page.selected_line = 0
    page.progress_percent = 0
    refreshed = []
    page._refresh_execution_progress = lambda: refreshed.append(page.machine_status)  # pylint: disable=protected-access

    page.apply_machine_progress({"status": "paused", "line_index": 1, "sent_count": 1, "total_count": 3})

    assert page.current_line == 1
    assert page.machine_status == "Paused"

    page.apply_machine_progress({"status": "stopped", "done": True, "line_index": 1, "sent_count": 1, "total_count": 3})

    assert page.current_line == 1
    assert page.machine_status == "Stopped"
    assert refreshed == ["Paused", "Stopped"]


def test_stop_process_keeps_machine_line_until_backend_reports_stop():
    page = _page_shell()
    page.simulation_mode = False
    page.execution_lines = ["CMD0", "CMD1", "CMD2"]
    page.current_line = 2
    page.selected_line = 2
    page.machine_status = "Running"
    page._cancel_simulation = lambda: None  # pylint: disable=protected-access
    page._refresh_execution_progress = lambda: None  # pylint: disable=protected-access

    payload = EngineRoomPage._stop_process(page, None)  # pylint: disable=protected-access

    assert page.machine_status == "Stopping"
    assert page.current_line == 2
    assert page.selected_line == 2
    assert payload["line_index"] == 2


def test_store_serial_settings_persists_user_config(monkeypatch):
    saved_values = []
    page = _page_shell()

    monkeypatch.setattr(
        "src.gui.view.engine_room_page.Configuration.set",
        staticmethod(lambda key, value, section="USER": saved_values.append((key, value, section))),
    )

    EngineRoomPage._store_serial_settings(page, "COM9", 57600)  # pylint: disable=protected-access

    assert saved_values == [
        ("SERIAL_PORT", "COM9", "USER"),
        ("BAUD_RATE", 57600, "USER"),
    ]
