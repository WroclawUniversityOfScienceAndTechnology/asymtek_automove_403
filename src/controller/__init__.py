#!/usr/bin/env python

# pylint: disable=C0114

import signal
import sys

# others
from src.logger import Logger
from src.cfg import Configuration, ConfigFileHelper
from src.controller.main_state_machine import MainStateMachine
from src.gui.tk_framework import tk
from src.gui.screen import (
    BASE_SCREEN_HEIGHT,
    BASE_SCREEN_WIDTH,
    SUPPORTED_RESOLUTIONS,
    format_resolution,
    get_resolution_scale,
)


class MainController(tk.Tk):
    """
    Main controller is responsible for setting up the view and transfer data between
    View and the model
    """

    def __init__(self, *args, **kwargs):
        """
        Init UI and its base views(pages)
        """
        tk.Tk.__init__(self, *args, **kwargs)

        self.configure(bg="white")
        program_name = Configuration.get("program_name", section="GENERAL")
        self.title(program_name)
        Logger().log_info(program_name)

        self.screen_width = Configuration.get("screen_width", section="GENERAL")
        self.screen_height = Configuration.get("screen_height", section="GENERAL")
        self.scale = get_resolution_scale(self.screen_width, self.screen_height)
        screen_size = format_resolution(self.screen_width, self.screen_height)

        Logger().log_debug(screen_size)
        self.geometry(screen_size)
        self._create_menu_bar()
        self.protocol("WM_DELETE_WINDOW", self._quit_adv)
        signal.signal(signal.SIGINT, self._signal_handler)

        # this container contains all the pages
        container = tk.Frame(self)
        container.pack(side="left", fill=tk.BOTH, expand=True)
        # make the cell in grid cover the entire window
        container.grid_rowconfigure(0, weight=1)
        # make the cell in grid cover the entire window
        container.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(container, bg="white", relief="raised")
        self._configure_canvas_resolution()
        if Configuration.get("fullscreen_mode", section="GENERAL"):
            self.attributes("-fullscreen", True)
            # pylint: disable=W0511
            # TODO uncomment in the final product version
            # self.config(cursor="none")
        else:
            self._create_scrollable_container(vertical=True)

        self.canvas.pack(side="left", fill=tk.BOTH, expand=True)
        self.update()  # update to get correct widgets sizes

        # main state machine
        self.main_state_machine = MainStateMachine()
        self.main_state_machine.init_state_machine(
            self.canvas,
            img_dir=ConfigFileHelper.IMAGE_DIR,
            default_font=ConfigFileHelper.DEFAULT_FONT,
            scale=self.scale,
        )
        self.main_state_machine.init()

    # pylint: disable=W0613
    def _signal_handler(self, sig, frame):
        self.quit()

    def _quit_adv(self):
        """
        Quit the application
        """
        try:
            self.quit()
            sys.exit()
        # pylint: disable=W0703
        except Exception as error:
            Logger().log_critical("Start Frame problem" + str(error))
            sys.exit()

    # Sets up the Canvas scrollbars for scrolling
    def _create_scrollable_container(self, vertical=True, horizontal=False):
        self.attributes("-fullscreen", False)
        if horizontal:
            scroll_x = tk.Scrollbar(
                self,
                orient="horizontal",
                command=self.canvas.xview,
                highlightthickness=0,
            )
            scroll_x.pack(fill=tk.X, side=tk.TOP, expand=tk.FALSE)
            self.canvas.configure(xscrollcommand=scroll_x.set)

        if vertical:
            scroll_y = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            scroll_y.pack(fill=tk.Y, side=tk.RIGHT, expand=tk.FALSE)
            self.canvas.configure(yscrollcommand=scroll_y.set)

    def _create_menu_bar(self):
        self.resolution_var = tk.StringVar(value=format_resolution(self.screen_width, self.screen_height))
        menu_bar = tk.Menu(self)
        machine_menu = tk.Menu(menu_bar, tearoff=False)
        resolution_menu = tk.Menu(menu_bar, tearoff=False)

        machine_menu.add_command(label="Serial settings", command=self._open_serial_settings)
        machine_menu.add_command(
            label="Restore default machine parameters",
            command=self._restore_default_machine_settings,
        )

        for width, height in SUPPORTED_RESOLUTIONS:
            label = format_resolution(width, height)
            resolution_menu.add_radiobutton(
                label=label,
                value=label,
                variable=self.resolution_var,
                command=lambda width=width, height=height: self._change_resolution(width, height),
            )

        menu_bar.add_cascade(label="Machine", menu=machine_menu)
        menu_bar.add_cascade(label="Screen resolution", menu=resolution_menu)
        self.config(menu=menu_bar)

    def _open_serial_settings(self):
        if hasattr(self, "main_state_machine"):
            self.main_state_machine.open_serial_settings(self)

    def _restore_default_machine_settings(self):
        if hasattr(self, "main_state_machine"):
            self.main_state_machine.restore_default_machine_settings()

    def _configure_canvas_resolution(self):
        self.canvas.configure(
            width=self.screen_width,
            height=self.screen_height,
            scrollregion=(0, 0, self.screen_width, self.screen_height),
        )
        self.canvas.design_width = BASE_SCREEN_WIDTH
        self.canvas.design_height = BASE_SCREEN_HEIGHT
        self.canvas.ui_scale = self.scale

    def _change_resolution(self, width, height):
        self.screen_width = width
        self.screen_height = height
        self.scale = get_resolution_scale(width, height)

        Configuration.set("screen_width", width, section="GENERAL")
        Configuration.set("screen_height", height, section="GENERAL")
        if Configuration.get("fullscreen_mode", section="GENERAL"):
            Configuration.set("fullscreen_mode", False, section="GENERAL")
        self.attributes("-fullscreen", False)

        self.geometry(format_resolution(width, height))
        self._configure_canvas_resolution()
        self.update_idletasks()

        if hasattr(self, "main_state_machine"):
            self.main_state_machine.set_scale(self.scale)
            self.main_state_machine.reload_current_view()
