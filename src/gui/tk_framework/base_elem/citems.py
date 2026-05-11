#!/usr/bin/env python


# pylint: disable=C0114, W0105, C0413, E1101, R0903, C0115, R0902, C0116, C0103
import os
from datetime import datetime

try:
    import tkinter as tk  # python3
except ImportError:
    import Tkinter as tk  # python2

from enum import Enum, unique
from PIL import ImageTk, Image
from src.logger import Logger


@unique
class AnchorEnum(Enum):
    """
    Relative position of item on the screen
    """

    NW = tk.NW
    NE = tk.NE
    SW = tk.SW
    SE = tk.SE
    CENTER = tk.CENTER
    CS = tk.CENTER + tk.S
    CN = tk.CENTER + tk.N
    CE = tk.CENTER + tk.E
    CW = tk.CENTER + tk.W

    @classmethod
    def has_value(cls, value):
        """
        Check is enum class contatin value

        Args:
            value (int): tk padding

        Returns:
            [type]: [description]
        """
        return value in cls._value2member_map_


class CImage:
    """
    Manage image properties
    """

    def __init__(self, path, **kwargs):
        self.inactive = kwargs.get("inactive", False)
        self.padding = kwargs.get("padding", 0)
        self.anchor = kwargs.get("anchor", AnchorEnum.NW.value)
        if not AnchorEnum.has_value(self.anchor):
            self.anchor = AnchorEnum.NW.value
        self.path = path
        if self.inactive:
            self.path = CImage.set_inactive(self.path)

        if (self.padding == 0) or (len(self.padding) != 2):
            self.padding = {"x": 0, "y": 0}
        else:
            self.padding = {"x": self.padding[0], "y": self.padding[1]}

    @classmethod
    def set_inactive(cls, path):
        """
        Get image inactive path. Such image must have "_inactive" postfix before file extension

        Args:
            path (string): path to the file

        Returns:
            string: inactive file path
        """
        filename, file_extension = os.path.splitext(path)
        return filename + "_inactive" + file_extension


