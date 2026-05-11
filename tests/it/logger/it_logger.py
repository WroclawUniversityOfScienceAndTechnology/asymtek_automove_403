#!/usr/bin/env python


import pytest
import os
from src.logger import Logger, LogLevel
from os.path import expanduser

LOG_DIR = "/repo/out/program.log"


@pytest.fixture(scope="function", autouse=True)
def _setup():
    if os.path.exists(LOG_DIR):
        os.remove(LOG_DIR)
    yield


def check_for_phrase(phrase):
    with open(LOG_DIR) as f:
        if phrase in f.read():
            return True
    return False


def test_log_critical():
    Logger().logger_init(
        LOG_DIR, LogLevel.LOG_CRITICAL.value, LogLevel.LOG_CRITICAL.value
    )
    Logger().log_critical("test critical")
    Logger().log_error("test error")
    assert os.path.exists(LOG_DIR)
    assert check_for_phrase("CRITICAL") is True
    assert check_for_phrase("ERROR") is False


def test_log_error():
    Logger().logger_init(LOG_DIR, LogLevel.LOG_ERROR.value, LogLevel.LOG_ERROR.value)
    Logger().log_critical("test critical")
    Logger().log_error("test error")
    Logger().log_warning("test warinng")
    assert os.path.exists(LOG_DIR)
    assert check_for_phrase("CRITICAL") is True
    assert check_for_phrase("ERROR") is True
    assert check_for_phrase("WARNING") is False


def test_log_warning():
    Logger().logger_init(
        LOG_DIR, LogLevel.LOG_WARNING.value, LogLevel.LOG_WARNING.value
    )
    Logger().log_critical("test critical")
    Logger().log_error("test error")
    Logger().log_warning("test warning")
    Logger().log_debug("test debug")
    assert os.path.exists(LOG_DIR)
    assert check_for_phrase("CRITICAL") is True
    assert check_for_phrase("ERROR") is True
    assert check_for_phrase("WARNING") is True
    assert check_for_phrase("INFO") is False


def test_log_info():
    Logger().logger_init(LOG_DIR, LogLevel.LOG_INFO.value, LogLevel.LOG_INFO.value)
    Logger().log_critical("test critical")
    Logger().log_error("test error")
    Logger().log_warning("test warning")
    Logger().log_info("test info")
    Logger().log_debug("test debug")
    assert os.path.exists(LOG_DIR)
    assert check_for_phrase("CRITICAL") is True
    assert check_for_phrase("ERROR") is True
    assert check_for_phrase("WARNING") is True
    assert check_for_phrase("INFO") is True
    assert check_for_phrase("DEBUG") is False


def test_log_debug():
    Logger().logger_init(LOG_DIR, LogLevel.LOG_DEBUG.value, LogLevel.LOG_DEBUG.value)
    Logger().log_critical("test critical")
    Logger().log_error("test error")
    Logger().log_warning("test warning")
    Logger().log_info("test info")
    Logger().log_debug("test debug")
    assert os.path.exists(LOG_DIR)
    assert check_for_phrase("CRITICAL") is True
    assert check_for_phrase("ERROR") is True
    assert check_for_phrase("WARNING") is True
    assert check_for_phrase("INFO") is True
    assert check_for_phrase("DEBUG") is True
