#!/usr/bin/env python3

# pylint: disable=C0114
from src.business_logic.models.manager_model_base import ManagerModelBase


class LanguageModel(ManagerModelBase):
    """
    Language data preparation
    TODO! need implementation

    Returns:
        [type]: [description]
    """

    @classmethod
    def get_model_data(cls):
        """
        Get all data for model view page

        Returns:
            [type]: [description]
        """
        _dict = {
            "available_lang": cls._get_available_languages(),
            "language": cls.get_language(),
        }
        return _dict

    @classmethod
    def _get_available_languages(cls):
        """
        Get list of available languages

        Returns:
            list: list of strings
        """
        return ["pl", "en"]
