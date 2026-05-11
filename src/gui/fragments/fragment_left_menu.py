#!/usr/bin/env python

# pylint: disable=C0114, R0903, C0114, C0115, E0602, R1705, R0903
from src.gui.tk_framework import tk, CImage, CButton
from .fragment_base import FragmentBase


class FragmentLeftMenu(FragmentBase):
    MENU_LEFT = "menu_left"
    BT_ENGINE_ROOM = "engine_room"
    BT_NOTIFICATIONS = "notifications"
    BT_LANGUAGE = "language"

    def __init__(self, parent, **kwargs):
        FragmentBase.__init__(self, parent, **kwargs)
        self.current_feature_id = parent.ENGINE_ROOM

    def add_fragment(self, **kwargs):
        """
        Create fragment of the Top menu and add it to existing canvas
        """
        self.current_feature_id = kwargs.get("feature_id", self.parent.ENGINE_ROOM)
        self._add_felt_menu()

    def _add_felt_menu(self):
        """
        Add custom login background
        """
        _y = 280
        _x = 48

        img = CImage(
            path=self.parent.img_dir + "/" + FragmentLeftMenu.MENU_LEFT + ".png"
        )

        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                anchor=tk.NW,
                padding=[48, 280],
                cimg_list=[img],
            )
        )
        _y += 105
        _x += 1
        _offset_y = 80

        self._add_menu_bt(
            inactive=self._check_if_inactive(self.parent.ENGINE_ROOM),
            padding=[49, _y],
            text=_("Engine room"),
            bt_name=self.BT_ENGINE_ROOM,
            event_name="engine_room",
        )

        _y += _offset_y
        self._add_menu_bt(
            inactive=self._check_if_inactive(self.parent.NOTIFICATIONS),
            padding=[49, _y],
            text=_("Notifications"),
            bt_name=self.BT_NOTIFICATIONS,
            event_name="notifications",
        )

        _y += _offset_y
        self._add_menu_bt(
            inactive=self._check_if_inactive(self.parent.LANGUAGE),
            padding=[49, _y],
            text=_("Language"),
            bt_name=self.BT_LANGUAGE,
            event_name="language",
        )

    def _check_if_inactive(self, feature_id):
        if feature_id == self.current_feature_id:
            return False
        else:
            return True

    def _add_menu_bt(self, **kwargs):
        """
        Adding cleft menu button with action
        """
        inactive = kwargs.get("inactive", True)
        padding = kwargs.get("padding", [0, 0])
        text = kwargs.get("text", "")
        bt_name = kwargs.get("bt_name", "")
        event_name = kwargs.get("event_name", "")

        img = CImage(
            path=self.parent.img_dir + "/bt_" + self.MENU_LEFT + ".png",
            inactive=inactive,
        )
        img1 = CImage(
            path=self.parent.img_dir + "/" + bt_name + ".png",
            padding=[40, 27],
            inactive=inactive,
        )
        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=lambda event, event_name=event_name: self._callback(
                    event_name, event
                ),
                anchor=tk.NW,
                padding=padding,
                cimg_list=[img, img1],
                text=text,
                size=14,
                color="black" if inactive else "white",
            )
        )

    def _callback(self, event_name, event):
        """
        rx based callback

        Args:
            event (tk.Event): event of a user
        """
        dictionary = {
            "event_src": self.__class__.__name__,
            "event_name": event_name,
            "event": event,
        }
        print(dictionary)
        self.parent.subject.on_next(dictionary)
