

# for more information visit
# https://pypi.org/project/pytest-bdd/
import pytest
from src.controller.temperature_convertion import *

# test Celcius to Fahrenheit convertion
def test_convert_simple_celc_val_to_fahrenheit():
    assert celc_to_fahrenheit(37.5) == 99.5


def test_convert_celc_large_negative_to_fahrenheit():
    assert celc_to_fahrenheit(-273.15) == -459.67


def test_convert_celc_large_positive_to_fahrenheit():
    assert celc_to_fahrenheit(537.78) == 1000


# test Fahrenheit to Celcius convertion
def test_convert_simple_fahrenheit_val_to_celc():
    assert fahrenheit_to_celc(99.5) == 37.5


def test_convert_fahrenheit_large_negative_to_celc():
    assert fahrenheit_to_celc(-459.67) == -273.15


def test_convert_fahrenheit_large_positive_to_celc():
    assert fahrenheit_to_celc(1000) == 537.78
