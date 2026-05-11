#!/usr/bin/env python

# pylint: disable=C0114
# pylint: disable=E0611
from src.gui.fragments import FragmentTopMenu
from src.gui.view.feature_base import FeatureBase


class StartPage(FeatureBase):
    """
    Start Page after login

    Args:
        FeatureBase ([type]): [description]
    """

    def __init__(self, canvas, **kwargs):
        FeatureBase.__init__(self, canvas, **kwargs)

    def update_impl(self, **kwargs):
        """
        Update page method
        """
        self.make_update(**kwargs)
        fragment = FragmentTopMenu(self)
        fragment.add_fragment()
