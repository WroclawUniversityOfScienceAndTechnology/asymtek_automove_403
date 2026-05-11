#!/usr/bin/env python

# pylint: disable=C0114
from src.gui.view.manager_base import ManagerBase


class LanguagePage(ManagerBase):
    """
    Start Page after login

    Args:
        ManagerBase ([type]): [description]
    """

    def __init__(self, canvas, **kwargs):
        ManagerBase.__init__(self, canvas, **kwargs)

    def update_impl(self, **kwargs):
        """
        Update page method
        """
        kwargs["feature_id"] = self.LANGUAGE
        self.make_update(**kwargs)
