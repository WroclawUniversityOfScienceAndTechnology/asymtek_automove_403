#!/usr/bin/env python

# pylint: disable=C0114, R0903
from src.gui.tk_framework import tk, CImage, CButton
from .fragment_base import FragmentBase


class FragmentRoundMenu(FragmentBase):
    """
    Draw Round menu on a canvas

    Args:
        FragmentBase ([type]): [description]
    """

    BT_CENTER = "center"
    BT_TOP_RIGHT = "top_right"
    BT_BOTTOM_LEFT = "bottom_left"
    BT_TOP_LEFT = "top_left"
    BT_BOTTOM_RIGHT = "bottom_right"
    BT_INFO = "info"
    BT_BACK = "back"

    def __init__(self, parent, **kwargs):
        FragmentBase.__init__(self, parent, **kwargs)

    def add_fragment(self, **kwargs):
        self.parent.scale = kwargs.get("scale", self.parent.scale)
        inactive = kwargs.get("inactive", False)

        img = CImage(path=self.parent.img_dir + "/bt_" + FragmentRoundMenu.BT_TOP_RIGHT + ".png")
        img1 = CImage(
            path=self.parent.img_dir + "/" + FragmentRoundMenu.BT_TOP_RIGHT + ".png",
            anchor=tk.NW,
            padding=[60, 60],
            inactive=inactive,
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._top_right,
                anchor=tk.NW,
                padding=[15, 15],
                scale=self.parent.scale,
                cimg_list=[img, img1],
            )
        )

        img = CImage(path=self.parent.img_dir + "/bt_" + FragmentRoundMenu.BT_BOTTOM_LEFT + ".png")
        img1 = CImage(
            path=self.parent.img_dir + "/" + FragmentRoundMenu.BT_BOTTOM_LEFT + ".png",
            anchor=tk.SW,
            padding=[60, 60],
            inactive=inactive,
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._bottom_left,
                anchor=tk.SW,
                padding=[15, 15],
                scale=self.parent.scale,
                cimg_list=[img, img1],
            )
        )

        img = CImage(path=self.parent.img_dir + "/bt_" + FragmentRoundMenu.BT_TOP_LEFT + ".png")
        img1 = CImage(
            path=self.parent.img_dir + "/" + FragmentRoundMenu.BT_TOP_LEFT + ".png",
            anchor=tk.NE,
            padding=[60, 60],
            inactive=inactive,
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._top_left,
                anchor=tk.NE,
                padding=[15, 15],
                scale=self.parent.scale,
                cimg_list=[img, img1],
            )
        )

        img = CImage(path=self.parent.img_dir + "/bt_" + FragmentRoundMenu.BT_BOTTOM_RIGHT + ".png")
        img1 = CImage(
            path=self.parent.img_dir + "/" + FragmentRoundMenu.BT_BOTTOM_RIGHT + ".png",
            anchor=tk.SE,
            padding=[60, 60],
            inactive=inactive,
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._bottom_right,
                anchor=tk.SE,
                padding=[15, 15],
                scale=self.parent.scale,
                cimg_list=[img, img1],
            )
        )

        img = CImage(path=self.parent.img_dir + "/bt_" + FragmentRoundMenu.BT_BACK + ".png")
        img1 = CImage(
            path=self.parent.img_dir + "/" + FragmentRoundMenu.BT_INFO + ".png",
            anchor=tk.CENTER,
            padding=[0, 5],
            inactive=inactive,
        )

        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._info,
                anchor=tk.CENTER + tk.S,
                padding=[0, 15],
                scale=self.parent.scale,
                cimg_list=[img, img1],
                shape="oval",
            )
        )

        img = CImage(path=self.parent.img_dir + "/bt_" + FragmentRoundMenu.BT_CENTER + ".png")

        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._center,
                anchor=tk.CENTER,
                padding=[0, 0],
                scale=self.parent.scale,
                cimg_list=[img],
                shape="oval",
            )
        )

    def _center(self, event):
        self.parent.update_callback(event_src=self.__class__.__name__, event_name="_center", event=event)

    def _top_right(self, event):
        self.parent.update_callback(event_src=self.__class__.__name__, event_name="_top_right", event=event)

    def _top_left(self, event):
        self.parent.update_callback(event_src=self.__class__.__name__, event_name="_top_left", event=event)

    def _bottom_left(self, event):
        self.parent.update_callback(event_src=self.__class__.__name__, event_name="_buttom_left", event=event)

    def _bottom_right(self, event):
        self.parent.update_callback(event_src=self.__class__.__name__, event_name="_bottom_right", event=event)

    def _info(self, event):
        self.parent.update_callback(event_src=self.__class__.__name__, event_name="_info", event=event)

    def _back(self, event):
        self.parent.update_callback(event_src=self.__class__.__name__, event_name="_back", event=event)
