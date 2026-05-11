#!/usr/bin/env python

# pylint: skip-file
from src.gui.tk_framework import Base
from src.gui.fragments import FragmentMenu, FragmentLeftMenu


class ManagerBase(Base):
    """
    Inherit from this class to create standard page elements

    Args:
        Base ([type]): [description]
    """

    ENGINE_ROOM = 0x01
    NOTIFICATIONS = 0x02
    LANGUAGE = 0x03

    def __init__(self, canvas, **kwargs):
        Base.__init__(self, canvas, **kwargs)

    def make_update(self, **kwargs):
        """
        Make page update
        """
        # add top menu
        menu = FragmentMenu(self)
        menu.add_fragment(**kwargs)

        left_menu = FragmentLeftMenu(self)
        left_menu.add_fragment(**kwargs)
