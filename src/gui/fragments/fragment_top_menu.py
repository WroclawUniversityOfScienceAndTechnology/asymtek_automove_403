#!/usr/bin/env python

# pylint: skip-file
from src.gui.tk_framework import tk, CImage, CButton
from .fragment_base import FragmentBase


class FragmentTopMenu(FragmentBase):
    BT_BASE = "base"
    BT_SAVE = "save"
    BT_LOAD = "save"
    BT_CONFIG = "back"
    BT_INFO = "info"
    BT_LOGOUT = "logout"

    def __init__(self, parent, **kwargs):
        FragmentBase.__init__(self, parent, **kwargs)

    def add_fragment(self, **kwargs):
        """
        Create fragment of the Top menu and add it to existing canvas
        """
        self.parent.scale = kwargs.get("scale", self.parent.scale)
        inactive = kwargs.get("inactive", False)
        x_pad = 35
        y_pad = 35
        x_shift = 60

        img = CImage(path=self.parent.img_dir + "/bt_" + FragmentTopMenu.BT_BASE + ".png")
        img1 = CImage(
            path=self.parent.img_dir + "/" + FragmentTopMenu.BT_SAVE + ".png",
            anchor=tk.NW,
            padding=[15, 15],
            inactive=inactive,
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._save,
                anchor=tk.NW,
                padding=[x_pad, y_pad],
                scale=self.parent.scale,
                cimg_list=[img, img1],
            )
        )

        x_pad = x_pad + x_shift
        img = CImage(path=self.parent.img_dir + "/bt_" + FragmentTopMenu.BT_BASE + ".png")
        img1 = CImage(
            path=self.parent.img_dir + "/" + FragmentTopMenu.BT_LOAD + ".png",
            anchor=tk.NW,
            padding=[15, 15],
            inactive=inactive,
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._load,
                anchor=tk.NW,
                padding=[x_pad, y_pad],
                scale=self.parent.scale,
                cimg_list=[img, img1],
            )
        )

        x_pad = x_pad + x_shift
        img = CImage(path=self.parent.img_dir + "/bt_" + FragmentTopMenu.BT_BASE + ".png")
        img1 = CImage(
            path=self.parent.img_dir + "/" + FragmentTopMenu.BT_CONFIG + ".png",
            anchor=tk.NW,
            padding=[15, 15],
            inactive=inactive,
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._config,
                anchor=tk.NW,
                padding=[x_pad, y_pad],
                scale=self.parent.scale,
                cimg_list=[img, img1],
            )
        )

        x_pad = x_pad + x_shift
        img = CImage(path=self.parent.img_dir + "/bt_" + FragmentTopMenu.BT_BASE + ".png")
        img1 = CImage(
            path=self.parent.img_dir + "/" + FragmentTopMenu.BT_INFO + ".png",
            anchor=tk.NW,
            padding=[8, 18],
            inactive=inactive,
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._info,
                anchor=tk.NW,
                padding=[x_pad, y_pad],
                scale=self.parent.scale,
                cimg_list=[img, img1],
            )
        )

        img = CImage(path=self.parent.img_dir + "/bt_" + FragmentTopMenu.BT_BASE + ".png")
        img1 = CImage(
            path=self.parent.img_dir + "/" + FragmentTopMenu.BT_LOGOUT + ".png",
            anchor=tk.NW,
            padding=[10, 8],
            inactive=inactive,
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._logout,
                anchor=tk.NE,
                padding=[40, y_pad],
                scale=self.parent.scale,
                cimg_list=[img, img1],
            )
        )

    def _save(self, event):
        """
        Save callback

        Args:
            event (tk.Event): event of a user
        """
        dictionary = {
            "event_src": self.__class__.__name__,
            "event_name": "_save",
            "event": event,
        }
        self.parent.subject.on_next(dictionary)

    def _load(self, event):
        """
        Load callback

        Args:
            event (tk.Event): event of a user
        """
        dictionary = {
            "event_src": self.__class__.__name__,
            "event_name": "_load",
            "event": event,
        }
        self.parent.subject.on_next(dictionary)

    def _config(self, event):
        """
        Config callback

        Args:
            event (tk.Event): event of a user
        """
        dictionary = {
            "event_src": self.__class__.__name__,
            "event_name": "_config",
            "event": event,
        }
        self.parent.subject.on_next(dictionary)

    def _info(self, event):
        """
        Config callback

        Args:
            event (tk.Event): event of a user
        """
        dictionary = {
            "event_src": self.__class__.__name__,
            "event_name": "_info",
            "event": event,
        }
        self.parent.subject.on_next(dictionary)

    def _logout(self, event):
        """
        _logout callback

        Args:
            event (tk.Event): event of a user
        """
        dictionary = {
            "event_src": self.__class__.__name__,
            "event_name": "logout",
            "event": event,
        }
        self.parent.subject.on_next(dictionary)
