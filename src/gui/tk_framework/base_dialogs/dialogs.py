#!/usr/bin/env python3

# pylint: skip-file
from src.gui.tk_framework import tk

try:
    from tkinter import Label, Button
except ImportError:
    from Tkinter import Label, Button


class DialogBase(tk.Toplevel):
    def __init__(self, parent, title, msg, type="Info"):
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        self.parent = parent

        if title:
            self.title(title)
        body = tk.Frame(self)
        self.initial_focus = self.body(body, msg)
        body.pack(padx=5, pady=5)
        self.buttonbox(type)

        if not self.initial_focus:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

        self.initial_focus.focus_set()
        self.wait_visibility()

    def body(self, body, msg):
        pass

    def buttonbox(self, type="Info"):
        box = tk.Frame(self)
        w = Button(box, text=_("OK"), width=10, default=tk.ACTIVE, command=self.ok)
        w.pack(side=tk.LEFT, padx=5, pady=5)

        if type != "Info":
            w = Button(box, text=_("Cancel"), width=10, command=self.cancel)
            w.pack(side=tk.LEFT, padx=5, pady=5)
            self.bind("<Escape>", self.cancel)

        self.bind("<Return>", self.ok)
        box.pack()

    def ok(self):
        """
        Ok button was pressed
        """
        self.withdraw()
        self.update_idletasks()
        self.destroy()

    def cancel(self):
        """
        Cancel button was pressed
        """
        self.destroy()


class OkCancelDialog(DialogBase):
    """
    OK-Cancel dialog box. Show and lock on popup window with chosen message
    and tile. Wait till OK pressed!
    """

    def __init__(self, parent, title, msg, type="Info"):
        DialogBase.__init__(self, parent, title, msg, type)
        self.grab_set_global()

    def body(self, body, msg):
        """
        Override of the popup body

        Args:
            body (tk.Frame): middle frame in the popup
            msg (string): message appering in the popup window
        """
        label = Label(body, text=msg, font=("Verdana", 12))
        label.pack(side="top", fill="x", pady=10)
