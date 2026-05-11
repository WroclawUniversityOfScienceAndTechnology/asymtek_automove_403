#!/usr/bin/env python

# pylint: disable=C0114, R1705, R0903
from src.logger import Logger
from src.cfg import Configuration


class Authenticator:
    """
    Perform user authentication

    Returns:
        [type]: [description]
    """

    @classmethod
    def make_user_authentication(cls, login="", secret=""):
        """
        Try to authenticate the user base on login and password

        Args:
            login (string): login
            secret (str, optional): [description]. Defaults to "".

        Returns:
            bool: True in authentication succeed, False otherwise
        """
        pin = Configuration.get("pin", section="USER")
        if pin == secret:
            return True
        else:
            Logger().log_warning("Login =" + str(login) + ", secret=" + str(secret))
            return False
