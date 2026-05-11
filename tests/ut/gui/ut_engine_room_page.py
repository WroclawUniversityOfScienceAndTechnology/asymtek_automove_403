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
    page.machine_progress = {}
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
