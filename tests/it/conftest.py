

import pytest
from src.cfg import Configuration


def pytest_addoption(parser):
    """
    Parse the input parameters here
    :param parser:
    :return:
    """
    parser.addoption("--runslow", action="store_true", help="Run slow tests only")


def pytest_runtest_setup(item):
    """
    It will skip slow test. Usage is recommended for nightly or other long term tests
    :param item:
    :return:
    """
    if "slow" in item.keywords and not item.config.getvalue("runslow"):
        pytest.skip("need --runslow option to run")

    # apply fresh config file
    Configuration.reset_settings()
    Configuration.update_settings()
    Configuration.install_language()
