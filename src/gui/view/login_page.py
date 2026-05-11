#!/usr/bin/env python3

# pylint: disable=C0114
# pylint: disable=E0602, W0613
from src.gui.tk_framework import tk, CImage, CButton, CLabel, Base
from src.gui.fragments import NumericalKeyboard, FragmentMenu


class LoginPage(Base):
    """
    Add new user view page

    Args:
        Base (LoginPage): Login Page
    """

    BG_LOGIN = "bg_login"
    LOGIN = "login"

    def __init__(self, canvas, **kwargs):
        Base.__init__(self, canvas, **kwargs)
        self.keyboard_chars = None

    def update_impl(self, **kwargs):
        chamber_id = kwargs.get("chamber_id", "CRYO-1111")

        self._add_bg_login()
        self._add_top_labels()
        self._add_botom_labels(chamber_id=chamber_id)
        # add numerical keyboard for passwd
        self.keyboard_chars = NumericalKeyboard(self)
        self.keyboard_chars.add_fragment(anchor=tk.N, passType=1)
        self._add_bt_login()

        menu = FragmentMenu(self)
        menu.add_fragment(**kwargs)

    def _add_bt_login(self):
        """
        Add login button
        """
        padding = [388, 1335]

        img = CImage(
            path=self.img_dir + "/bt_" + LoginPage.LOGIN + ".png", anchor=tk.NW
        )

        self.add_to_canvas_list(
            CButton(
                self.canvas,
                callback=self.login_user_callback,
                anchor=tk.NW,
                scale=self.scale,
                padding=padding,
                cimg_list=[img],
                text=_("LOGIN"),
                color="white",
            )
        )

    def _add_top_labels(self):
        self.add_to_canvas_list(
            CLabel(
                self.canvas,
                anchor=tk.CENTER + tk.N,
                text=_("Welcome back!"),
                padding=[0, 507],
                size=40,
            )
        )
        self.add_to_canvas_list(
            CLabel(
                self.canvas,
                anchor=tk.CENTER + tk.N,
                text=_("Enter pin code to unlock device."),
                padding=[0, 573],
                size=14,
            )
        )

    def _add_botom_labels(self, chamber_id="CRYO-1111"):
        self.add_to_canvas_list(
            CLabel(
                self.canvas,
                anchor=tk.CENTER + tk.N,
                text=_("CRYO CHAMBER ID"),
                padding=[0, 1818],
                size=10,
            )
        )
        self.add_to_canvas_list(
            CLabel(
                self.canvas,
                anchor=tk.CENTER + tk.N,
                text=_(str(chamber_id)),
                padding=[0, 1854],
                size=14,
            )
        )

    def _add_bg_login(self):
        """
        Add custom login background
        """
        img = CImage(path=self.img_dir + "/" + LoginPage.BG_LOGIN + ".png")

        self.add_to_canvas_list(
            CButton(
                self.canvas,
                anchor=tk.NW,
                padding=[0, 0],
                scale=self.scale,
                cimg_list=[img],
            )
        )

    # pylint: disable=W0613
    def login_user_callback(self, event):
        """
        User login callback

        Args:
            user_name (string): user name
        """
        dictionary = {
            "event_src": self.__class__.__name__,
            "event_name": "login_user",
            "event": self.keyboard_chars.get_keybord_inserted_value(),
        }
        self.subject.on_next(dictionary)
