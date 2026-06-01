

import pytest

# from pytest_bdd import scenario, given, when, then

from src.cfg import ConfigVerificator


def test_get_keys():
    assert ConfigVerificator.get_keys() == [
        "auto_update",
        "program_name",
        "extended_mode",
        "fullscreen_mode",
        "screen_width",
        "screen_height",
        "log_file_path",
        "file_log_level",
        "console_log_level",
        "audio_dir",
        "language",
        "pin",
        "temperature_units",
        "TIME_PER_SQMM",
        "Z_OFFSET_PER_SEC",
        "Z_SAFE_HEIGHT",
        "STEPSXY_PER_MM",
        "STEPSZ_PER_MM",
        "PROGRAM_STEP_DELAY_SEC",
        "jog_distance_mm",
        "SERIAL_PORT",
        "BAUD_RATE",
    ]


def test_check_existing_key():
    assert ConfigVerificator.check("auto_update")


def test_check_non_existing_key():
    assert ConfigVerificator.check("non_existing_key") == False


def test_check_non_string_key():
    with pytest.raises(AssertionError):
        assert ConfigVerificator.check(1)


def test_verify_non_existing_key():
    with pytest.raises(KeyError):
        assert ConfigVerificator.verify("non_existing_key", 10)


def test_verify_bool_keys():
    for key in ["auto_update", "extended_mode", "fullscreen_mode"]:
        assert ConfigVerificator.verify(key, True)
        assert ConfigVerificator.verify(key, False)


def test_verify_bool_keys_wrong_type():
    for key in ["auto_update", "extended_mode", "fullscreen_mode"]:
        assert ConfigVerificator.verify(key, 1) == False
        assert ConfigVerificator.verify(key, "test") == False


def test_verify_int_keys():
    for key in ["screen_width", "screen_height"]:
        assert ConfigVerificator.verify(key, 12)


def test_verify_int_keys_wrong_type():
    for key in ["screen_width", "screen_height"]:
        assert ConfigVerificator.verify(key, False) == False
        assert ConfigVerificator.verify(key, "test") == False
        assert ConfigVerificator.verify(key, 1.25) == False


def test_verify_str_keys():
    for key in ["program_name", "log_file_path", "SERIAL_PORT"]:
        assert ConfigVerificator.verify(key, "test")


def test_verify_str_keys_wrong_type():
    for key in ["program_name", "log_file_path", "SERIAL_PORT"]:
        assert ConfigVerificator.verify(key, False) == False
        assert ConfigVerificator.verify(key, 13) == False
        assert ConfigVerificator.verify(key, 1.25) == False


def test_verify_log_levels():
    for key in ["file_log_level", "console_log_level"]:
        for value in range(0, 50, 10):
            assert ConfigVerificator.verify(key, value)


def test_verify_log_levels_not_in_range():
    for key in ["file_log_level", "console_log_level"]:
        for value in [-1, 1, 11, 51]:
            assert ConfigVerificator.verify(key, value) == False


def test_verify_baud_rate():
    assert ConfigVerificator.verify("BAUD_RATE", 9600)
    assert ConfigVerificator.verify("BAUD_RATE", 115200)


def test_verify_baud_rate_wrong_type():
    for value in [False, "9600", 0, -9600, 9600.0]:
        assert ConfigVerificator.verify("BAUD_RATE", value) == False


def test_verify_machine_float_settings():
    for key in ["TIME_PER_SQMM", "Z_SAFE_HEIGHT", "STEPSXY_PER_MM", "STEPSZ_PER_MM", "jog_distance_mm"]:
        assert ConfigVerificator.verify(key, 1)
        assert ConfigVerificator.verify(key, 1.25)
        assert ConfigVerificator.verify(key, 0) == False
        assert ConfigVerificator.verify(key, False) == False
        assert ConfigVerificator.verify(key, "1.25") == False


def test_verify_non_negative_machine_float_settings():
    for key in ["Z_OFFSET_PER_SEC", "PROGRAM_STEP_DELAY_SEC"]:
        assert ConfigVerificator.verify(key, 0)
        assert ConfigVerificator.verify(key, 1.25)
        assert ConfigVerificator.verify(key, -0.1) == False
        assert ConfigVerificator.verify(key, False) == False
        assert ConfigVerificator.verify(key, "0.25") == False


def test_verify_language():
    assert ConfigVerificator.verify("language", "en")


def test_verify_language_not_in_range():
    assert ConfigVerificator.verify("language", "pl") == False


def test_verify_pin():
    for value in ["012345", "000000", "999999"]:
        assert ConfigVerificator.verify("pin", value)


def test_verify_pin_not_in_range():
    for value in ["0123456", "01234", "a12345"]:
        assert ConfigVerificator.verify("pin", value) == False


def test_verify_language():
    for value in ["C", "F"]:
        assert ConfigVerificator.verify("temperature_units", value)


def test_get_section():
    for key in [
        "auto_update",
        "program_name",
        "extended_mode",
        "fullscreen_mode",
        "screen_width",
        "screen_height",
        "log_file_path",
        "file_log_level",
        "console_log_level",
    ]:
        assert ConfigVerificator.get_section(key) == "GENERAL"
    for key in [
        "language",
        "pin",
        "temperature_units",
        "TIME_PER_SQMM",
        "Z_OFFSET_PER_SEC",
        "Z_SAFE_HEIGHT",
        "STEPSXY_PER_MM",
        "STEPSZ_PER_MM",
        "PROGRAM_STEP_DELAY_SEC",
        "jog_distance_mm",
        "SERIAL_PORT",
        "BAUD_RATE",
    ]:
        assert ConfigVerificator.get_section(key) == "USER"