class CItem:
    def __init__(self, canvas, **kwargs):
        self.canvas = canvas
        self._x = kwargs.get("x", 0)
        self._y = kwargs.get("y", 0)
        self.color = kwargs.get("color", "black")
        self.scale = kwargs.get("scale", getattr(canvas, "ui_scale", 1))
        self.callback = kwargs.get("callback", None)
        self.width = kwargs.get("width", 0)
        self.height = kwargs.get("height", 0)
        self.anchor = kwargs.get("anchor", AnchorEnum.NW.value)
        self.padding = kwargs.get("padding", 0)
        self.canvas_items = []
        self.name = kwargs.get("name", "")
        self.idx = 0
        self.font = kwargs.get("font", "")
        self.font_weight = kwargs.get("font_weight", "")
        self.max_w = 0
        self.max_h = 0

        if (self.padding == 0) or (len(self.padding) != 2):
            self.padding = {"x": 0, "y": 0}
        else:
            self.padding = {"x": self.padding[0], "y": self.padding[1]}

        if not isinstance(self._x, int):
            raise ValueError()
        if not isinstance(self._y, int):
            raise ValueError()
        if not isinstance(self.width, int):
            raise ValueError()
        if not isinstance(self.height, int):
            raise ValueError()

    def _scaled(self, value):
        return int(round(value * self.scale))

    def _scaled_width(self, value):
        return max(1, self._scaled(value))

    def _font_size(self, size):
        return self._scaled_width(size)

    def _set_positions(self):
        if (self._x != 0) or (self._y != 0):
            self.anchor = AnchorEnum.NW.value

        self.max_w = getattr(self.canvas, "design_width", self.canvas.winfo_width())
        self.max_h = getattr(self.canvas, "design_height", self.canvas.winfo_height())

        if self.anchor == AnchorEnum.NW.value:
            self._x = 0 + self.padding["x"]
            self._y = 0 + self.padding["y"]
        elif self.anchor == AnchorEnum.NE.value:
            self._x = self.max_w - self.width - self.padding["x"]
            self._y = 0 + self.padding["y"]
        elif self.anchor == AnchorEnum.SW.value:
            self._x = 0 + self.padding["x"]
            self._y = self.max_h - self.height - self.padding["y"]
        elif self.anchor == AnchorEnum.SE.value:
            self._x = self.max_w - self.width - self.padding["x"]
            self._y = self.max_h - self.height - self.padding["y"]
        elif self.anchor == AnchorEnum.CENTER.value:
            self._x = self.max_w / 2 - self.width / 2 + self.padding["x"]
            self._y = self.max_h / 2 - self.height / 2 + self.padding["y"]
        elif self.anchor == AnchorEnum.CS.value:
            self._x = self.max_w / 2 - self.width / 2 + self.padding["x"]
            self._y = self.max_h - self.height - self.padding["y"]
        elif self.anchor == AnchorEnum.CN.value:
            self._x = self.max_w / 2 - self.width / 2 + self.padding["x"]
            self._y = 0 + self.padding["y"]
        elif self.anchor == AnchorEnum.CW.value:
            self._x = 0 + self.padding["x"]
            self._y = self.max_h / 2 - self.height / 2 - self.padding["y"]
        elif self.anchor == AnchorEnum.CE.value:
            self._x = self.max_w - self.width - self.padding["x"]
            self._y = self.max_h / 2 - self.height / 2 - self.padding["y"]

    def __del__(self):
        self.delete_all_items()

    def tag_lower(self):
        """
        Move the item to lower level in presentation hierarhy (like push back)
        """
        self.canvas.tag_lower(self.idx)

    def get_index(self):
        """
        Get citem index

        Returns:
            int: index of the citem
        """
        return self.idx

    def get_name(self):
        return self.name

    def addToItemList(self, citem):
        """
        Add citem to the canvas list

        Args:
            item (citem): object which inherit form citem
        """
        self.canvas_items.append(citem)

    def delete_all_items(self):
        """
        Delete elements belong to citems from the canvas
        """
        # remove all items from canvas
        for val in self.canvas_items:
            try:
                self.canvas.delete(val)
            except tk.TclError:
                pass
        self.canvas_items = []

    def geometry_assign(self, x, y, width, height):
        if x >= 0:
            self._x = x
        if y >= 0:
            self._y = y
        if width >= 0:
            self.width = width
        if height >= 0:
            self.height = height

    @staticmethod
    def get_img_size(path=""):
        """
        Get size of the image

        Args:
            path (str, optional): path to the image. Defaults to "".

        Returns:
            tuple: width, height
        """
        try:
            image = Image.open(path)
            size = image.size
            image.close()
            return size
        except IOError as error:
            Logger().log_critical("The image cannot be loaded: " + str(error))
            return 0, 0

    @staticmethod
    def get_image(path="", **kwargs):
        """
        Get image instance

        Args:
            path (str, optional): path to image. Defaults to "".

        Returns:
            ImageTk.PhotoImage: image instance
        """
        try:
            image = Image.open(path)
            width, height = image.size
            scale = kwargs.get("scale", 1)
            if scale != 1:
                resampling_filter = getattr(Image, "Resampling", Image).LANCZOS
                image = image.resize(
                    (
                        max(1, int(round(width * scale))),
                        max(1, int(round(height * scale))),
                    ),
                    resampling_filter,
                )
            return ImageTk.PhotoImage(image)
        except IOError as error:
            Logger().log_critical("The image cannot be loaded: " + str(error))
            return None

    @staticmethod
    def polygon_button(canvas, points, callback, **kwargs):
        """
        Create polygon shaped button

        Args:
            canvas (tktinter canvas): canvas
            points (x,y, point list): list of the points
            callback (function): callback function which will be triggered by
            the button

        Returns:
            tk.Button: new button with shape and action
        """
        shape = kwargs.get("shape", "rect")
        fill = kwargs.get("fill", "")
        outline = kwargs.get("outline", "")

        if shape == "oval":
            button = canvas.create_oval(points, fill=fill, outline=outline)
        else:
            button = canvas.create_rectangle(points, fill=fill, outline=outline)
        canvas.tag_raise(button)
        canvas.tag_bind(button, "<Button-1>", callback)
        return button


