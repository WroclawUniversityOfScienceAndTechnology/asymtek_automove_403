# !/usr/bin/env python3

# pylint: disable=C0114, C0103, W0107, W0613
from src.gui.tk_framework import CImage, CButton, CEntry, CPassField, tk
from src.gui.fragments.fragment_base import FragmentBase


class BaseKeybord(FragmentBase):
    """
    Draw keybord on a canvas

    Args:
        FragmentBase ([type]): [description]

    Returns:
        [type]: [description]
    """

    REF_START = "ref_start"
    REF_CLEAR = "clear"
    NUMBER = "rectangle_160"

    def __init__(self, parent, **kwargs):
        FragmentBase.__init__(self, parent, **kwargs)
        self.keyboard_name = "keyboard"
        self.numbers = kwargs.get("numbers", QwertyKeyboard.NUMBER)
        self.ref_start = kwargs.get("ref_start", QwertyKeyboard.REF_START)
        self.ref_clear = kwargs.get("clear", QwertyKeyboard.REF_CLEAR)

    def get_keybord_inserted_value(self):
        """
        Get complete value inserted by the user

        Returns:
            [string]: full value from text field inserted by the user
        """
        return self.parent.get_citem_by_name(self.keyboard_name).get()

    def config(self, **kwargs):
        """
        Configure entry. To see kwargs option please refert to tkinter Entry
        """
        self.parent.get_citem_by_name(self.keyboard_name).config(**kwargs)

    def add_fragment(self, **kwargs):
        """
        Add fragment to paresnt canvas
        """
        self.scale = kwargs.get("scale", getattr(self.parent, "scale", self.scale))
        anchor = kwargs.get("anchor", tk.CENTER + tk.N)
        passEntry = kwargs.get("passType")
        # padding = kwargs.get("padding", [0, 60])

        keyboard_chars = None

        if passEntry == 1:
            imgPath = self.parent.img_dir + "/tf_login" + ".png"
            keyboard_chars = CPassField(
                self.parent.canvas,
                anchor=anchor,
                padding=[542, 671],
                scale=self.scale,
                size=30,
                length=18,
                image_path=imgPath,
                name=self.keyboard_name,
                font=self.parent.default_font,
                font_weight="bold",
            )
        else:
            keyboard_chars = CEntry(
                self.parent.canvas,
                anchor=anchor,
                padding=[542, 671],
                scale=self.scale,
                size=30,
                length=20,
                name=self.keyboard_name,
                font=self.parent.default_font,
                font_weight="bold",
            )

        self.parent.add_to_canvas_list(keyboard_chars)
        self.set_keyboard(**kwargs)

    def set_keyboard(self, **kwargs):
        """
        Set keyboard buttons - need to be implemented by the child
        """
        pass

    def update_keyboard(self, event, chars):
        """
        Update entry callback

        Args:
            event ([type]): [description]
            chars ([type]): [description]
        """
        self.parent.get_citem_by_name(self.keyboard_name).config(bg="White")
        self.parent.get_citem_by_name(self.keyboard_name).insert(chars)

    def _custom_key_add(self, number, padding, **kwargs):
        button_name = kwargs.get("button_name", "")
        shape = kwargs.get("shape", "oval")

        show_no = number
        img = [CImage(path=self.parent.img_dir + "/bt_" + self.numbers + ".png", anchor=tk.NW)]

        if button_name in (self.ref_clear, self.ref_start):
            show_no = ""
            img.append(
                CImage(
                    path=self.parent.img_dir + "/bt_" + button_name + ".png",
                    anchor=tk.NW,
                )
            )

        self.parent.add_to_canvas_list(
            CButton(
                self.parent.canvas,
                callback=(lambda event, no=number: self.update_keyboard(event, no)),
                anchor=tk.NW,
                scale=self.scale,
                padding=padding,
                cimg_list=img,
                shape=shape,
                text=str(show_no),
                font=self.parent.default_font,
                font_weight="bold",
                size=30,
                color="white",
            )
        )

    @classmethod
    def _validate(cls, data):
        if len(data) < 1 or len(data) > 10:
            return False
        return True

    def _get_new_user(self):
        data = self.get_keybord_inserted_value()
        if not self._validate(data):
            self.parent.get_citem_by_name(self.keyboard_name).config(bg="Red")
            return

        _dict = {
            "event_src": self.__class__.__name__,
            "event_name": "get_new_user",
            "event": data,
        }
        self.parent.subject.on_next(_dict)


