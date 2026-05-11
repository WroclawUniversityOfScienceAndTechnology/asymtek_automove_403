#!/usr/bin/env python3

# pylint: disable=C0114
from src.gui.tk_framework import (
    tk,
    CButton,
    CImage,
    OkCancelDialog,
)
from .feature_base import FeatureBase


class ConfigPage(FeatureBase):
    """
    Config view page

    Args:
        FeatureBase ([type]): [description]
    """

    BT_BOTTOM_LEFT = "config"
    USER = "user"

    AVATARS = ["mustard", "brown", "green", "skyblue", "purple"]

    def __init__(self, canvas, **kwargs):
        FeatureBase.__init__(self, canvas, **kwargs)

    def update_impl(self, **kwargs):
        self.make_update(**kwargs)

        img1 = CImage(
            path=self.img_dir + "/" + ConfigPage.BT_BOTTOM_LEFT + ".png",
            anchor=tk.CENTER,
            inactive=True,
        )
        self.add_to_canvas_list(
            CButton(
                self.canvas,
                callback=self.service_mode,
                anchor=tk.SW,
                padding=[75, 75],
                scale=self.scale,
                cimg_list=[img1],
            )
        )

    # pylint: disable=W0613
    def service_mode(self, event):
        """
        :params
        :return
        """

        OkCancelDialog(self.canvas, "ok", "test message")