class CButton(CItem):
    def __init__(self, canvas, **kwargs):
        CItem.__init__(self, canvas, **kwargs)
        self.cimg_list = kwargs.get("cimg_list", [])
        self.shape = kwargs.get("shape", "rect")
        self.text = kwargs.get("text", "")
        self.size = kwargs.get("size", 12)
        self.font = kwargs.get("font", "")
        self.font_weight = kwargs.get("font_weight", "")
        self.imgs = []

        if len(self.cimg_list) > 0:
            self.width, self.height = CItem.get_img_size(self.cimg_list[0].path)

        self._set_positions()
        self._create_cbutton(shape=self.shape)

    def _create_cbutton(self, **kwargs):
        """
        Create button with or without pictogram
        """
        if len(self.cimg_list) > 0:
            self._create_pictograms()
        if self.text:
            self._add_text_to_button()
        if self.callback:
            self.addToItemList(self._create_custom_bt(**kwargs))

    def _create_pictograms(self):
        """
        Create pictorgem (image) for the button
        """
        for idx, cimg in enumerate(self.cimg_list):
            img = CItem.get_image(path=cimg.path, scale=self.scale)
            self.imgs.append(img)
            x, y = self.adj_img_position(cimg, idx)
            # if idx == 0:
            self.addToItemList(self.canvas.create_image((x, y), image=img, anchor=tk.NW))
            self.idx = self.canvas_items[-1]

    def adj_img_position(self, cimg, idx):
        """
        Addjust position of the image

        Args:
            cimg ([type]): [description]
            idx (int): [description]

        Returns:
            tuple: position in form of x, y
        """
        x = self._x + int(cimg.padding["x"])
        y = self._y + int(cimg.padding["y"])

        if idx > 0:
            img_w, img_h = CItem.get_img_size(cimg.path)
            img_w = self.width - img_w
            img_h = self.height - img_h
            padd_x = int(cimg.padding["x"])
            padd_y = int(cimg.padding["y"])
            if cimg.anchor == AnchorEnum.NW.value:
                x = self._x + padd_x
                y = self._y + padd_y
            elif cimg.anchor == AnchorEnum.NE.value:
                x = self._x + img_w - padd_x
                y = self._y + padd_y
            elif cimg.anchor == AnchorEnum.SW.value:
                x = self._x + padd_x
                y = self._y + img_h - padd_y
            elif cimg.anchor == AnchorEnum.SE.value:
                x = self._x + img_w - padd_x
                y = self._y + img_h - padd_y
            elif cimg.anchor == AnchorEnum.CENTER.value:
                x = (self._x + img_w / 2) + padd_x
                y = (self._y + img_h / 2) + padd_y

        return self._scaled(x), self._scaled(y)

    def _create_custom_bt(self, **kwargs):
        if len(self.cimg_list) < 1:
            kwargs["fill"] = self.color
        points = [
            self._scaled(self._x),
            self._scaled(self._y),
            self._scaled(self._x + self.width),
            self._scaled(self._y + self.height),
        ]

        return CItem.polygon_button(self.canvas, points, self.callback, **kwargs)

    def _add_text_to_button(self):
        """
        Add test to button
        """
        self.addToItemList(
            self.canvas.create_text(
                self._scaled(self._x + self.width / 2),
                self._scaled(self._y + self.height / 2),
                fill=self.color,
                font=(
                    self.font,
                    str(self._font_size(self.size)),
                    self.font_weight,
                ),
                text=self.text,
            )
        )


class CLabel(CItem):
    """
    Lable which will be drawn on the canvas

    Args:
        CItem (CLabel): Label item
    """

    def __init__(self, canvas, **kwargs):
        CItem.__init__(self, canvas, **kwargs)
        self.text = kwargs.get("text", "")
        self.size = kwargs.get("size", 12)
        self._set_positions()
        self._create_ctext()

    def _create_ctext(self):
        """
        Create ctext item
        """
        self.addToItemList(
            self.canvas.create_text(
                self._scaled(self._x + self.width / 2),
                self._scaled(self._y + self.height / 2),
                fill=self.color,
                font=(
                    self.font,
                    str(self._font_size(self.size)),
                    self.font_weight,
                ),
                text=self.text,
            )
        )
        self.idx = self.canvas_items[-1]


