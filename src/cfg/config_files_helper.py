#!/usr/bin/env python3


"""
This module is responsible for accessing config file.
"""

import os
from pathlib import Path
from os.path import expanduser
from shutil import copyfile
from distutils.dir_util import copy_tree


class ConfigFileHelper:
    """
    Global configuration management helper methods.
    """

    # default config files
    PROGRAM_DIR = "./src/cfg"
    INSTALL_DIR_NAME = "AppData"
    DEFAULT_DIR = PROGRAM_DIR + "/" + INSTALL_DIR_NAME
    DEFAULT_CFG_DIR = DEFAULT_DIR + "/cfg"
    DEFAULT_AUDIO_DIR = DEFAULT_DIR + "/audio"
    DEFAULT_FONT_DIR = DEFAULT_DIR + "/fonts"

    DEFAULT_SETTINGS_PATH = DEFAULT_CFG_DIR + "/conf.ini"
    # local config files
    MAIN_DIR = expanduser("~") + "/" + INSTALL_DIR_NAME

    CONFIGURATION_DIR = MAIN_DIR + "/cfg"
    AUDIO_DIR = MAIN_DIR + "/audio"
    SETTINGS_PATH = CONFIGURATION_DIR + "/conf.ini"
    LANGUAGE_DIR = DEFAULT_DIR + "/locale"
    IMAGE_DIR = DEFAULT_DIR + "/images"
    FONT_DIR = expanduser("~") + "/" + ".fonts/"
    DEFAULT_FONT = "ITC Avant Garde Gothic Pro"

    @classmethod
    def create_default_set_if_not_exist(cls):
        """
        Create default config file in the system if not exist jet
        :return:
        """
        cls._install_dirs_tree(cls.CONFIGURATION_DIR)
        cls._install_dirs_tree(cls.AUDIO_DIR)
        cls._install_dirs_tree(cls.FONT_DIR)

        cls._copy_file(cls.DEFAULT_SETTINGS_PATH, cls.SETTINGS_PATH)
        cls._copy_dirtree(cls.DEFAULT_AUDIO_DIR, cls.AUDIO_DIR)
        cls._copy_dirtree(cls.DEFAULT_FONT_DIR, cls.FONT_DIR)

    @classmethod
    def remove_config_files(cls):
        """
        Reset the configuration store in a system by
        removing existing config file and creating default one
        :return:
        """
        if os.path.exists(cls.SETTINGS_PATH):
            os.remove(cls.SETTINGS_PATH)

    @classmethod
    def _copy_dirtree(cls, source, destination):
        if os.path.exists(source):
            copy_tree(source, destination)

    @classmethod
    def _install_dirs_tree(cls, destination, exist_ok=True):
        """
        Create define directory tree
        :param directory:
        :param exist_ok:
        :return:
        """
        # create target directory if not exist
        path = Path(destination)
        path.mkdir(parents=True, exist_ok=exist_ok)

    @classmethod
    def _copy_file(cls, source, destination, copy=False):
        """
        Create define directory tree
        :param destination:
        :param source:
        :param copy:
        :return:
        """
        if os.path.exists(source) and copy:
            copyfile(source, destination)
        elif not os.path.exists(destination):
            copyfile(source, destination)
