#!/usr/bin/env python


# coding: utf-8
import os
import pytest
from src.cfg.config_files_helper import ConfigFileHelper
from os.path import expanduser


class TestConfigWrapper:
    CONFIG_PATH = expanduser("~") + "/AppData/cfg/conf.ini"

    @pytest.fixture(scope="function", autouse=True)
    def _setup(self):
        pass

    def test_createDefaultSetIfNotExist(self):
        ConfigFileHelper.create_default_set_if_not_exist()
        assert os.path.isfile(TestConfigWrapper.CONFIG_PATH)
