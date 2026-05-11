import pytest
import os

from os.path import expanduser
from src.business_logic import LoginModel
from src.cfg import Configuration


def test_language_change():
    LoginModel.set_language("en")
    data = LoginModel.get_model_data()
    assert data["language"] == "en"
