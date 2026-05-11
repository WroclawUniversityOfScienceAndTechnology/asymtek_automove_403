

import pytest
from pytest_bdd import scenario, given, when, then

from src.cfg import Configuration


@scenario("features/cfg.feature", "Set new value")
def test_set_value():
    pass


@pytest.fixture
@given("Configuration")
def configuration():
    return Configuration()


@pytest.fixture
@when("Set new value")
def update(configuration):
    configuration.set("fullscreen_mode", True)
    configuration.set("program_name", "test_name")


@pytest.fixture
@then("New value has been set")
def assertion(configuration):
    fullscreen_mode = configuration.get("fullscreen_mode")
    program_name = configuration.get("program_name")
    assert fullscreen_mode == True
    assert program_name == "test_name"
