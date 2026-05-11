#!/usr/bin/env python3

# pylint: skip-file
from src.gui.tk_framework import tk

try:
    from tkinter import Button
except ImportError:
    from Tkinter import Button


class PopupKeyboard(tk.Toplevel):
    """
    Popup Keyboard is a module to be used with Python's Tkinter library
    It subclasses the Entry widget as KeyboardEntry to make a pop-up
    keyboard appear when the widget gains focus.
    A Toplevel instance that displays a keyboard that is attached to
    another widget. Only the Entry widget has a subclass in this version.
    """

    # pylint: disable=C0103, R0913
    def __init__(self, parent, attach, x, y, key_color="black", key_size=10):
        tk.Toplevel.__init__(self, takefocus=0)

        self.overrideredirect(True)
        self.attributes("-alpha", 0.85)

        self.parent = parent
        self.attach = attach
        self.key_size = key_size
        self.key_color = key_color
        self.x = x
        self.y = y
        self.capital = False
        self._init_keys()
        # resize to fit keys
        self.update_idletasks()
        self.grab_set()

    def _init_keys(self):
        pass

    def destroy_popup(self):
        self.destroy()

    def select(self, k):
        if k == "Caps Lock":
            self.capital = not self.capital
        elif k == "<":
            length = len(self.attach.get())
            self.attach.delete((length - 1), length)
        elif k == "^":
            self.destroy_popup()
        else:
            if self.capital:
                self.attach.insert(tk.END, k.capitalize())
            else:
                self.attach.insert(tk.END, k)


class CharsKeyboard(PopupKeyboard):
    """
    A Toplevel instance that displays a keyboard that is attached to
    another widget. Only the Entry widget has a subclass in this version.
    """

    def __init__(self, parent, attach, x, y, key_color="black", key_size=10):
        PopupKeyboard.__init__(
            self, parent, attach, x, y, key_color="black", key_size=key_size
        )

        self.geometry(
            "{}x{}+{}+{}".format(self.winfo_width(), self.winfo_height(), 0, self.y)
        )

    def _init_keys(self):
        buttons = [
            "q",
            "w",
            "e",
            "r",
            "t",
            "y",
            "u",
            "i",
            "o",
            "p",
            "a",
            "s",
            "d",
            "f",
            "g",
            "h",
            "j",
            "k",
            "l",
            "<",
            "Caps Lock",
            "z",
            "x",
            "c",
            "v",
            "b",
            "n",
            "m",
            "-",
            "_",
            "^",
        ]
        var_row = 0
        var_col = 0
        for button in buttons:
            Button(
                self,
                text=button,
                width=self.key_size,
                height=self.key_size / 2,
                fg=self.key_color,
                command=(lambda x=button: self.select(x)),
            ).grid(row=var_row, column=var_col)

            var_col += 1
            if var_col > 9:
                var_col = 0
                var_row += 1


class NumericalKeyboard(PopupKeyboard):
    """
    A Toplevel instance that displays a keyboard that is attached to
    another widget. Only the Entry widget has a subclass in this version.
    """

    def __init__(self, parent, attach, x, y, key_color="black", key_size=10):
        PopupKeyboard.__init__(
            self, parent, attach, x, y, key_color="black", key_size=key_size
        )

        self.geometry(
            "{}x{}+{}+{}".format(
                self.winfo_width(), self.winfo_height(), self.x, self.y
            )
        )

    def _init_keys(self):
        buttons = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "<", "0", "^"]
        var_row = 0
        var_col = 0
        for button in buttons:
            Button(
                self,
                text=button,
                width=self.key_size,
                height=int(self.key_size / 4),
                fg=self.key_color,
                command=(lambda x=button: self.select(x)),
            ).grid(row=var_row, column=var_col)

            var_col += 1
            if var_col > 2:
                var_col = 0
                var_row += 1


class KeyboardEntry(tk.Frame):
    """
    An extension/subclass of the Tkinter Entry widget, capable
    of accepting all existing args, plus a keysize and keycolor option.
    Will pop up an instance of _PopupKeyboard when focus moves into
    the widget

    Usage:
    KeyboardEntry(parent, keysize=6, keycolor='white').pack()
    """

    def __init__(
        self,
        parent,
        key_type="numerical",
        key_size=10,
        key_color="gray",
        text="",
        *args,
        **kwargs
    ):
        tk.Frame.__init__(self, parent)
        self.parent = parent
        self.key_type = key_type

        self.entry = tk.Entry(self, *args, **kwargs)
        self.entry.pack()
        self.entry.insert(tk.END, text)
        self.key_size = key_size
        self.key_color = key_color
        self.kb = None

        self.state = "idle"

        self.entry.bind("<FocusIn>", lambda e: self._check_state("focusin"))
        self.entry.bind("<FocusOut>", lambda e: self._check_state("focusout"))
        self.entry.bind("<Key>", lambda e: self._check_state("keypress"))
        self.entry.bind("<Button-1>", lambda e: self._check_state("focusin"))

    def _check_state(self, event):
        """
        finite state machine
        :param event:
        :return:
        """
        if self.state == "idle":
            if event == "focusin":
                self._call_popup()
                self.state = "virtualkeyboard"
        elif self.state == "virtualkeyboard":
            if event == "focusout":
                self.destroy_popup()
                self.state = "idle"
            elif event == "keypress":
                self.destroy_popup()
                self.state = "typing"
            elif event == "focusin":
                self._call_popup()
                self.state = "virtualkeyboard"
        elif self.state == "typing":
            if event == "focusout":
                self.state = "idle"

    def _call_popup(self):
        if self.key_type == "numerical":
            self.kb = NumericalKeyboard(
                attach=self.entry,
                parent=self.parent,
                x=self.entry.winfo_rootx(),
                y=self.entry.winfo_rooty() + self.entry.winfo_reqheight(),
                key_size=self.key_size,
                key_color=self.key_color,
            )
        else:
            self.kb = CharsKeyboard(
                attach=self.entry,
                parent=self.parent,
                x=self.entry.winfo_rootx(),
                y=self.entry.winfo_rooty() + self.entry.winfo_reqheight(),
                key_size=self.key_size,
                key_color=self.key_color,
            )

    def get_value(self):
        """
        Get value form the entry

        Returns:
            string: entry value in form of string
        """
        return self.entry.get()

    def is_valid(self):
        if self.kb is None:
            return False
        return True

    def destroy_popup(self):
        """
        Destroy popup keypad
        """
        self.kb.destroy_popup()

    def set_bg_color(self, color):
        """
        Change entry backgroung

        Args:
            color (string): color of the backgorund
        """
        self.entry.config({"background": color})