class QwertyKeyboard(BaseKeybord):
    """
    Draw Qwerty keybord on a canvas

    Args:
        FragmentBase ([type]): [description]

    Returns:
        [type]: [description]
    """

    def __init__(self, parent, **kwargs):
        BaseKeybord.__init__(self, parent, **kwargs)

    def set_keyboard(self, **kwargs):
        """
        Set keyboard on a canvas
        """
        max_row = 3
        max_col = 10
        number = 0
        width_offset = kwargs.get("width_offset", 302)
        height_offset = kwargs.get("height_offset", 831)
        width_padding = kwargs.get("width_padding", 190)
        height_padding = kwargs.get("height_padding", 120)

        letters = [
            "Q",
            "W",
            "E",
            "R",
            "T",
            "Y",
            "U",
            "I",
            "O",
            "P",
            "A",
            "S",
            "D",
            "F",
            "G",
            "H",
            "J",
            "K",
            "L",
            "<",
            "Z",
            "X",
            "C",
            "V",
            "B",
            "N",
            "M",
            "-",
            "_",
            "OK",
        ]

        for j in range(max_row):
            for i in range(max_col):
                padding = [
                    width_offset + i * width_padding,
                    height_offset + j * height_padding,
                ]
                button_name = None
                if letters[number] == "OK":
                    button_name = self.ref_start
                elif letters[number] == "<":
                    button_name = self.ref_clear

                self._custom_key_add(letters[number], padding, button_name=button_name, **kwargs)
                number += 1

    def update_keyboard(self, event, chars):
        """
        Update entry callback

        Args:
            event ([type]): [description]
            chars ([type]): [description]
        """
        self.parent.get_citem_by_name(self.keyboard_name).config(bg="White")

        if chars == "OK":
            self._get_new_user()
        elif chars == "<":
            self.parent.get_citem_by_name(self.keyboard_name).clean()
        else:
            self.parent.get_citem_by_name(self.keyboard_name).insert(chars)


class NumericalKeyboard(BaseKeybord):
    """
    Draw Qwerty keybord on a canvas

    Args:
        FragmentBase ([type]): [description]

    Returns:
        [type]: [description]
    """

    def __init__(self, parent, **kwargs):
        BaseKeybord.__init__(self, parent, **kwargs)

    def set_keyboard(self, **kwargs):
        """
        Set keyboard on a canvas
        """
        max_row = 4
        max_col = 3
        number = 0
        width_offset = kwargs.get("width_offset", 302)
        height_offset = kwargs.get("height_offset", 831)
        width_padding = kwargs.get("width_padding", 190)
        height_padding = kwargs.get("height_padding", 120)

        letters = [
            "1",
            "2",
            "3",
            "4",
            "5",
            "6",
            "7",
            "8",
            "9",
            "<",
            "0",
            "C",
        ]

        for j in range(max_row):
            for i in range(max_col):
                padding = [
                    width_offset + i * width_padding,
                    height_offset + j * height_padding,
                ]

                self._custom_key_add(letters[number], padding, button_name=None, **kwargs)
                number += 1

    def update_keyboard(self, event, chars):
        """
        Update entry callback

        Args:
            event ([type]): [description]
            chars ([type]): [description]
        """
        self.parent.get_citem_by_name(self.keyboard_name).config(bg="White")

        if chars == "OK":
            self._get_new_user()
        elif "C" in chars:
            self.parent.get_citem_by_name(self.keyboard_name).clean()
        elif chars == "<":
            self.parent.get_citem_by_name(self.keyboard_name).remove_last_char()
        else:
            self.parent.get_citem_by_name(self.keyboard_name).insert(chars)
