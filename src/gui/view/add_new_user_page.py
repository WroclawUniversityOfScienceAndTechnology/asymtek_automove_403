#!/usr/bin/env python3

# pylint: disable=C0114
from src.gui.view.feature_base import FeatureBase
from src.gui.tk_framework import tk, CImage, CButton
from src.gui.fragments import QwertyKeyboard


class AddNewUserPage(FeatureBase):
    """
    Add new user view page

    Args:
        FeatureBase ([type]): [description]
    """

    USER_ADD = "user_add"

    def __init__(self, canvas, **kwargs):
        FeatureBase.__init__(self, canvas, **kwargs)
        self.keyboard_chars = None

    def update_impl(self, **kwargs):
        self.make_update(feature=True)
        self.set_add_user()
        self.keyboard_chars = QwertyKeyboard(self)
        self.keyboard_chars.add_fragment()

    def back(self, event):
        _dict = {
            "event_src": self.__class__.__name__,
            "event_name": "back",
        }
        self.subject.on_next(_dict)
        self.on_exit()

    def on_exit(self):
        """
        Do some extra work on page exit
        """
        del self.keyboard_chars

    # pylint: disable=C0116
    def set_add_user(self):
        img = CImage(
            path=self.img_dir + "/bt_" + AddNewUserPage.USER_ADD + ".png",
            anchor=tk.NW,
        )
        self.add_to_canvas_list(
            CButton(
                self.canvas,
                anchor=tk.NW,
                scale=self.scale,
                padding=[50, 50],
                cimg_list=[img],
            )
        )
