import pytest
import os

from src.business_logic import Authenticator


def test_correct_Authentication():
    assert Authenticator.make_user_authentication("", "123456") == True


def test_incorrect_Authentication():
    assert Authenticator.make_user_authentication("GUEST", "secret") == False
