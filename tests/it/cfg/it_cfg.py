#!/usr/bin/env python3


import os
import pytest
from src.cfg import Configuration
from os.path import expanduser


# default config files
PROGRAM_DIR = "/repo"
INSTALL_DIR_NAME = "AppData"
DEFAULT_SETTINGS_PATH = os.path.abspath(
    PROGRAM_DIR + "/" + INSTALL_DIR_NAME + "/cfg/conf.ini"
)
# local config files
MAIN_DIR = expanduser("~") + "/" + INSTALL_DIR_NAME
CONFIGURATION_DIR = MAIN_DIR + "/cfg"
SETTINGS_PATH = CONFIGURATION_DIR + "/conf.ini"


def test_check_if_user_config_exists():
    assert os.path.exists(SETTINGS_PATH)


def test_check_autou_pdate_value_match():
    def_data = Configuration.get(key="auto_update", section="GENERAL")
    assert def_data == True


def test_overwrite_default_value():
    init_value = str(456258)
    Configuration.set(value=init_value, key="pin", section="USER")
    get_val = Configuration.get(key="pin", section="USER")
    assert init_value == get_val


def test_remove_behavior():
    if os.path.exists(SETTINGS_PATH):
        os.remove(SETTINGS_PATH)
    def_data = Configuration.get(key="auto_update", section="GENERAL")

    # assert os.path.exists(SETTINGS_PATH)
