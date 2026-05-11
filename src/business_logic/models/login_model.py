#!/usr/bin/env python3


# pylint: disable=C0114
from src.cfg import Configuration
from src.logger import Logger


class LoginModel:
    """
    Model responsible for data preparation for loggin page.
    Use classmethod as a static functions
    """

    @classmethod
    def get_model_data(cls):
        """
        Get all data for loggin view page

        Returns:
            [type]: [description]
        """
        _dict = {
            "language": cls._get_language(),
            "users": cls._get_users(),
        }
        return _dict

    @classmethod
    def _get_users(cls):
        """
        Get available users related data

        Returns:
            [type]: [description]
        """
        return [{"name": "GUEST", "avatar": "brown"}]

    @classmethod
    def _get_language(cls):
        """
        Get preset application language

        Returns:
            string: language
        """
        return Configuration.get("language")

    @classmethod
    def set_language(cls, lang):
        """
        Set new application language and install it

        Args:
            lang (string): language
        """
        Configuration.install_language(lang)
        Configuration.set("language", lang)
        Logger().log_debug("Language change to = " + lang)
