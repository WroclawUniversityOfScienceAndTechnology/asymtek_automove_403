#!/usr/bin/env python3


import pytest
from mock import patch

from src.cfg import Configuration
from src.controller import MainController
from src.gui.tk_framework import OkCancelDialog


@pytest.fixture(scope="module")
def app():
    """
    Set Configuration and pass control to MainController

    Yields:
        MainController: controller instance
    """
    app = MainController()
    yield app
    Configuration.reset_settings()


def test_check_if_in_init_state(app):
    """
    Test state of the state machine after init

    Args:
        app (MainController): fixture returning main controller
    """
    assert "logged_state" is app.main_state_machine.current_state.value


def test_full_screen(app):
    """
    Test if user full screen in present and set to TRUE

    Args:
        app (MainController): fixture returning main controller
    """
    Configuration.set("fullscreen_mode", True, section="GENERAL")
    assert Configuration.get("fullscreen_mode", section="GENERAL") is True


def test_kill_app(app):
    """
    Test kill signal send by controller

    Args:
        app (MainController): fixture returning main controller
    """
    with patch("src.controller.sys.exit") as exit_mock:
        app._quit_adv()
        assert exit_mock.called


def test_check_login_states(app):
    """
    Check if view consing apriopriage states

    Args:
        app (MainController): fixture returning main controller
    """
    assert "logged_state" is app.main_state_machine.current_state.value
    app.main_state_machine.login()
    assert "login_state" is app.main_state_machine.current_state.value
    app.main_state_machine.logged()
    assert "logged_state" is app.main_state_machine.current_state.value


def test_dialog_ok(app):
    dial_ok = OkCancelDialog(app.canvas, "ok", "test message")
