#!/usr/bin/env python3

# pylint: disable=C0114, W0613, R0201

from src.logger import Logger
from src.gui.tk_framework import CImage, CButton, Base, tk


class FeatureBase(Base):
    """
    Inherit from this class to create standard page elements

    Args:
        Base ([type]): [description]
    """

    BG_LOGIN = "bg_login"
    BG_FEATURE = "bg_feature"
    LOGOUT = "logout"
    BT_BACK = "back"

    def __init__(self, canvas, **kwargs):
        Base.__init__(self, canvas, **kwargs)

    def make_update(self, **kwargs):
        """
        Make page update
        """
        self.scale = kwargs.get("scale", self.scale)
        inactive = kwargs.get("inactive", False)
        feature = kwargs.get("feature", False)

        self.add_background(**kwargs)

        if feature:
            img = CImage(path=self.img_dir + "/" + FeatureBase.BG_FEATURE + ".png")
        else:
            img = CImage(path=self.img_dir + "/" + FeatureBase.BG_LOGIN + ".png")

        self.add_to_canvas_list(
            CButton(
                self.canvas,
                anchor=tk.NW,
                padding=[15, 15],
                scale=self.scale,
                cimg_list=[img],
            )
        )

        if feature:
            img = CImage(path=self.img_dir + "/bt_" + FeatureBase.BT_BACK + ".png")
            img1 = CImage(
                path=self.img_dir + "/" + FeatureBase.BT_BACK + ".png",
                anchor=tk.CENTER,
                padding=[0, 5],
                inactive=inactive,
            )

            self.add_to_canvas_list(
                CButton(
                    self.canvas,
                    callback=self.back,
                    anchor=tk.CENTER + tk.S,
                    padding=[0, 15],
                    scale=self.scale,
                    cimg_list=[img, img1],
                )
            )

    def back(self, event):
        """
        Back button action if exist

        Args:
            event ([type]): [description]
        """
        Logger().log_warning("Need to be implemented by the child")
