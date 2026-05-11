#!/usr/bin/env python3

# pylint: disable=C0114
from src.cfg import Configuration

# pylint: disable=R0903


class ManagerModelBase:
    """
    Base class for all manager panel pages
    Returns:
        [type]: [description]
    """

    @classmethod
    def get_language(cls):
        """
        Get preset application language

        Returns:
            string: language
        """
        return Configuration.get("language")
