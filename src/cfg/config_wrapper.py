#!/usr/bin/env python3

# pylint: disable=C0114
import ast
import os
import configparser


class ConfigWrapper:
    """
    Update strategy:
    <param>=<value>; <update mode>
    where <update mode> can be one of following:
    FU - Force update, force update param value
    SU - Soft update, if value not exist then add it, if exist not update it and keep user data
    DU - Delete update, remove param if exist

    DEFAULT values shall be updated anyway
    """

    CONFIG_DEFAULT = "GENERAL"

    @classmethod
    def update_settings(cls, old_settings_path, new_settings_path, **kwargs):
        """

        :param old_settings_path: path to old user settings
        :param new_settings_path: path to settings which shall be updated
        :return:
        """
        force_update = kwargs.get("force_update", False)
        old_settings = cls.get_settings_from_path(old_settings_path)
        new_settings = cls.get_settings_from_path(new_settings_path)
        if cls._check_update_needed(old_settings, new_settings, force_update):
            # update old settings
            old_settings = cls._update_old_setting(old_settings, new_settings)
            cls.set_settings_from_path(old_settings_path, old_settings)

    @classmethod
    def set_settings_value_in_section(cls, settings, section, key, value, **kwargs):
        """
        Set settings param. If is the same as in default then remove it from other section
        Do not remove if section is default
        :param settings: settings read from the file as ConfigParser()
        :param section: section of the settings (eg 'USER')
        :param key: parameter to be update
        :param value: value to update chosen parameter
        :return:
        """
        force_update = kwargs.get("force_update", False)
        if section not in settings:
            settings.add_section(section)

        if force_update:
            settings[section][key] = str(value)

        if section == cls.CONFIG_DEFAULT:
            return

        if key not in settings[section]:
            settings[section][key] = str(value)

    @staticmethod
    def get_settings_value_from_section(settings, section, key, fallback=None):
        """
        Safe read parameter or return None if not succeed
        :param settings: settings read from the file as ConfigParser()
        :param section: section of the settings (eg 'USER')
        :param key: parameter to be safe read
        :param fallback: fallback value if not exist
        :return:
        """
        value = fallback
        if section in settings:
            value = settings[section].get(key, fallback)
        return value

    @staticmethod
    def get_settings_from_path(settings_path):
        """
        get setting form given path or create one if not exist

        Args:
            settings_path (string): path to ini config file

        Returns:
            configparser: read configuration
        """
        if not os.path.exists(settings_path):
            file = open(settings_path, "w+")
            file.write("[GENERAL]\n")
            file.write("auto_update = True\n")
            file.close()

        settings = configparser.ConfigParser()
        settings.read(settings_path)
        return settings

    @staticmethod
    def set_settings_from_path(settings_path, settings):
        """
        Use setting instance to create empty settings file
        :param settings_path: path where empty setting shall be created
        :param settings: setting instance form configparser
        :return:
        """
        with open(settings_path, "w") as configfile:
            settings.write(configfile)

    @classmethod
    def _check_update_needed(cls, old_settings, new_settings, force_update="False"):
        """
        Check if update of user configuration file is compulsory
        :param old_settings: present user configuration instance
        :param new_settings: new configuration instance
        :param force_update: force update flag
        :return: True is update is needed, False otherwise
        """
        if force_update:
            return True
        # if settings was not updated yet
        auto_update = cls.get_settings_value_from_section(new_settings, section=cls.CONFIG_DEFAULT, key="auto_update")
        auto_update = ast.literal_eval(auto_update)

        if auto_update:
            return True

        # if settings was not updated yet
        auto_update = cls.get_settings_value_from_section(old_settings, section=cls.CONFIG_DEFAULT, key="auto_update")
        auto_update = ast.literal_eval(auto_update)

        if auto_update:
            return True

        return False

    @classmethod
    def _update_old_setting(cls, old_settings, new_settings):
        """
        Update present user configuration with the new one
        :param old_settings: present user configuration
        :param new_settings: new configuration
        :return: updated old configuration according to update strategy
        """
        sections = cls._get_settings_sections(new_settings)
        for section in sections:
            for key, value in new_settings[section].items():
                # update user define data according to update strategy
                cls._update_strategy(old_settings, section, key, value)
        return old_settings

    @staticmethod
    def _get_settings_sections(settings):
        """
        Get all settings sections
        :param settings: setting instance form configparser
        :return: all sections
        """
        settings_section = []
        for key, _ in settings.items():
            settings_section.append(key)
        return settings_section

    @classmethod
    def _update_strategy(cls, settings, section, key, value):
        """
        Update settings key-value in chosen section
        :param settings : settings read from the file as ConfigParser()
        :param section: section of the settings (eg ConfigWrapper.CONFIG_DEFAULT)
        :param key: parameter to be update
        :param value: value to update chosen parameter
        :return:
        """
        values = [item.strip() for item in value.split(";")]

        if section == cls.CONFIG_DEFAULT:
            # copy defaults as it is
            cls.set_settings_value_in_section(settings, section, key, values[0], force_update=True)
            return

        if "FU" in values:
            # Force update
            cls.set_settings_value_in_section(settings, section, key, values[0], force_update=True)
        elif "DU" in values:
            # Delete update
            settings.remove_option(section, key)
        else:
            # case for SU or missing strategy
            cls.set_settings_value_in_section(settings, section, key, values[0], force_update=False)
