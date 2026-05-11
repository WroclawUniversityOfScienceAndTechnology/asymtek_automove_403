#!/usr/bin/env python

# pylint: disable=C0114, C0115, R0903
from src.gui.tk_framework import tk, CImage, CButton
from src.gui.fragments.fragment_base import FragmentBase


class FragmentNextCancle(FragmentBase):
    """
    Prepare two buttons fragment visible for all threatment pages

    Args:
        FragmentBase ([type]): [description]
    """

    BUTTON = "login"

    def __init__(self, parent, **kwargs):
        FragmentBase.__init__(self, parent, **kwargs)

    def add_fragment(self, **kwargs):
        """
        Create fragment of the Top menu and add it to existing canvas
        """
        bt_next_text = kwargs.get("bt_next_text", "next")
        bt_cancle_text = kwargs.get("bt_cancle_text", "cancel")

        self._add_bt_next(bt_next_text)
        self._add_bt_cancel(bt_cancle_text)

    def _add_bt_next(self, bt_next_text):
        """
        Add next button

        Args:
            bt_next_text (string): lable on the button
        """
        padding = [200, 100]

        img = CImage(
            path=self.parent.img_dir + "/bt_" + self.BUTTON + ".png", anchor=tk.NW
        )

        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._callback_next,
                anchor=tk.CENTER + tk.S,
                scale=self.scale,
                padding=padding,
                cimg_list=[img],
                text=bt_next_text,
                color="white",
            )
        )

    def _add_bt_cancel(self, bt_cancle_text):
        """
        Add cancel button

        Args:
            bt_cancle_text (string): lable on the button
        """
        padding = [-200, 100]

        img = CImage(
            path=self.parent.img_dir + "/bt_" + self.BUTTON + ".png", anchor=tk.NW
        )

        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._callback_cancel,
                anchor=tk.CENTER + tk.S,
                scale=self.scale,
                padding=padding,
                cimg_list=[img],
                text=bt_cancle_text,
                color="white",
            )
        )

    def _callback_next(self, event):
        """
        User next callback
        """
        dictionary = {
            "event_src": self.__class__.__name__,
            "event_name": "next",
            "event": event,
        }
        self.parent.subject.on_next(dictionary)

    def _callback_cancel(self, event):
        """
        User cancel callback
        """
        dictionary = {
            "event_src": self.__class__.__name__,
            "event_name": "cancel",
            "event": event,
        }
        self.parent.subject.on_next(dictionary)
