#!/usr/bin/env python3

# pylint: disable=C0114
from src.business_logic.models.manager_model_base import ManagerModelBase


class NotificationsModel(ManagerModelBase):
    """
    Notifications data preparation
    TODO! need implementation

    Returns:
        [type]: [description]
    """

    @classmethod
    def get_model_data(cls):
        """
        Get all data for loggin view page

        Returns:
            [type]: [description]
        """
        _dict = {
            "error": cls._get_warnings(),
            "warning": cls._get_warnings(),
            "info": cls._get_info(),
            "language": cls.get_language(),
        }
        return _dict

    @classmethod
    def _get_errors(cls):
        """
        Get error message of the chamber

        Returns:
            list: list of strings
        """
        return ["e0", "e1"]

    @classmethod
    def _get_warnings(cls):
        """
        Get warining messages of the chamber

        Returns:
            list: list of strings
        """
        return ["w0", "w1"]

    @classmethod
    def _get_info(cls):
        """
        Get info messages of the chamber

        Returns:
            list: list of strings
        """
        return ["i0", "i1"]
