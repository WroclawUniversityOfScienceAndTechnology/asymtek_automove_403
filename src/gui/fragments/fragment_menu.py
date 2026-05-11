#!/usr/bin/env python

# pylint: skip-file
from src.gui.tk_framework import tk, CImage, CButton, CClock, CLabel
from src.gui.fragments.fragment_base import FragmentBase


class FragmentMenu(FragmentBase):
    """
    Present menu placed on the top of the screen

    Args:
        FragmentBase ([type]): [description]
    """

    MENU_LINE = "menu_line"
    BT_LOGOUT = "logout"
    ICON_LANG = "icon_language"

    def __init__(self, parent, **kwargs):
        FragmentBase.__init__(self, parent, **kwargs)

    def add_fragment(self, **kwargs):
        """
        Create fragment of the Top menu and add it to existing canvas
        """
        language = kwargs.get("language", "EN")
        self._add_bg_menu()
        self._add_logout_bt()
        self._add_clock()
        self._add_language(language)

    def _add_language(self, lang):
        """
        Adding language icon and Label

        Args:
            lang (string): Present language
        """
        img = CImage(path=self.parent.img_dir + "/" + FragmentMenu.ICON_LANG + ".png")
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                anchor=tk.NW,
                padding=[32, 32],
                scale=self.parent.scale,
                cimg_list=[img],
            )
        )

        _lang = str.upper(lang)
        self.parent.add_to_canvas_list(
            CLabel(
                self.parent.canvas,
                anchor=tk.NW,
                text=_lang,
                padding=[85, 48],
                size=14,
            )
        )

    def _add_clock(self):
        """
        Add system clock to the menu
        """
        self.parent.add_to_canvas_list(
            CClock(
                self.parent.canvas,
                anchor=tk.NW,
                padding=[980, 48],
                name="clk",
                color="black",
                size=14,
            )
        )

    def _add_logout_bt(self):
        """
        Adding logout button
        """
        img = CImage(
            path=self.parent.img_dir + "/bt_" + FragmentMenu.BT_LOGOUT + ".png"
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=self._logout,
                anchor=tk.NW,
                padding=[1016, 32],
                scale=self.parent.scale,
                cimg_list=[img],
            )
        )

    def _add_bg_menu(self):
        """
        Add custom login background
        """

        img = CImage(path=self.parent.img_dir + "/" + FragmentMenu.MENU_LINE + ".png")

        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                anchor=tk.CENTER + tk.N,
                padding=[0, 95],
                cimg_list=[img],
            )
        )

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
