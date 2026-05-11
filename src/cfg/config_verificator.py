#!/usr/bin/env python3


"""
Vericiator module
"""


class ConfigVerificator:
    """
    Class which stores the scheme for the configuration file
    and the verification criateria for each field.
    """

    schema = {
        "auto_update": lambda value: isinstance(value, bool),
        "program_name": lambda value: isinstance(value, str),
        "extended_mode": lambda value: isinstance(value, bool),
        "fullscreen_mode": lambda value: isinstance(value, bool),
        "screen_width": lambda value: isinstance(value, int) and not isinstance(value, bool),
        "screen_height": lambda value: isinstance(value, int) and not isinstance(value, bool),
        "log_file_path": lambda value: isinstance(value, str),
        "file_log_level": lambda value: isinstance(value, int)
        and not isinstance(value, bool)
        and 0 <= value <= 50
        and value % 10 == 0,
        "console_log_level": lambda value: isinstance(value, int)
        and not isinstance(value, bool)
        and 0 <= value <= 50
        and value % 10 == 0,
        "audio_dir": lambda value: isinstance(value, str),
        "language": lambda value: isinstance(value, str) and value == "en",
        "pin": lambda value: isinstance(value, str) and len(value) == 6 and value.isdecimal(),
        "temperature_units": lambda value: isinstance(value, str) and value == "C" or value == "F",
    }

    section_mappings = {
        "auto_update": "GENERAL",
        "program_name": "GENERAL",
        "extended_mode": "GENERAL",
        "fullscreen_mode": "GENERAL",
        "screen_width": "GENERAL",
        "screen_height": "GENERAL",
        "log_file_path": "GENERAL",
        "file_log_level": "GENERAL",
        "console_log_level": "GENERAL",
        "audio_dir": "GENERAL",
        "language": "USER",
        "pin": "USER",
        "temperature_units": "USER",
    }

    @classmethod
    def check(cls, key):
        """Checks if given key is in the schema"""
        return key in cls.schema.keys()

    @classmethod
    def verify(cls, key, value):
        """Checks if given key, value pair is valid"""
        return cls.schema[key](value)

    @classmethod
    def get_keys(cls):
        """Returns list of keys"""
        return list(cls.schema.keys())

    @classmethod
    def get_section(cls, key):
        """Returns proper section of key"""
        return cls.section_mappings[key]
