

# for more information visit
# https://pypi.org/project/pytest-bdd/
import pytest
import os.path
from pytest_bdd import scenario, given, when, then

from src.cfg import Configuration
from os.path import expanduser


CONFIG_PATH = expanduser("~") + "/AppData/cfg/conf.ini"


@scenario("features/cfg.feature", "Update old configuration")
def test_configuration():
    pass


@pytest.fixture
@given("old configuration new configuration")
def configuration():
    return Configuration()


@pytest.fixture
@when("update old configuration")
def update(configuration):
    configuration.update_settings()


@pytest.fixture
@then("old configuration has been updated with new values")
def assertion(configuration):
    assert os.path.isfile(CONFIG_PATH)
