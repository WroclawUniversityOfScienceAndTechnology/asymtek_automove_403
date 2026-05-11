#!/usr/bin/env python

# pylint: disable=C0114

from rx.subject import Subject
from src.logger import Logger
from src.gui.tk_framework.base_elem import CImage, CButton, tk


class Base:
    """
    Base class for all view Pages

    Returns:
        [type]: [description]
    """

    BACKGROUND = "background"

    def __init__(self, canvas, **kwargs):
        self.img_dir = kwargs.get("img_dir", "")
        self.canvas = canvas
        self.canvas_items = []
        self.background_img = kwargs.get("background_img", Base.BACKGROUND)
        self.default_font = kwargs.get("default_font", "")
        # update/draw canvas callbacks
        self.subject = Subject()
        self.scale = kwargs.get("scale", 1)

    def __del__(self):
        self.subject.dispose()
        self.finish()

    def update(self, **kwargs):
        """
        Update page
        """
        self.subject = Subject()
        self.scale = kwargs.get("scale", self.scale)
        self.add_background(**kwargs)
        # this part is implemented by the childs
        self.update_impl(**kwargs)

    # pylint: disable=R0201
    def update_impl(self, **kwargs):
        """
        Each screen shall implement this method
        :return:
        """
        Logger().log_warning("Need to be implemented by the child" + str(kwargs))

    # pylint: disable=W0622
    def rx_subscribe(self, next=None, error=None, complete=None):
        """
        Subscribe to observable

        Args:
            next (function, optional): On next callback. Defaults to None.
            error (function, optional): On error callback. Defaults to None.
            complete (function, optional): On complete callback. Defaults to None.
        """
        self.subject.subscribe(next, error, complete)

    def add_background(self, **kwargs):
        """
        Add background image
        """
        scale = kwargs.get("scale", self.scale)
        bacground = kwargs.get("background", True)

        if bacground:
            img = CImage(path=self.img_dir + "/" + self.background_img + ".png")
            self.add_to_canvas_list(
                CButton(
                    self.canvas,
                    callback=None,
                    anchor=tk.NW,
                    scale=scale,
                    cimg_list=[img],
                    name="background",
                )
            )

    def finish(self):
        """
        Finish te page be stopping all actions
        and removing all stored items
        """
        self.delete_canvas_items()
        self.subject.dispose()

    def add_to_canvas_list(self, citem):
        """
        Add next citem base object to list

        Args:
            citem (citem): citem inherited object

        Returns:
            int: index of the item in the lsit
        """
        self.canvas_items.append(citem)
        return len(self.canvas_items) - 1

    def get_citem_by_name(self, name):
        """
        Get citem from the list base on its name

        Args:
            name (string): citem name

        Returns:
            citem: citem base object
        """
        for citem in self.canvas_items:
            if citem.get_name() == name:
                return citem
        return None

    def delete_item_by_idx(self, idx):
        """
        Delete item from list by the index

        Args:
            idx (int): index of an item int the list
        """
        if idx < len(self.canvas_items):
            del self.canvas_items[idx]

    def delete_citem_by_name(self, name):
        """
        Delete chosen citem by name

        Args:
            name (string): name of the citem
        """
        for citem in self.canvas_items:
            if citem.get_name() == name:
                self.__delete_item(citem)
                return

    def __delete_item(self, citem):
        """
        Delete chosen canvas oitem

        Args:
            citem (citem): [description]
        """
        if citem in self.canvas_items:
            del self.canvas_items[self.canvas_items.index(citem)]

    def delete_canvas_items(self):
        """
        Delete all canvas items
        """
        for item in self.canvas_items:
            try:
                if hasattr(item, "delete_all_items"):
                    item.delete_all_items()
                else:
                    self.canvas.delete(item)
            except tk.TclError:
                pass
        del self.canvas_items[:]