class CCircularProgressbar(CItem):
    """
    Create circular progress bar

    Args:
        CItem (CCircularProgressbar): Circular progress bar
    """

    def __init__(self, canvas, **kwargs):
        CItem.__init__(self, canvas, **kwargs)
        self.start_ang = kwargs.get("start_ang", 90)
        self.full_extent = kwargs.get("full_extent", 360)

        self.running = False
        self.interval = 0
        self.increment = 0
        self.extent = 0
        self.cur_extent = 0

        color_val = "#%02x%02x%02x" % (227, 6, 19)
        self.color = kwargs.get("color", color_val)

        if self.height == 0:
            self.height = self.width
        elif self.width == 0:
            self.width = self.height

        self._set_positions()
        self._create_cprogress_bar()
        self.start()

    def __del__(self):
        self.stop()
        self.delete_all_items()

    def _create_cprogress_bar(self):
        """
        create progress bar
        """
        self.running = False
        self.interval = 0
        self.increment = 0
        self.extent = 0
        self.cur_extent = 0
        self.addToItemList(
            self.canvas.create_arc(
                self._scaled(self._x),
                self._scaled(self._y),
                self._scaled(self._x + self.width),
                self._scaled(self._y + self.height),
                start=self.start_ang,
                extent=self.extent,
                width=self._scaled_width(self.width),
                style="arc",
                outline=self.color,
            )
        )
        self.idx = self.canvas_items[-1]

    def reset(self):
        """
        reset progress bar to it initial
        """
        self._create_cprogress_bar()

    def start(self, interval=10):
        """
        start progress bar couting with interva

        Args:
            interval (int, optional): interval/step of progress. Defaults to 10.
        """
        self.interval = interval
        self.increment = self.full_extent / interval
        self.extent = 0
        self.running = True

        self.cur_extent = 0
        # percent = '0%'
        # self.label_id = self.canvas.create_text(self.tx, self.ty, text=percent,
        #                                        font=self.custom_font)
        self.running = True
        self.canvas.after(interval, self.step, self.increment)

    def step(self, delta):
        """
        Increment extent and update arc and label displaying how much completed.
        """
        if self.running:
            self.cur_extent = self.cur_extent + 0.1
            if self.cur_extent < 360:
                self.canvas.itemconfigure(self.idx, extent=self.cur_extent)

            # percent = '{:.0f}%'.format(round(float(self.cur_extent) / self.full_extent * 100))
            # self.canvas.itemconfigure(self.label_id, text=percent)
            self.canvas.after(self.interval, self.step, delta)

    def stop(self):
        """
        Stop progress bar
        """
        self.running = not self.running


class CClock(CItem):
    """
    Create simple clock base on system time - asynchronous

    Args:
        CItem (CClock): graphical clock representation
    """

    def __init__(self, canvas, **kwargs):
        CItem.__init__(self, canvas, **kwargs)
        self.size = kwargs.get("size", 12)
        self.timer = int(kwargs.get("timer", -1))
        self.running = False
        self.interval = 0

        color_val = "#%02x%02x%02x" % (227, 6, 19)
        self.color = kwargs.get("color", color_val)

        if self.height == 0:
            self.height = self.width
        elif self.width == 0:
            self.width = self.height

        self._set_positions()
        self._create_cclock()
        self.start()

    def _create_cclock(self):
        dt_string = CClock.get_present_date_str()
        self.addToItemList(
            self.canvas.create_text(
                self._scaled(self._x),
                self._scaled(self._y),
                fill=self.color,
                font=(self.font, str(self._font_size(self.size)), self.font_weight),
                text=dt_string,
            )
        )
        self.idx = self.canvas_items[-1]

    def reset(self):
        """
        Reset the timer
        """
        if self.timer > 0:
            self.timer = -1

    def start(self, interval=1000):
        """
        Start the clock

        Args:
            interval (int, optional): [description]. Defaults to 1000.
        """
        self.interval = interval
        self.running = True
        self.canvas.after(self.interval, self.step)

    def step(self):
        """
        Increment extent and update arc and label displaying how much completed.
        """
        if self.running and (self.timer > 0):
            self.timer -= 1
            if (self.timer == 0) and self.callback:
                self.callback()

        if self.running:
            dt_string = self.get_present_date_str()
            self.canvas.itemconfigure(self.idx, text=dt_string)

            # percent = '{:.0f}%'.format(round(float(self.cur_extent) / self.full_extent * 100))
            # self.canvas.itemconfigure(self.label_id, text=percent)
            self.canvas.after(self.interval, self.step)

    def stop(self):
        """
        Stop the clock asych object
        """
        self.running = not self.running

    @classmethod
    def get_present_date_str(cls):
        """
        Get actual data representation

        Returns:
            string: present datatime in format "%H:%M"
        """
        # datetime object containing current date and time
        now = datetime.now()
        # dd/mm/YY H:M:S
        dt_string = now.strftime("%H:%M")
        return dt_string


