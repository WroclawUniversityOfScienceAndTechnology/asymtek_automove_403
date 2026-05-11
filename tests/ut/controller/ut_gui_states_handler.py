from src.controller.gui_states_handler import GuiStates, GuiStatesHandler


class MachineDispatcherSpy:
    def __init__(self):
        self.started_payload = None
        self.sent_payload = None
        self.jog_payload = None
        self.paused_task_id = None
        self.resumed_task_id = None
        self.stopped_task_id = None
        self.progress = None

    def start_program(self, payload):
        self.started_payload = payload
        return "task-1"

    def get_task_progress(self, task_id):
        self.progress = {"task_id": task_id, "done": True, "line_index": 2}
        return self.progress

    def send_current_command(self, payload):
        self.sent_payload = payload
        return "command-task-1"

    def jog(self, payload):
        self.jog_payload = payload
        return "jog-task-1"

    def pause_program(self, task_id):
        self.paused_task_id = task_id
        return task_id

    def resume_program(self, task_id):
        self.resumed_task_id = task_id
        return task_id

    def stop_program(self, task_id):
        self.stopped_task_id = task_id
        return task_id


def test_machine_event_is_not_dispatched_when_payload_is_simulated():
    handler = GuiStatesHandler(state_machine=None, canvas=None)
    handler.machine_dispatcher = MachineDispatcherSpy()

    handler._handle_machine_event(  # pylint: disable=protected-access
        "start_process",
        {"simulation_mode": True, "execution_lines": ["MA 0, 0;"]},
    )

    assert handler.machine_dispatcher.started_payload is None


def test_machine_event_is_dispatched_when_payload_targets_machine():
    handler = GuiStatesHandler(state_machine=None, canvas=None)
    handler.machine_dispatcher = MachineDispatcherSpy()
    payload = {"simulation_mode": False, "execution_lines": ["MA 0, 0;"]}

    handler._handle_machine_event("start_process", payload)  # pylint: disable=protected-access

    assert handler.machine_dispatcher.started_payload == payload
    assert handler._machine_task_id == "task-1"  # pylint: disable=protected-access


def test_z_jog_ui_event_is_dispatched_to_machine():
    handler = GuiStatesHandler(state_machine=None, canvas=None)
    handler.machine_dispatcher = MachineDispatcherSpy()
    payload = {"axis": "Z", "distance_mm": 1.0}

    handler._handle_manager_options("machine_jog_z_plus", payload)  # pylint: disable=protected-access

    assert handler.machine_dispatcher.jog_payload == payload
    assert handler._machine_task_id == "jog-task-1"  # pylint: disable=protected-access


def test_single_command_event_starts_progress_polling():
    handler = GuiStatesHandler(state_machine=None, canvas=None)
    handler.machine_dispatcher = MachineDispatcherSpy()
    payload = {"command": "MA 0, 0;"}

    handler._handle_machine_event("step_line", payload)  # pylint: disable=protected-access

    assert handler.machine_dispatcher.sent_payload == payload
    assert handler._machine_task_id == "command-task-1"  # pylint: disable=protected-access


def test_start_from_line_runs_program_from_selected_line():
    handler = GuiStatesHandler(state_machine=None, canvas=None)
    handler.machine_dispatcher = MachineDispatcherSpy()
    payload = {"command": "CMD2", "execution_lines": ["CMD0", "CMD1", "CMD2"], "line_index": 2}

    handler._handle_machine_event("start_from_line", payload)  # pylint: disable=protected-access

    assert handler.machine_dispatcher.started_payload == payload
    assert handler._machine_task_id == "task-1"  # pylint: disable=protected-access


def test_pause_stop_and_resume_control_existing_program_task():
    handler = GuiStatesHandler(state_machine=None, canvas=None)
    handler.machine_dispatcher = MachineDispatcherSpy()
    handler._machine_task_id = "task-1"  # pylint: disable=protected-access

    handler._handle_machine_event("pause_process", {})  # pylint: disable=protected-access
    handler._handle_machine_event("start_process", {"execution_lines": ["CMD0"]})  # pylint: disable=protected-access
    handler._handle_machine_event("stop_process", {})  # pylint: disable=protected-access

    assert handler.machine_dispatcher.paused_task_id == "task-1"
    assert handler.machine_dispatcher.resumed_task_id == "task-1"
    assert handler.machine_dispatcher.stopped_task_id == "task-1"
    assert handler.machine_dispatcher.started_payload is None


def test_machine_progress_poll_updates_engine_room_page():
    class PageSpy:
        def __init__(self):
            self.progress = None

        def apply_machine_progress(self, progress):
            self.progress = progress

    handler = GuiStatesHandler(state_machine=None, canvas=None)
    handler.machine_dispatcher = MachineDispatcherSpy()
    page = PageSpy()
    handler.pages[GuiStates.ENGINE_ROOM_STATE] = page
    handler._machine_task_id = "task-1"  # pylint: disable=protected-access

    handler._poll_machine_progress()  # pylint: disable=protected-access

    assert page.progress == {"task_id": "task-1", "done": True, "line_index": 2}
    assert handler._machine_task_id is None  # pylint: disable=protected-access
