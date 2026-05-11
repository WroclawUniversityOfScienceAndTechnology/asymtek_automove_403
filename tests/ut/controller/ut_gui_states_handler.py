from src.controller.gui_states_handler import GuiStates, GuiStatesHandler


class MachineDispatcherSpy:
    def __init__(self):
        self.started_payload = None
        self.sent_payload = None
        self.jog_payload = None
        self.progress = None

    def start_program(self, payload):
        self.started_payload = payload
        return "task-1"

    def get_task_progress(self, task_id):
        self.progress = {"task_id": task_id, "done": True, "line_index": 2}
        return self.progress

    def send_current_command(self, payload):
        self.sent_payload = payload

    def jog(self, payload):
        self.jog_payload = payload


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
