

import pytest


def pytest_addoption(parser):
    """
    Parse the input parameters here
    :param parser:
    :return:
    """
    pass


def pytest_runtest_setup(item):
    """
    Setup before each single tests separately
    It will skip slow tests. Usage is recommended for nightly or other long term tests
    :param item:
    :return:
    """
    pass