class CClockData(CClock):
    """
    Create simple clock base on system time - asynchronous

    Args:
        CItem (CClockData): graphical clock and data representation
    """

    def __init__(self, canvas, **kwargs):
        CClock.__init__(self, canvas, **kwargs)

    @classmethod
    def get_present_date_str(cls):
        """
        Get actual data representation

        Returns:
            string: present datatime in format "%d/%m/%Y %H:%M:%S"
        """
        # datetime object containing current date and time
        now = datetime.now()
        # dd/mm/YY H:M:S
        dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
        return dt_string


class CCounter(CItem):
    """
    Create simble graphicla counter

    Args:
        CItem (CItem): counter graphical representation
    """

    def __init__(self, canvas, **kwargs):
        CItem.__init__(self, canvas, **kwargs)
        self.size = kwargs.get("size", 12)
        self.counter = kwargs.get("counter", 3)
        self.interval = kwargs.get("interval", 1000)
        self.running = False
        self.cur_counter = self.counter

        color_val = "#%02x%02x%02x" % (227, 6, 19)
        self.color = kwargs.get("color", color_val)

        if self.height == 0:
            self.height = self.width
        elif self.width == 0:
            self.width = self.height

        self._set_positions()
        self._create_cclock()
        self.start()

    def _create_cclock(self):
        """
        Create clock
        """
        self.addToItemList(
            self.canvas.create_text(
                self._scaled(self._x),
                self._scaled(self._y),
                fill=self.color,
                font=(self.font, str(self._font_size(self.size)), self.font_weight),
                text=(str(self.counter) + " s"),
            )
        )
        self.idx = self.canvas_items[-1]

    def start(self, interval=1000):
        """
        Start the counter

        Args:
            interval (int, optional): [description]. Defaults to 1000.
        """
        self.interval = interval
        self.cur_counter = self.counter
        self.running = True
        self.canvas.after(self.interval, self.step)

    def step(self):
        """
        Increment extent and update arc and label displaying how much completed.
        """
        self.cur_counter = self.cur_counter - 1

        if self.running and (self.cur_counter > 0):
            self.canvas.itemconfigure(self.idx, text=(str(self.cur_counter) + " s"))
            self.canvas.after(self.interval, self.step)
        elif self.cur_counter == 0:
            self.running = not self.running
            if self.callback:
                self.callback()
        else:
            return

    def stop(self):
        """
        Stop the counter
        """
        self.running = not self.running
        self.cur_counter = -1


