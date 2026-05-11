#!/usr/bin/env python3


"""
This module is interface for config parser.
"""

import ast
import gettext

from .config_files_helper import ConfigFileHelper
from .config_wrapper import ConfigWrapper
from .config_verificator import ConfigVerificator


class Configuration:
    """
    Project global configuration/calibration data management.
    Provide a possibility to read/write data from/to non-volatile memory
    """

    @staticmethod
    def check_config():
        """
        Check if configuration on disk is valid. Raise exception in case of invalid config
        """

        keys = ConfigVerificator.get_keys()
        for key in keys:
            if not ConfigVerificator.check(key):
                raise RuntimeError("Config invalid, key {} not allowed".format(key))
            value = Configuration.get(key, ConfigVerificator.get_section(key))
            if not ConfigVerificator.verify(key, value):
                raise RuntimeError(
                    "Config invalid, value {} invalid for key {}".format(value, key)
                )

    @staticmethod
    def install_language(language="pl", language_dir=ConfigFileHelper.LANGUAGE_DIR):
        """
        Install language base on language string or use pl as default

        Args:
            language (str, optional): [description]. Defaults to "pl".
            language_dir (string, optional): path to lang dir.
            Defaults to ConfigFileHelper.LANGUAGE_DIR.
        """
        lang = gettext.translation("base", localedir=language_dir, languages=[language])
        lang.install()

    @staticmethod
    def update_settings():
        """
        Load the configuration base on config.ini file.
        If this file not exist in defined localisation them
        new config.ini will be created
        :return:
        """
        ConfigFileHelper.create_default_set_if_not_exist()
        ConfigWrapper.update_settings(
            ConfigFileHelper.SETTINGS_PATH,
            ConfigFileHelper.DEFAULT_SETTINGS_PATH,
        )
        Configuration._update_local_paths()

    @staticmethod
    def reset_settings():
        """
        Reset all configuration data store in config.ini to defaults
        :return:
        """
        ConfigFileHelper.remove_config_files()
        Configuration.update_settings()

    @staticmethod
    def _update_local_paths():
        settings = ConfigWrapper.get_settings_from_path(ConfigFileHelper.SETTINGS_PATH)
        ConfigWrapper.set_settings_value_in_section(
            settings,
            "GENERAL",
            "log_file_path",
            '"' + ConfigFileHelper.MAIN_DIR + "/program.log" + '"',
            force_update=True,
        )
        ConfigWrapper.set_settings_value_in_section(
            settings,
            "GENERAL",
            "audio_dir",
            '"' + ConfigFileHelper.AUDIO_DIR + '"',
            force_update=True,
        )
        ConfigWrapper.set_settings_from_path(ConfigFileHelper.SETTINGS_PATH, settings)

    @classmethod
    def get(cls, key, section="USER"):
        """
        Get value from configuration
        :param key: param which shall be read
        :param section: read from user section if not specified
        :return: value of the key in the configuration
        """
        if not ConfigVerificator.check(key):
            raise RuntimeError("Invalid key {}".format(key))
        settings = ConfigWrapper.get_settings_from_path(ConfigFileHelper.SETTINGS_PATH)
        value = ConfigWrapper.get_settings_value_from_section(
            settings, section, str(key)
        )
        if value is None:
            raise RuntimeError("Key {} has no value".format(key))
        return cls._parse_value(value)

    @staticmethod
    def set(key, value, section="USER", force_update=True):
        """
        Set settings value for chosen key and store the settings
        :param force_update:
        :param key:
        :param value:
        :param section: read from user section if not specified
        :return:
        """
        if not ConfigVerificator.check(key):
            raise RuntimeError("No such key {}".format(key))
        if not ConfigVerificator.verify(key, value):
            raise RuntimeError("Invalid value {} for key {}".format(value, key))
        settings = ConfigWrapper.get_settings_from_path(ConfigFileHelper.SETTINGS_PATH)
        if isinstance(value, str):
            value = '"' + value + '"'
        ConfigWrapper.set_settings_value_in_section(
            settings, section, str(key), str(value), force_update=force_update
        )
        ConfigWrapper.set_settings_from_path(ConfigFileHelper.SETTINGS_PATH, settings)

    @classmethod
    def _parse_value(cls, value):
        """
        Get value according to its type

        Args:
            value ([type]): [description]

        Returns:
            [type]: value in auto-specified type
        """
        # pylint: disable=R1705
        if '"' in value:
            return str(value[1:-1])
        elif value.isdecimal():
            return int(value)
        elif value in (True, False):
            return bool(value)
        else:
            return ast.literal_eval(value)
