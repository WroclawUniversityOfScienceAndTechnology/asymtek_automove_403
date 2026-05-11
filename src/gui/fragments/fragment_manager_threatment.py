#!/usr/bin/env python

# pylint: disable=C0114, E0602, R0903
from src.gui.tk_framework import tk, CImage, CButton
from src.gui.fragments.fragment_base import FragmentBase


class FragmentManagerThreatment(FragmentBase):
    """
    Prepare two buttons fragment visible for all manager options
    and partially for threatment options

    Args:
        FragmentBase ([type]): [description]
    """

    BT_MANAGER = "manager_panel"
    BT_THREATMENT = "threatment"

    def __init__(self, parent, **kwargs):
        FragmentBase.__init__(self, parent, **kwargs)
        self.active_manager = False
        self.active_threatment = False

    def add_fragment(self, **kwargs):
        """
        Create fragment of the Top menu and add it to existing canvas
        """
        # only one can be active at a time
        self.active_manager = kwargs.get("active_manager", True)
        self.active_threatment = not self.active_manager

        self._add_bt_manager(active_graphics=self.active_manager)
        self._add_bt_threatment(active_graphics=self.active_threatment)

    def _add_bt_manager(self, active_graphics):
        """
        Adding language icon and Label

        Args:
            lang (string): Present language
        """
        color = "black"
        if active_graphics:
            color = "white"

        img = CImage(
            path=self.parent.img_dir
            + "/bt_"
            + FragmentManagerThreatment.BT_MANAGER
            + ".png",
            inactive=not active_graphics,
        )
        img1 = CImage(
            path=self.parent.img_dir
            + "/"
            + FragmentManagerThreatment.BT_MANAGER
            + ".png",
            padding=[40, 25],
            inactive=not active_graphics,
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._manager_panel,
                anchor=tk.NW,
                padding=[48, 152],
                scale=self.parent.scale,
                cimg_list=[img, img1],
                text=_("MANAGER PANEL"),
                color=color,
            )
        )

    def _add_bt_threatment(self, active_graphics):
        """
        Adding language icon and Label

        Args:
            active (bool): If button shall contain active graphics
        """
        color = "black"
        if active_graphics:
            color = "white"

        img = CImage(
            path=self.parent.img_dir
            + "/bt_"
            + FragmentManagerThreatment.BT_MANAGER
            + ".png",
            inactive=not active_graphics,
        )
        img1 = CImage(
            path=self.parent.img_dir
            + "/"
            + FragmentManagerThreatment.BT_THREATMENT
            + ".png",
            padding=[40, 25],
            inactive=not active_graphics,
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._threatment_panel,
                anchor=tk.NW,
                padding=[381, 152],
                scale=self.parent.scale,
                cimg_list=[img, img1],
                text=_("THREATMENT"),
                color=color,
            )
        )

    def _manager_panel(self, event):
        """
        _manager_panel callback

        Args:
            event (tk.Event): event of a user
        """
        # no need any action if already activated
        if self.active_manager:
            return

        dictionary = {
            "event_src": self.__class__.__name__,
            "event_name": "_manager_panel",
            "event": event,
        }
        self.parent.subject.on_next(dictionary)

    def _threatment_panel(self, event):
        """
        _threatment_panel callback

        Args:
            event (tk.Event): event of a user
        """
        # no need any action if already activated
        if self.active_threatment:
            return

        dictionary = {
            "event_src": self.__class__.__name__,
            "event_name": "_threatment_panel",
            "event": event,
        }
        self.parent.subject.on_next(dictionary)
