#!/usr/bin/env python

# pylint: disable=C0114

from statemachine import StateMachine, State
from src.logger import Logger
from src.controller.gui_states_handler import GuiStatesHandler, GuiStates


class MainStateMachine(StateMachine):
    """
    Main state machine of the application
    """

    initial_state = State("init", initial=True)
    login_state = State("login")
    # manager states
    logged_state = State("logged")
    notifications_state = State("notifications")
    language_state = State("language")

    # init
    init = initial_state.to(logged_state)
    # login
    login = login_state.from_(initial_state, logged_state, login_state, notifications_state, language_state)

    logged = login_state.to(logged_state) | notifications_state.to(logged_state) | language_state.to(logged_state)
    notifications = logged_state.to(notifications_state) | language_state.to(notifications_state)
    language = logged_state.to(language_state) | notifications_state.to(language_state)

    def init_state_machine(self, canvas, **kwargs):
        """
        Initialize the state machine
        """
        img_dir = kwargs.get("img_dir", "")
        default_font = kwargs.get("default_font", "")
        scale = kwargs.get("scale", 1)
        # work-around - cannot be added to constructor with this state machine impl
        # pylint: disable=W0201
        self.gui_states_handler = GuiStatesHandler(
            self,
            canvas,
            img_dir=img_dir,
            default_font=default_font,
            scale=scale,
        )

    def set_scale(self, scale):
        self.gui_states_handler.set_scale(scale)

    def reload_current_view(self):
        self.gui_states_handler.reload_present_state()

    def open_serial_settings(self, parent=None):
        self.gui_states_handler.open_serial_settings(parent=parent)

    # states handle
    def on_init(self):
        """
        Initialize the program
        """
        Logger().log_debug("on_init")
        self.gui_states_handler.add_base_pages()
        # exceptional usage to automatically call first transition
        self.gui_states_handler.load(GuiStates.ENGINE_ROOM_STATE)

    def on_login(self):
        """
        Login state preparation
        """
        Logger().log_debug("on_login")
        self.gui_states_handler.load(GuiStates.ENGINE_ROOM_STATE)

    def on_logged(self):
        """
        Logged screen preparation
        if successfully verified show first screen after login
        """
        Logger().log_debug("on_logged")
        self.gui_states_handler.load(GuiStates.ENGINE_ROOM_STATE)

    def on_notifications(self):
        """
        Notification screen preparation
        """
        Logger().log_debug("on_notifications")
        self.gui_states_handler.load(GuiStates.NOTIFICATIONS_STATE)

    def on_language(self):
        """
        Language screen preparation
        """
        Logger().log_debug("on_language")
        self.gui_states_handler.load(GuiStates.LANGUAGE_STATE)
