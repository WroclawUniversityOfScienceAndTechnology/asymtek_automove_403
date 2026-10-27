#!/usr/bin/env python3

# pylint: disable=C0114

from enum import Enum, unique
from src.backend.machine_dispatcher import MachineTaskDispatcher
from src.logger import Logger
from src.gui.view import (
    LoginPage,
    EngineRoomPage,
    NotificationPage,
    LanguagePage,
)

# business logic - model
from src.business_logic import (
    Authenticator,
    LoginModel,
    EngineRoomModel,
    NotificationsModel,
    LanguageModel,
)


@unique
class GuiStates(Enum):
    """
    State in which gui can be in form of enum. Add all pages which can be swich
    in your app.
    It will be pass automatically when inherit from page_base - > Base class
    """

    LOGIN_STATE = 0x00
    ENGINE_ROOM_STATE = 0x01
    NOTIFICATIONS_STATE = 0x02
    LANGUAGE_STATE = 0x03


MACHINE_JOG_EVENTS = (
    "machine_jog_up",
    "machine_jog_down",
    "machine_jog_left",
    "machine_jog_right",
    "machine_jog_z_plus",
    "machine_jog_z_minus",
)


class GuiStatesHandler:
    """
    Part of the controller which handle gui events and update screens
    """

    def __init__(self, state_machine, canvas, **kwargs):
        self.pages = {}
        self.present_state = None
        self.new_state = None
        self.canvas = canvas
        self.img_dir = kwargs.get("img_dir", "")
        self.default_font = kwargs.get("default_font", "")
        self.scale = kwargs.get("scale", 1)
        self.state_machine = state_machine
        self.machine_dispatcher = MachineTaskDispatcher()
        self._machine_task_id = None
        self._xy_calibration_task_id = None
        self._machine_progress_after_id = None
        self._machine_progress_interval_ms = 250

    def add_base_pages(self):
        """
        Add pages to you application
        """
        # #login pages
        self.pages[GuiStates.LOGIN_STATE] = LoginPage(
            self.canvas,
            update_callback=self.callback_view,
            img_dir=self.img_dir,
            default_font=self.default_font,
            scale=self.scale,
        )
        # # main flow pages
        # manager panel
        self.pages[GuiStates.ENGINE_ROOM_STATE] = EngineRoomPage(
            self.canvas,
            update_callback=self.callback_view,
            img_dir=self.img_dir,
            default_font=self.default_font,
            scale=self.scale,
        )
        self.pages[GuiStates.NOTIFICATIONS_STATE] = NotificationPage(
            self.canvas,
            update_callback=self.callback_view,
            img_dir=self.img_dir,
            default_font=self.default_font,
            scale=self.scale,
        )
        self.pages[GuiStates.LANGUAGE_STATE] = LanguagePage(
            self.canvas,
            update_callback=self.callback_view,
            img_dir=self.img_dir,
            default_font=self.default_font,
            scale=self.scale,
        )

    def set_scale(self, scale):
        self.scale = scale
        self.canvas.ui_scale = scale

    def reload_present_state(self):
        if self.present_state is not None:
            self._update_view(self.present_state)

    def open_serial_settings(self, parent=None):
        page = self.pages.get(GuiStates.ENGINE_ROOM_STATE)
        if page is not None:
            page.open_serial_settings_dialog(parent=parent)

    def open_z_compensation(self, parent=None):
        page = self.pages.get(GuiStates.ENGINE_ROOM_STATE)
        if page is not None:
            page.open_z_compensation_dialog(parent=parent)

    def open_xy_fiducial_calibration(self, parent=None):
        page = self.pages.get(GuiStates.ENGINE_ROOM_STATE)
        if page is not None:
            page.open_xy_fiducial_calibration_dialog(parent=parent)

    def restore_default_machine_settings(self):
        settings = EngineRoomModel.restore_default_machine_settings()
        page = self.pages.get(GuiStates.ENGINE_ROOM_STATE)
        if page is not None and self.present_state == GuiStates.ENGINE_ROOM_STATE:
            page.apply_machine_settings(settings, status="Defaults restored")

    def _engine_room_page(self):
        return self.pages.get(GuiStates.ENGINE_ROOM_STATE)

    def load(self, state, **kwargs):
        """
        Load screen with model data is needed

        Args:
            state (GuiStates): one of defined View Pages states
        """
        if state == GuiStates.LOGIN_STATE:
            kwargs = LoginModel.get_model_data()
        elif state == GuiStates.ENGINE_ROOM_STATE:
            kwargs = EngineRoomModel.get_model_data()
        elif state == GuiStates.NOTIFICATIONS_STATE:
            kwargs = NotificationsModel.get_model_data()
        elif state == GuiStates.LANGUAGE_STATE:
            kwargs = LanguageModel.get_model_data()
        # elif state == GuiStates.LANGUAGE_STATE:
        #         kwargs = LanguageModel.get_model_data()

        # update view with appropriate data
        self._update_view(state, **kwargs)

    def callback_view(self, dictionary):
        """
        Update state base on callback
        """
        event_src = dictionary.get("event_src", 0)
        event_name = dictionary.get("event_name", 0)
        event = dictionary.get("event", 0)
        if isinstance(event, dict) and "execution_lines" in event:
            event = event.copy()
            event["execution_lines"] = "count={}".format(len(event["execution_lines"]))
        Logger().log_debug(str(event_src) + " " + str(event_name) + " " + str(event))
        self._ui_event_handle(dictionary)

    def _update_view(self, state, **kwargs):
        self.new_state = state
        kwargs["scale"] = self.scale
        if self.present_state is not None:
            self.pages[self.present_state].finish()

        self.pages[self.new_state].update(**kwargs)
        self.pages[self.new_state].rx_subscribe(next=self.callback_view)

        # update present_state base on new_state
        Logger().log_debug("present=" + str(self.present_state) + " , new=" + str(self.new_state))
        self.present_state = self.new_state

    def _try_login(self, **kwargs):
        """
        If successful set of secret, then go to first page after logout
        go to login page otherwise
        """
        secret = kwargs.get("event", "")
        if Authenticator.make_user_authentication(login="", secret=secret):
            # successfully login
            self.state_machine.logged()
        else:
            # unsuccessfully login
            self.state_machine.login()

    def _change_language(self, **kwargs):
        """
        Change program language translation
        """
        lang = kwargs.get("event")
        LoginModel.set_language(lang)
        self.load(self.present_state, **kwargs)

    def _global_event_handler(self, **kwargs):
        """
        Handle global event be event_name

        Returns:
            bool: True is event was handle here, False otherwise
        """
        event_name = kwargs.get("event_name", "")

        if event_name == "logout":
            self.state_machine.login()
        elif event_name == "change_language":
            self._change_language(**kwargs)
        elif event_name == "cancel":
            self.state_machine.logged()
        else:
            return False
        return True

    def _handle_machine_event(self, event_name, payload):
        payload = payload or {}
        if payload.get("simulation_mode"):
            Logger().log_info("Machine dispatch skipped for simulation event: " + event_name)
            return None
        if event_name == "start_process":
            if self._machine_task_id:
                self.machine_dispatcher.resume_program(self._machine_task_id)
                self._ensure_machine_progress_poll()
            else:
                task_id = self.machine_dispatcher.start_program(payload)
                self._start_machine_progress_poll(task_id)
        elif event_name == "start_from_line":
            task_id = self.machine_dispatcher.start_program(payload)
            self._start_machine_progress_poll(task_id)
        elif event_name == "step_line":
            task_id = self.machine_dispatcher.send_current_command(payload)
            self._start_machine_progress_poll(task_id)
        elif event_name == "pause_process":
            self.machine_dispatcher.pause_program(self._machine_task_id)
            self._ensure_machine_progress_poll()
        elif event_name == "stop_process":
            self.machine_dispatcher.stop_program(self._machine_task_id)
            self._ensure_machine_progress_poll()
        elif event_name in MACHINE_JOG_EVENTS:
            task_id = self.machine_dispatcher.jog(payload)
            self._start_machine_progress_poll(task_id)
        elif event_name == "machine_get_position":
            if not getattr(self, "_position_task_active", False):
                poll_task_id = self.machine_dispatcher.trigger_get_position(payload)
                if poll_task_id:
                    self._position_task_active = True
                    self._poll_single_position_task(poll_task_id)
        elif event_name == "calibration_command":
            task_id = self.machine_dispatcher.send_current_command(payload)
            page = self._engine_room_page()
            if page is not None and page.xy_calibration_active:
                self._xy_calibration_task_id = task_id
            self._start_machine_progress_poll(task_id)
        elif event_name == "nozzle_cleaning":
            task_id = self.machine_dispatcher.start_program(payload)
            self._start_machine_progress_poll(task_id)
        elif event_name == "machine_init":
            task_id = self.machine_dispatcher.init_machine(payload)
            self._start_machine_progress_poll(task_id)
        elif event_name == "machine_home":
            task_id = self.machine_dispatcher.home_machine(payload)
            self._start_machine_progress_poll(task_id)
        elif event_name == "set_origin":
            task_id = self.machine_dispatcher.set_origin(payload)
            self._start_machine_progress_poll(task_id)

    def _start_machine_progress_poll(self, task_id):
        self._cancel_machine_progress_poll()
        self._machine_task_id = task_id
        if task_id:
            self._schedule_machine_progress_poll()

    def _ensure_machine_progress_poll(self):
        if self._machine_task_id and self._machine_progress_after_id is None:
            self._schedule_machine_progress_poll()

    def _schedule_machine_progress_poll(self):
        if self.canvas is not None:
            self._machine_progress_after_id = self.canvas.after(
                self._machine_progress_interval_ms,
                self._poll_machine_progress,
            )

    def _cancel_machine_progress_poll(self):
        if self._machine_progress_after_id is None or self.canvas is None:
            self._machine_progress_after_id = None
            return
        try:
            self.canvas.after_cancel(self._machine_progress_after_id)
        except Exception:  # pylint: disable=W0718
            pass
        self._machine_progress_after_id = None

    def _poll_machine_progress(self):
        self._machine_progress_after_id = None
        if not self._machine_task_id:
            return

        polled_task_id = self._machine_task_id
        progress = self.machine_dispatcher.get_task_progress(polled_task_id)
        page = self._engine_room_page()
        if progress and page is not None:
            page.apply_machine_progress(progress)

        # Applying a completed task can synchronously dispatch the next calibration
        # move. Do not clear that new task when returning from the previous poll.
        if self._machine_task_id != polled_task_id:
            if self._machine_task_id and self._machine_progress_after_id is None:
                self._schedule_machine_progress_poll()
            return

        if progress and progress.get("done"):
            if self._xy_calibration_task_id == polled_task_id:
                self._xy_calibration_task_id = None
            self._machine_task_id = None
            return
        self._schedule_machine_progress_poll()

    def _poll_single_position_task(self, task_id):
        if not task_id:
            self._position_task_active = False
            return

        result = self.machine_dispatcher.get_task_progress(task_id)

        if result:
            if result.get("status") in ("error", "FAILURE", "poll_error"):
                Logger().log_warning(f"Zignorowano błąd odpytywania tła: {result.get('error', 'Unknown')}")
                self._position_task_active = False
                return

            page = self._engine_room_page()
            if page is not None and result.get("status") == "poll_success":
                page.apply_machine_progress(result)
            if result.get("done") or result.get("status") in ("poll_success", "success"):
                self._position_task_active = False
                return
        if self.canvas is None:
            self._position_task_active = False
            return
        self.canvas.after(500, lambda: self._poll_single_position_task(task_id))

    def _handle_manager_options(self, event_name, payload=None):
        if event_name == "engine_room":
            self.state_machine.logged()
        elif event_name == "notifications":
            self.state_machine.notifications()
        elif event_name == "language":
            self.state_machine.language()
        elif event_name in (
            "load_gerber",
            "save_program",
            "start_process",
            "pause_process",
            "stop_process",
            "start_from_line",
            "step_line",
            "extruder_minus",
            "extruder_plus",
            "machine_init",
            "machine_home",
            "set_origin",
            "calibration_command",
            "nozzle_cleaning",
            "machine_get_position",
            *MACHINE_JOG_EVENTS,
        ):
            Logger().log_info("Machine UI event: " + event_name)
            self._handle_machine_event(event_name, payload or {})

    # pylint: disable=R0912
    def _ui_event_handle(self, dictionary):
        """
        Handle rx events from the view pages

        Args:
            dictionary ([type]): [description]
        """
        event_name = dictionary.get("event_name", "")
        payload = dictionary.get("event", {})

        if self._global_event_handler(**dictionary):
            return

        if self.present_state == GuiStates.LOGIN_STATE:
            if event_name == "login_user":
                self._try_login(**dictionary)

        elif (
            self.present_state == GuiStates.ENGINE_ROOM_STATE
            or self.present_state == GuiStates.NOTIFICATIONS_STATE
            or self.present_state == GuiStates.LANGUAGE_STATE
        ):
            self._handle_manager_options(event_name, payload=payload)