class CEntry(CItem):
    """
    CEntry is a text field which can be fill by the user

    Args:
        CItem (CEntry): CEntry based on tk.Entry
    """

    def __init__(self, canvas, **kwargs):
        CItem.__init__(self, canvas, **kwargs)
        self.text = kwargs.get("text", "")
        self.size = kwargs.get("size", 12)
        self.length = kwargs.get("length", 8)
        self.iner_entry = None
        self._set_positions()
        self._create_centry()

    def __del__(self):
        CItem.__del__(self)
        del self.iner_entry

    def _create_centry(self):
        """
        Create CEntry
        """
        self.iner_entry = tk.Entry(
            self.canvas,
            font=(self.font, str(self._font_size(self.size)), self.font_weight),
            width=self.length,
            justify="center",
        )

        self.addToItemList(
            self.canvas.create_window(
                self._scaled(self._x + self.padding["x"]),
                self._scaled(self._y + self.padding["y"]),
                window=self.iner_entry,
            )
        )
        self.idx = self.canvas_items[-1]

    def get_centry(self):
        """
        Get entry object

        Returns:
            Entry: tk inter entry
        """
        return self.iner_entry

    def insert(self, number):
        """
        Insert number into centry

        Args:
            number (string): some string
        """
        self.iner_entry.insert(tk.END, number)

    def config(self, **kwargs):
        """
        Configure the Entry, for more details please see tk.Entry
        """
        self.iner_entry.config(**kwargs)

    def clean(self, color="White"):
        """
        Clean the Entry - repoze all entry data

        Args:
            color (str, optional): [description]. Defaults to "White".
        """
        self.iner_entry.config(bg=color)
        self.iner_entry.delete(0, tk.END)

    def get(self):
        """
        get value of the entry
        Returns:
            string: entry value
        """
        return self.iner_entry.get()

    def remove_last_char(self):
        # take the string currently in the widget, all the way up to the last character
        txt = self.iner_entry.get()[:-1]
        # clear the widget of text
        self.iner_entry.delete(0, tk.END)
        # insert the new string, sans the last character
        self.iner_entry.insert(0, txt)


class CPassField(CItem):
    """
    CPassField is a password field with marked signs

    Args:
        CItem (CEntry): CEntry based on tk.Entry
    """

    def __init__(self, canvas, **kwargs):
        CItem.__init__(self, canvas, **kwargs)
        self.text = kwargs.get("text", "")
        self.size = kwargs.get("size", 12)
        self.length = kwargs.get("length", 8)
        self.iner_entry = None
        self.iner_canvas = None
        self.img_path = kwargs.get("image_path")
        self.img = None
        self._set_positions()
        self._create_centry()

    def __del__(self):
        CItem.__del__(self)
        del self.iner_entry

    def _create_centry(self):
        """
        Create CEntry
        """

        self.img = CItem.get_image(path=self.img_path, scale=self.scale)

        self.iner_entry = tk.Entry(
            self.canvas,
            font=(self.font, self._font_size(self.size), self.font_weight),
            width=self.length,
            justify="center",
            bd=0,
            highlightthickness=0,
            relief="ridge",
            bg="white",
            show="●",
        )

        self.iner_entry.bind("<Button-1>", lambda e: "break")  # keyup

        self.addToItemList(
            self.canvas.create_image(
                self._scaled(self._x + self.padding["x"]),
                self._scaled(self._y + self.padding["y"]),
                image=self.img,
                anchor="center",
            )
        )
        self.canvas.image = self.img

        self.addToItemList(
            self.canvas.create_window(
                self._scaled(self._x + self.padding["x"]),
                self._scaled(self._y + self.padding["y"]),
                window=self.iner_entry,
            )
        )
        self.idx = self.canvas_items[-1]

    def get_centry(self):
        """
        Get entry object

        Returns:
            Entry: tk inter entry
        """
        return self.iner_entry

    def insert(self, number):
        """
        Insert number into centry

        Args:
            number (string): some string
        """
        self.iner_entry.insert(tk.END, number)

    def config(self, **kwargs):
        """
        Configure the Entry, for more details please see tk.Entry
        """
        self.iner_entry.config(**kwargs)

    def clean(self, color="White"):
        """
        Clean the Entry - repoze all entry data

        Args:
            color (str, optional): [description]. Defaults to "White".
        """
        self.iner_entry.config(bg=color)
        self.iner_entry.delete(0, tk.END)

    def get(self):
        """
        get value of the entry
        Returns:
            string: entry value
        """
        return self.iner_entry.get()

    def remove_last_char(self):
        # take the string currently in the widget, all the way up to the last character
        txt = self.iner_entry.get()[:-1]
        # clear the widget of text
        self.iner_entry.delete(0, tk.END)
        # insert the new string, sans the last character
        self.iner_entry.insert(0, txt)
