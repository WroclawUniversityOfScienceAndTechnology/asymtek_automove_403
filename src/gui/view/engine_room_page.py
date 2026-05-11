#!/usr/bin/env python

# pylint: disable=C0114, W0613
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.backend.machine_management import (
    generate_acl_from_gerber,
    get_serial_preflight_error,
    list_serial_ports,
    parse_acl_toolpath,
)
from src.cfg import Configuration
from src.gui.tk_framework import Base, tk


class EngineRoomPage(Base):
    """
    ACL CNC frontend dashboard.

    Args:
        Base ([type]): [description]
    """

    def __init__(self, canvas, **kwargs):
        Base.__init__(self, canvas, **kwargs)
        self.program_name = "ACL CNC"
        self.machine_status = "Idle"
        self.active_file = "No Gerber loaded"
        self.extruder_percent = 100
        self.progress_percent = 0
        self.current_line = 0
        self.selected_line = 0
        self.simulation_mode = True
        self.execution_lines = []
        self.machine_progress = {}
        self.machine_position = {"X": None, "Y": None, "Z": None}
        self._simulation_after_id = None
        self._simulation_interval_ms = 300
        self._embedded_widgets = []
        self._machine_setting_entries = {}
        self._machine_position_text_items = {}
        self._serial_settings_dialog = None
        self._status_text_item = None
        self._progress_bar_item = None
        self._progress_text_item = None
        self._selected_line_text_item = None
        self._current_line_text_item = None
        self._progress_summary_text_item = None
        self._execution_line_list = None
        self._displayed_current_line = None
        self._preview_dynamic_items = []
        self.machine_settings = {
            "TIME_PER_SQMM": 1.0,
            "Z_OFFSET_PER_SEC": 0.2,
            "Z_SAFE_HEIGHT": 100.0,
            "STEPSXY_PER_MM": 100.0,
            "STEPSZ_PER_MM": 100.0,
            "jog_distance_mm": 1.0,
            "SERIAL_PORT": "/dev/ttyUSB0",
            "BAUD_RATE": 9600,
        }
        self.machine_setting_fields = [
            ("TIME_PER_SQMM", "TIME_PER_SQMM", "s/mm2"),
            ("Z_OFFSET_PER_SEC", "Z_OFFSET_PER_SEC", "mm/s"),
            ("Z_SAFE_HEIGHT", "Z_SAFE_HEIGHT", "mm"),
            ("STEPSXY_PER_MM", "STEPSXY_PER_MM", "steps/mm"),
            ("STEPSZ_PER_MM", "STEPSZ_PER_MM", "steps/mm"),
        ]

    def update_impl(self, **kwargs):
        """
        Update page method
        """
        self.program_name = kwargs.get("program_name", self.program_name)
        self.machine_status = kwargs.get("machine_status", self.machine_status)
        self.active_file = kwargs.get("active_file", self.active_file)
        self.extruder_percent = kwargs.get("extruder_percent", self.extruder_percent)
        self.progress_percent = kwargs.get("progress_percent", self.progress_percent)
        self.simulation_mode = kwargs.get("simulation_mode", self.simulation_mode)
        self.execution_lines = kwargs.get("execution_lines", self.execution_lines)
        self.machine_progress = kwargs.get("machine_progress", self.machine_progress)
        self.machine_position.update(kwargs.get("machine_position", {}))
        self.machine_settings.update(kwargs.get("machine_settings", {}))
        self._normalize_line_positions()
        self._render()

    def _render(self):
        self.delete_canvas_items()
        self._add_background()
        self._add_header()
        self._add_file_panel()
        self._add_control_panel()
        self._add_preview_panel()
        self._add_execution_panel()

    def finish(self):
        self._close_serial_settings_dialog()
        self._cancel_simulation()
        super().finish()

    def _add_raw(self, item):
        self.canvas_items.append(item)
        return item

    def _add_preview_dynamic_raw(self, item):
        self.canvas_items.append(item)
        self._preview_dynamic_items.append(item)
        return item

    def delete_canvas_items(self):
        for widget in self._embedded_widgets:
            try:
                widget.destroy()
            except tk.TclError:
                pass
        self._embedded_widgets = []
        self._machine_setting_entries = {}
        self._clear_dynamic_render_refs()
        super().delete_canvas_items()

    def _clear_dynamic_render_refs(self):
        self._status_text_item = None
        self._progress_bar_item = None
        self._progress_text_item = None
        self._selected_line_text_item = None
        self._current_line_text_item = None
        self._progress_summary_text_item = None
        self._execution_line_list = None
        self._displayed_current_line = None
        self._preview_dynamic_items = []
        self._machine_position_text_items = {}

    def _scaled(self, value):
        return int(round(value * self.scale))

    def _scaled_width(self, value):
        return max(1, self._scaled(value))

    def _coords(self, values):
        return [self._scaled(value) for value in values]

    def _style_kwargs(self, kwargs):
        if "width" in kwargs:
            kwargs["width"] = self._scaled_width(kwargs["width"])
        return kwargs

    def _font(self, font):
        if len(font) < 2:
            return font
        scaled_size = self._scaled_width(font[1])
        return (font[0], scaled_size) + tuple(font[2:])

    def _rect(self, x0, y0, x1, y1, **kwargs):
        return self._add_raw(
            self.canvas.create_rectangle(
                self._scaled(x0),
                self._scaled(y0),
                self._scaled(x1),
                self._scaled(y1),
                **self._style_kwargs(kwargs),
            )
        )

    def _line(self, *args, **kwargs):
        return self._add_raw(self.canvas.create_line(*self._coords(args), **self._style_kwargs(kwargs)))

    def _oval(self, x0, y0, x1, y1, **kwargs):
        return self._add_raw(
            self.canvas.create_oval(
                self._scaled(x0),
                self._scaled(y0),
                self._scaled(x1),
                self._scaled(y1),
                **self._style_kwargs(kwargs),
            )
        )

    def _polygon(self, *args, **kwargs):
        return self._add_raw(self.canvas.create_polygon(*self._coords(args), **self._style_kwargs(kwargs)))

    def _text(self, x, y, text, **kwargs):
        font = kwargs.pop("font", (self.default_font or "Helvetica", 18))
        fill = kwargs.pop("fill", "#101820")
        anchor = kwargs.pop("anchor", tk.NW)
        if "width" in kwargs:
            kwargs["width"] = self._scaled(kwargs["width"])
        return self._add_raw(
            self.canvas.create_text(
                self._scaled(x),
                self._scaled(y),
                text=text,
                font=self._font(font),
                fill=fill,
                anchor=anchor,
                **kwargs,
            )
        )

    def _preview_line(self, *args, **kwargs):
        return self._add_preview_dynamic_raw(self.canvas.create_line(*self._coords(args), **self._style_kwargs(kwargs)))

    def _preview_oval(self, x0, y0, x1, y1, **kwargs):
        return self._add_preview_dynamic_raw(
            self.canvas.create_oval(
                self._scaled(x0),
                self._scaled(y0),
                self._scaled(x1),
                self._scaled(y1),
                **self._style_kwargs(kwargs),
            )
        )

    def _preview_polygon(self, *args, **kwargs):
        return self._add_preview_dynamic_raw(
            self.canvas.create_polygon(*self._coords(args), **self._style_kwargs(kwargs))
        )

    def _preview_text(self, x, y, text, **kwargs):
        font = kwargs.pop("font", (self.default_font or "Helvetica", 18))
        fill = kwargs.pop("fill", "#101820")
        anchor = kwargs.pop("anchor", tk.NW)
        if "width" in kwargs:
            kwargs["width"] = self._scaled(kwargs["width"])
        return self._add_preview_dynamic_raw(
            self.canvas.create_text(
                self._scaled(x),
                self._scaled(y),
                text=text,
                font=self._font(font),
                fill=fill,
                anchor=anchor,
                **kwargs,
            )
        )

    def _window(self, x, y, width, height, widget, **kwargs):
        self._embedded_widgets.append(widget)
        return self._add_raw(
            self.canvas.create_window(
                self._scaled(x),
                self._scaled(y),
                width=self._scaled(width),
                height=self._scaled(height),
                window=widget,
                **kwargs,
            )
        )

    def _button(self, x, y, width, height, text, event_name, **kwargs):
        fill = kwargs.get("fill", "#1f6feb")
        outline = kwargs.get("outline", fill)
        text_fill = kwargs.get("text_fill", "white")
        font = kwargs.get("font", (self.default_font or "Helvetica", 18, "bold"))
        callback = kwargs.get("callback")
        emit_on_none = kwargs.get("emit_on_none", True)
        rect = self._rect(x, y, x + width, y + height, fill=fill, outline=outline, width=2)
        label = self._text(
            x + width / 2,
            y + height / 2,
            text,
            fill=text_fill,
            font=font,
            anchor=tk.CENTER,
        )

        def on_click(event):
            payload = None
            if callback:
                payload = callback(event)
            if payload is None and not emit_on_none:
                return
            self._emit(event_name, event, payload=payload)

        self.canvas.tag_bind(rect, "<Button-1>", on_click)
        self.canvas.tag_bind(label, "<Button-1>", on_click)
        return rect, label

    def _emit(self, event_name, event=None, payload=None):
        self.subject.on_next(
            {
                "event_src": self.__class__.__name__,
                "event_name": event_name,
                "event": payload if payload is not None else event,
            }
        )

    def _add_background(self):
        self._rect(0, 0, 1920, 1080, fill="#f4f7fb", outline="#f4f7fb")

    def _add_header(self):
        self._rect(0, 0, 1920, 88, fill="#172033", outline="#172033")
        self._text(
            32,
            25,
            self.program_name,
            fill="white",
            font=(self.default_font or "Helvetica", 30, "bold"),
        )
        self._status_text_item = self._text(
            930,
            31,
            "STATUS: " + self.machine_status.upper(),
            fill=self._status_fill(),
            font=(self.default_font or "Helvetica", 18, "bold"),
        )
        self._text(
            600,
            31,
            "MODE: " + ("SIMULATION" if self.simulation_mode else "MACHINE"),
            fill="#dce7f7",
            font=(self.default_font or "Helvetica", 16, "bold"),
        )
        self._text(
            1460,
            31,
            Path(self.active_file).name,
            fill="#dce7f7",
            font=(self.default_font or "Helvetica", 18),
        )

    def _add_file_panel(self):
        self._panel(24, 112, 360, 280, "Program")
        self._button(52, 178, 304, 62, "Load Gerber", "load_gerber", callback=self._load_gerber)
        self._button(
            52,
            258,
            304,
            62,
            "Save Program",
            "save_program",
            fill="#40536d",
            outline="#40536d",
            callback=self._save_program,
        )
        self._add_active_file_path()

    def _add_active_file_path(self):
        self._rect(52, 326, 356, 370, fill="#ffffff", outline="#cad5e3", width=1)
        path_frame = tk.Frame(self.canvas, bg="#ffffff")
        path_label = tk.Label(
            path_frame,
            anchor=tk.NW,
            bg="#ffffff",
            fg="#526071",
            font=self._font((self.default_font or "Helvetica", 8)),
            justify=tk.LEFT,
            padx=0,
            pady=0,
            text=self.active_file,
            wraplength=self._scaled(292),
        )
        path_label.pack(fill=tk.BOTH, expand=True)
        self._window(58, 330, 292, 36, path_frame, anchor=tk.NW)

    def _add_control_panel(self):
        self._panel(24, 410, 360, 622, "Machine Control")
        self._button(
            52,
            474,
            140,
            70,
            "START",
            "start_process",
            fill="#16833a",
            callback=self._start_process,
            emit_on_none=False,
        )
        self._button(216, 474, 140, 70, "PAUSE", "pause_process", fill="#ba7b00", callback=self._pause_process)
        self._button(52, 562, 304, 70, "STOP", "stop_process", fill="#b42318", callback=self._stop_process)
        self._button(
            52,
            650,
            140,
            58,
            "SIM ON" if self.simulation_mode else "MACHINE",
            "toggle_simulation",
            fill="#0ea5e9" if self.simulation_mode else "#40536d",
            outline="#0ea5e9" if self.simulation_mode else "#40536d",
            callback=self._toggle_simulation,
            emit_on_none=False,
        )
        self._button(
            216,
            650,
            140,
            58,
            "STEP",
            "step_line",
            fill="#40536d",
            callback=self._step_line,
            emit_on_none=False,
        )
        self._button(
            52,
            728,
            304,
            58,
            "INIT",
            "machine_init",
            fill="#16833a",
            outline="#16833a",
            callback=self._machine_init,
            emit_on_none=False,
        )

        self._text(52, 820, "Extruder time", fill="#526071", font=(self.default_font or "Helvetica", 16, "bold"))
        self._button(52, 864, 74, 58, "-5%", "extruder_minus", fill="#40536d", callback=self._extruder_down)
        self._rect(144, 864, 264, 912, fill="#ffffff", outline="#cad5e3", width=2)
        self._text(
            204,
            893,
            str(self.extruder_percent) + "%",
            fill="#172033",
            font=(self.default_font or "Helvetica", 22, "bold"),
            anchor=tk.CENTER,
        )
        self._button(282, 864, 74, 58, "+5%", "extruder_plus", fill="#40536d", callback=self._extruder_up)
        self._text(
            52,
            962,
            "Use the software with ACL base machines.",
            fill="#6b778c",
            font=(self.default_font or "Helvetica", 13),
            width=300,
        )

    def _add_preview_panel(self):
        self._panel(408, 112, 920, 444, "Board Preview")
        preview_bounds = (452, 184, 1284, 512)
        self._draw_preview_background(*preview_bounds)

        points = parse_acl_toolpath(self.execution_lines, settings=self.machine_settings)
        if points:
            mapped_points = self._map_toolpath_points(points, 488, 216, 1248, 466)
            self._draw_toolpath_segments(points, mapped_points)
            self._draw_dispense_points(points, mapped_points)
            self._draw_current_tool_position(points, mapped_points)
            self._preview_text(
                476,
                482,
                "{} moves  |  line {} / {}".format(
                    len(points),
                    min(self.current_line + 1, len(self.execution_lines)),
                    len(self.execution_lines),
                ),
                fill="#9fb2cc",
                font=(self.default_font or "Helvetica", 16),
            )
        else:
            self._preview_text(
                476,
                482,
                "No toolpath loaded",
                fill="#9fb2cc",
                font=(self.default_font or "Helvetica", 16),
            )

        self._add_process_setup_panel()

    def _draw_preview_background(self, x0, y0, x1, y1):
        self._rect(x0, y0, x1, y1, fill="#0f1724", outline="#22324a", width=2)
        for x in range(x0 + 48, x1 - 32, 80):
            self._line(x, y0, x, y1, fill="#1e2d43")
        for y in range(y0 + 56, y1 - 12, 80):
            self._line(x0, y, x1, y, fill="#1e2d43")

    def _map_toolpath_points(self, points, x0, y0, x1, y1):
        min_x = min(point.x_mm for point in points)
        max_x = max(point.x_mm for point in points)
        min_y = min(point.y_mm for point in points)
        max_y = max(point.y_mm for point in points)

        if min_x == max_x:
            min_x -= 0.5
            max_x += 0.5
        if min_y == max_y:
            min_y -= 0.5
            max_y += 0.5

        available_width = x1 - x0
        available_height = y1 - y0
        scale = min(available_width / (max_x - min_x), available_height / (max_y - min_y))
        path_width = (max_x - min_x) * scale
        path_height = (max_y - min_y) * scale
        left = x0 + (available_width - path_width) / 2
        bottom = y1 - (available_height - path_height) / 2

        return [
            (
                left + (point.x_mm - min_x) * scale,
                bottom - (point.y_mm - min_y) * scale,
            )
            for point in points
        ]

    def _draw_toolpath_segments(self, points, mapped_points):
        for idx in range(len(mapped_points) - 1):
            x0, y0 = mapped_points[idx]
            x1, y1 = mapped_points[idx + 1]
            is_complete = points[idx + 1].line_index <= self.current_line
            self._preview_line(
                x0,
                y0,
                x1,
                y1,
                fill="#22c55e" if is_complete else "#f6d365",
                width=5 if is_complete else 3,
            )

    def _draw_dispense_points(self, points, mapped_points):
        for point, mapped_point in zip(points, mapped_points):
            if not point.dispensing:
                continue
            x, y = mapped_point
            self._preview_oval(x - 8, y - 8, x + 8, y + 8, fill="#f97316", outline="#fed7aa")

    def _draw_current_tool_position(self, points, mapped_points):
        current_idx = 0
        for idx, point in enumerate(points):
            if point.line_index <= self.current_line:
                current_idx = idx
            else:
                break

        nozzle_x, nozzle_y = mapped_points[current_idx]
        self._preview_polygon(
            nozzle_x,
            nozzle_y - 30,
            nozzle_x - 18,
            nozzle_y + 18,
            nozzle_x + 18,
            nozzle_y + 18,
            fill="#22c55e",
            outline="#bbf7d0",
        )

    def _add_process_setup_panel(self):
        self._panel(408, 588, 920, 444, "Process Setup")
        self._text(436, 654, "Input data", fill="#526071", font=(self.default_font or "Helvetica", 16, "bold"))
        for idx, (key, label, unit) in enumerate(self.machine_setting_fields):
            y = 692 + idx * 42
            self._text(436, y + 8, label, fill="#172033", font=(self.default_font or "Helvetica", 13, "bold"))
            self._entry(key, 620, y, 112, 32)
            self._text(744, y + 8, unit, fill="#526071", font=(self.default_font or "Helvetica", 13))

        self._text(902, 654, "Manual move", fill="#526071", font=(self.default_font or "Helvetica", 16, "bold"))
        self._text(902, 694, "Distance", fill="#172033", font=(self.default_font or "Helvetica", 13, "bold"))
        self._entry("jog_distance_mm", 1000, 686, 102, 34)
        self._text(1116, 694, "mm / click", fill="#526071", font=(self.default_font or "Helvetica", 13))

        self._button(
            1030,
            744,
            72,
            54,
            "Y+",
            "machine_jog_up",
            fill="#40536d",
            callback=lambda event: self._jog("Y", 1),
            emit_on_none=False,
        )
        self._button(
            944,
            808,
            72,
            54,
            "X-",
            "machine_jog_left",
            fill="#40536d",
            callback=lambda event: self._jog("X", -1),
            emit_on_none=False,
        )
        self._button(
            1030,
            808,
            72,
            54,
            "Y-",
            "machine_jog_down",
            fill="#40536d",
            callback=lambda event: self._jog("Y", -1),
            emit_on_none=False,
        )
        self._button(
            1116,
            808,
            72,
            54,
            "X+",
            "machine_jog_right",
            fill="#40536d",
            callback=lambda event: self._jog("X", 1),
            emit_on_none=False,
        )
        self._button(
            1222,
            744,
            72,
            54,
            "Z+",
            "machine_jog_z_plus",
            fill="#40536d",
            callback=lambda event: self._jog("Z", 1),
            emit_on_none=False,
        )
        self._button(
            1222,
            808,
            72,
            54,
            "Z-",
            "machine_jog_z_minus",
            fill="#40536d",
            callback=lambda event: self._jog("Z", -1),
            emit_on_none=False,
        )
        self._add_machine_position_row()

    def _add_machine_position_row(self):
        y = 924
        self._text(436, y + 8, "Current position", fill="#526071", font=(self.default_font or "Helvetica", 16, "bold"))
        for idx, axis in enumerate(("X", "Y", "Z")):
            x = 620 + idx * 154
            self._text(x, y + 8, axis, fill="#172033", font=(self.default_font or "Helvetica", 13, "bold"))
            self._rect(x + 28, y, x + 120, y + 32, fill="#eef3fa", outline="#d8e1ef")
            self._machine_position_text_items[axis] = self._text(
                x + 74,
                y + 17,
                self._format_position_value(axis),
                fill="#172033",
                font=(self.default_font or "Helvetica", 13, "bold"),
                anchor=tk.CENTER,
            )

    def _entry(self, key, x, y, width, height):
        value = self.machine_settings.get(key, 0)
        entry = tk.Entry(
            self.canvas,
            bg="#ffffff",
            fg="#172033",
            font=self._font((self.default_font or "Helvetica", 13)),
            justify=tk.RIGHT,
            relief=tk.SOLID,
            bd=1,
        )
        entry.insert(0, self._format_setting_value(value))
        self._machine_setting_entries[key] = entry
        self._window(x, y, width, height, entry, anchor=tk.NW)
        return entry

    def _serial_port_options(self):
        ports = list_serial_ports()
        current_port = str(self.machine_settings.get("SERIAL_PORT", "")).strip()
        if current_port and current_port not in ports:
            return [current_port] + ports
        return ports

    def _close_serial_settings_dialog(self):
        dialog = self._serial_settings_dialog
        self._serial_settings_dialog = None
        if dialog is None:
            return
        try:
            if dialog.winfo_exists():
                dialog.destroy()
        except tk.TclError:
            pass

    def open_serial_settings_dialog(self, parent=None):
        if self._serial_settings_dialog is not None:
            try:
                self._serial_settings_dialog.lift()
                self._serial_settings_dialog.focus_force()
                return
            except tk.TclError:
                self._serial_settings_dialog = None

        parent = parent or self.canvas.winfo_toplevel()
        dialog = tk.Toplevel(parent)
        self._serial_settings_dialog = dialog
        dialog.title("Serial Settings")
        dialog.resizable(False, False)
        dialog.transient(parent)

        port_var = tk.StringVar(value=str(self.machine_settings.get("SERIAL_PORT", "")))
        baud_var = tk.StringVar(value=str(self.machine_settings.get("BAUD_RATE", 9600)))

        content = ttk.Frame(dialog, padding=16)
        content.grid(row=0, column=0, sticky="nsew")
        content.columnconfigure(1, weight=1)

        ttk.Label(content, text="Serial port").grid(row=0, column=0, padx=(0, 12), pady=6, sticky="w")
        port_combo = ttk.Combobox(content, textvariable=port_var, width=34)
        port_combo.grid(row=0, column=1, pady=6, sticky="ew")

        def refresh_ports():
            ports = self._serial_port_options()
            port_combo["values"] = ports
            if ports and not port_var.get().strip():
                port_var.set(ports[0])

        refresh_ports()
        ttk.Button(content, text="Refresh", command=refresh_ports).grid(row=0, column=2, padx=(8, 0), pady=6)

        ttk.Label(content, text="Baud rate").grid(row=1, column=0, padx=(0, 12), pady=6, sticky="w")
        baud_combo = ttk.Combobox(
            content,
            textvariable=baud_var,
            values=("1200", "2400", "4800", "9600", "19200", "38400", "57600", "115200"),
            width=12,
        )
        baud_combo.grid(row=1, column=1, pady=6, sticky="w")

        ttk.Label(content, text="7 data bits, odd parity, 2 stop bits, RTS/CTS").grid(
            row=2,
            column=0,
            columnspan=3,
            pady=(6, 14),
            sticky="w",
        )

        buttons = ttk.Frame(content)
        buttons.grid(row=3, column=0, columnspan=3, sticky="e")

        def close_dialog():
            self._serial_settings_dialog = None
            dialog.destroy()

        def apply_serial_settings():
            port = port_var.get().strip()
            try:
                baud_rate = int(float(baud_var.get().strip()))
            except ValueError:
                messagebox.showerror("Serial Settings", "Baud rate must be a number.", parent=dialog)
                return

            if not port:
                messagebox.showerror("Serial Settings", "Serial port cannot be empty.", parent=dialog)
                return

            settings = self._read_machine_settings()
            if settings is None:
                messagebox.showerror("Serial Settings", "Process setup contains invalid values.", parent=dialog)
                return

            settings["SERIAL_PORT"] = port
            settings["BAUD_RATE"] = baud_rate
            self.machine_settings = settings
            try:
                self._store_serial_settings(port, baud_rate)
            except RuntimeError as exc:
                messagebox.showerror("Serial Settings", str(exc), parent=dialog)
                return
            close_dialog()
            self.machine_status = "Serial set"
            self._render()

        ttk.Button(buttons, text="Cancel", command=close_dialog).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(buttons, text="Apply", command=apply_serial_settings).grid(row=0, column=1)

        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.bind("<Escape>", lambda event: close_dialog())
        dialog.bind("<Return>", lambda event: apply_serial_settings())
        dialog.grab_set()
        dialog.update_idletasks()
        x = parent.winfo_rootx() + max((parent.winfo_width() - dialog.winfo_width()) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - dialog.winfo_height()) // 2, 0)
        dialog.geometry("+{}+{}".format(x, y))
        port_combo.focus_set()

    def _store_serial_settings(self, port, baud_rate):
        Configuration.set("SERIAL_PORT", port, section="USER")
        Configuration.set("BAUD_RATE", baud_rate, section="USER")

    def _add_execution_panel(self):
        self._panel(1352, 112, 544, 920, "Upcoming Execution")
        self._text(1392, 184, "Generated ACL instructions", fill="#526071", font=(self.default_font or "Helvetica", 15))
        self._add_execution_list()
        self._add_execution_line_controls()

        self._text(1392, 884, "Process", fill="#526071", font=(self.default_font or "Helvetica", 16, "bold"))
        self._rect(1392, 924, 1856, 960, fill="#dbe5f3", outline="#dbe5f3")
        self._progress_bar_item = self._rect(
            1392,
            924,
            1392 + int(464 * self.progress_percent / 100),
            960,
            fill="#22c55e",
            outline="#22c55e",
        )
        self._progress_text_item = self._text(
            1624,
            943,
            str(self.progress_percent) + "%",
            fill="#172033",
            font=(self.default_font or "Helvetica", 15, "bold"),
            anchor=tk.CENTER,
        )

    def _add_execution_list(self):
        list_frame = tk.Frame(self.canvas, bg="#ffffff", highlightthickness=1, highlightbackground="#d8e1ef")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        line_list = tk.Listbox(
            list_frame,
            activestyle="none",
            bg="#ffffff",
            bd=0,
            exportselection=False,
            fg="#172033",
            font=self._font((self.default_font or "Helvetica", 14)),
            highlightthickness=0,
            selectbackground="#d9f7e4",
            selectforeground="#172033",
        )
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=line_list.yview)
        line_list.configure(yscrollcommand=scrollbar.set)
        line_list.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        for idx, line in enumerate(self.execution_lines):
            line_list.insert(tk.END, self._execution_row_text(idx))

        if self.execution_lines:
            line_list.selection_set(self.selected_line)
            line_list.activate(self.selected_line)
            line_list.see(self.selected_line)

        line_list.bind("<<ListboxSelect>>", self._select_execution_line)
        self._execution_line_list = line_list
        self._displayed_current_line = self.current_line
        self._window(1392, 228, 464, 560, list_frame, anchor=tk.NW)

    def _add_execution_line_controls(self):
        total_lines = len(self.execution_lines)
        selected_line = self.selected_line + 1 if total_lines else 0
        current_line = self.current_line + 1 if total_lines else 0

        self._selected_line_text_item = self._text(
            1392,
            812,
            "Selected line: {} / {}".format(selected_line, total_lines),
            fill="#526071",
            font=(self.default_font or "Helvetica", 15, "bold"),
        )
        self._current_line_text_item = self._text(
            1392,
            842,
            "Current line: {} / {}".format(current_line, total_lines),
            fill="#526071",
            font=(self.default_font or "Helvetica", 15),
        )
        progress_summary = self._machine_progress_summary()
        self._progress_summary_text_item = self._text(
            1392,
            870,
            progress_summary,
            fill="#526071",
            font=(self.default_font or "Helvetica", 12),
            width=464,
        )
        self._button(
            1694,
            804,
            162,
            58,
            "Start Line",
            "start_from_line",
            fill="#16833a",
            outline="#16833a",
            callback=self._start_from_selected_line,
            emit_on_none=False,
        )

    def _panel(self, x, y, width, height, title):
        self._rect(x, y, x + width, y + height, fill="#ffffff", outline="#d8e1ef", width=2)
        self._text(x + 28, y + 26, title, fill="#172033", font=(self.default_font or "Helvetica", 22, "bold"))

    def _set_status(self, status):
        self.machine_status = status
        self._refresh_execution_progress()

    def _status_fill(self):
        if self.machine_status in ("Running", "Simulating", "Sending", "Complete"):
            return "#8ee6a8"
        return "#f6d365"

    def _execution_row_text(self, idx):
        marker = ">" if idx == self.current_line else " "
        return "{:04d} {} {}".format(idx + 1, marker, self.execution_lines[idx])

    def _refresh_execution_row(self, idx):
        if self._execution_line_list is None or idx is None:
            return
        if idx < 0 or idx >= len(self.execution_lines):
            return
        self._execution_line_list.delete(idx)
        self._execution_line_list.insert(idx, self._execution_row_text(idx))

    def _refresh_execution_list_selection(self):
        line_list = self._execution_line_list
        if line_list is None:
            return
        if line_list.size() != len(self.execution_lines):
            self._render()
            return

        old_current_line = self._displayed_current_line
        if old_current_line != self.current_line:
            self._refresh_execution_row(old_current_line)
            self._refresh_execution_row(self.current_line)
        else:
            self._refresh_execution_row(self.current_line)

        if self.execution_lines:
            line_list.selection_clear(0, tk.END)
            line_list.selection_set(self.selected_line)
            line_list.activate(self.selected_line)
            line_list.see(self.selected_line)
        self._displayed_current_line = self.current_line

    def _clear_preview_dynamic_items(self):
        for item in self._preview_dynamic_items:
            try:
                self.canvas.delete(item)
            except tk.TclError:
                pass
            try:
                self.canvas_items.remove(item)
            except ValueError:
                pass
        self._preview_dynamic_items = []

    def _refresh_preview_progress(self):
        try:
            self._clear_preview_dynamic_items()
            points = parse_acl_toolpath(self.execution_lines, settings=self.machine_settings)
            if points:
                mapped_points = self._map_toolpath_points(points, 488, 216, 1248, 466)
                self._draw_toolpath_segments(points, mapped_points)
                self._draw_dispense_points(points, mapped_points)
                self._draw_current_tool_position(points, mapped_points)
                self._preview_text(
                    476,
                    482,
                    "{} moves  |  line {} / {}".format(
                        len(points),
                        min(self.current_line + 1, len(self.execution_lines)),
                        len(self.execution_lines),
                    ),
                    fill="#9fb2cc",
                    font=(self.default_font or "Helvetica", 16),
                )
            else:
                self._preview_text(
                    476,
                    482,
                    "No toolpath loaded",
                    fill="#9fb2cc",
                    font=(self.default_font or "Helvetica", 16),
                )
        except tk.TclError:
            self._render()

    def _refresh_execution_progress(self):
        dynamic_items = (
            self._status_text_item,
            self._progress_bar_item,
            self._progress_text_item,
            self._selected_line_text_item,
            self._current_line_text_item,
            self._progress_summary_text_item,
        )
        if any(item is None for item in dynamic_items):
            self._render()
            return
        if self._execution_line_list is None:
            self._render()
            return

        total_lines = len(self.execution_lines)
        selected_line = self.selected_line + 1 if total_lines else 0
        current_line = self.current_line + 1 if total_lines else 0

        try:
            self.canvas.itemconfig(
                self._status_text_item,
                text="STATUS: " + self.machine_status.upper(),
                fill=self._status_fill(),
            )
            self.canvas.coords(
                self._progress_bar_item,
                self._scaled(1392),
                self._scaled(924),
                self._scaled(1392 + int(464 * self.progress_percent / 100)),
                self._scaled(960),
            )
            self.canvas.itemconfig(self._progress_text_item, text=str(self.progress_percent) + "%")
            self._refresh_machine_position_fields()
            self.canvas.itemconfig(
                self._selected_line_text_item,
                text="Selected line: {} / {}".format(selected_line, total_lines),
            )
            self.canvas.itemconfig(
                self._current_line_text_item,
                text="Current line: {} / {}".format(current_line, total_lines),
            )
            self.canvas.itemconfig(self._progress_summary_text_item, text=self._machine_progress_summary())
            self._refresh_execution_list_selection()
            self._refresh_preview_progress()
        except tk.TclError:
            self._render()

    def _refresh_machine_position_fields(self):
        if set(self._machine_position_text_items.keys()) != {"X", "Y", "Z"}:
            self._render()
            return
        for axis, text_item in self._machine_position_text_items.items():
            self.canvas.itemconfig(text_item, text=self._format_position_value(axis))

    def _format_setting_value(self, value):
        if isinstance(value, float) and value.is_integer():
            return str(int(value))
        return str(value)

    def _format_position_value(self, axis):
        value = self.machine_position.get(axis)
        if value is None:
            return "--"
        try:
            return "{:.3f}".format(float(value))
        except (TypeError, ValueError):
            return str(value)

    def _machine_progress_summary(self):
        if not self.machine_progress:
            return ""
        state = self.machine_progress.get("state", "")
        sent_count = self.machine_progress.get("sent_count")
        total_count = self.machine_progress.get("total_count")
        line_index = self.machine_progress.get("line_index", self.machine_progress.get("last_line_index"))
        summary = "Machine report: {}".format(state)
        if line_index is not None:
            try:
                summary += " line {}".format(int(line_index) + 1)
            except (TypeError, ValueError):
                summary += " line {}".format(line_index)
        if sent_count is not None and total_count is not None:
            summary += " sent {}/{}".format(sent_count, total_count)
        return summary

    def _read_machine_settings(self):
        updated_settings = self.machine_settings.copy()
        for key, entry in self._machine_setting_entries.items():
            raw_value = entry.get().strip().replace(",", ".")
            try:
                if key == "SERIAL_PORT":
                    updated_settings[key] = raw_value
                elif key == "BAUD_RATE":
                    updated_settings[key] = int(float(raw_value))
                else:
                    updated_settings[key] = float(raw_value)
            except ValueError:
                self.machine_status = "Invalid input"
                return None
        self.machine_settings = updated_settings
        return updated_settings.copy()

    def _apply_machine_position(self, progress):
        position = progress.get("position", progress.get("machine_position"))
        if not isinstance(position, dict):
            return

        for axis in ("X", "Y", "Z"):
            found, value = self._position_axis_value(position, axis)
            if found:
                self.machine_position[axis] = value

    @staticmethod
    def _position_axis_value(position, axis):
        for key in (axis, axis.lower(), axis + "_MM", axis.lower() + "_mm"):
            if key in position:
                return True, position[key]
        return False, None

    def _machine_init(self, event):
        settings = self._read_machine_settings()
        if settings is None:
            self._render()
            return None
        if self.simulation_mode:
            self.machine_status = "Simulation"
            self._render()
            return {"settings": settings, "simulation_mode": True}
        self.machine_status = "Initialized"
        self._render()
        return {"settings": settings}

    def _jog(self, axis, direction):
        settings = self._read_machine_settings()
        if settings is None:
            self._render()
            return None
        distance = settings["jog_distance_mm"] * direction
        if self.simulation_mode:
            self.machine_status = "Sim Jog"
            self._render()
            return {
                "axis": axis,
                "distance_mm": distance,
                "settings": settings,
                "simulation_mode": True,
            }
        serial_error = get_serial_preflight_error(settings)
        if serial_error:
            self.machine_status = "Machine offline"
            self._render()
            return None
        self.machine_status = "Jogging"
        self._render()
        return {
            "axis": axis,
            "distance_mm": distance,
            "settings": settings,
        }

    def _current_command_payload(self):
        command = None
        if self.execution_lines:
            command = self.execution_lines[self.current_line]
        return {
            "active_file": self.active_file,
            "line_index": self.current_line,
            "command": command,
            "execution_lines": self.execution_lines,
            "settings": self.machine_settings.copy(),
            "simulation_mode": self.simulation_mode,
        }

    def apply_machine_progress(self, progress):
        self.machine_progress = progress or {}
        self._apply_machine_position(self.machine_progress)
        line_index = self.machine_progress.get("line_index", self.machine_progress.get("last_line_index"))
        if line_index is not None:
            try:
                self.current_line = int(line_index)
                self.selected_line = self.current_line
            except (TypeError, ValueError):
                pass
        self._normalize_line_positions()
        self._update_progress_from_current_line()

        state = self.machine_progress.get("state", "")
        status = self.machine_progress.get("status", "")
        if status == "error" or state == "FAILURE":
            self.machine_status = "Machine error"
        elif self.machine_progress.get("done"):
            self.machine_status = "Complete" if status == "sent" else "Machine done"
        elif line_index is not None:
            self.machine_status = "Sending"
        self._refresh_execution_progress()

    def _can_send_to_machine(self):
        settings = self._read_machine_settings()
        if settings is None:
            self._render()
            return False
        if not self.execution_lines:
            self.machine_status = "No program"
            self._render()
            return False
        if self.simulation_mode:
            return True
        serial_error = get_serial_preflight_error(settings)
        if serial_error:
            self.machine_status = "Machine offline"
            self._render()
            return False
        return True

    def _load_gerber(self, event):
        path = filedialog.askopenfilename(
            title="Load Gerber",
            filetypes=[("Gerber files", "*.gbr *.ger *.gtl *.gbl"), ("All files", "*.*")],
        )
        if path:
            settings = self._read_machine_settings()
            if settings is None:
                self._render()
                return None
            try:
                self.execution_lines = generate_acl_from_gerber(path, settings=settings)
            except Exception as exc:  # pylint: disable=W0718
                self.machine_status = "Load failed"
                self.execution_lines = [str(exc)]
                self.current_line = 0
                self.selected_line = 0
                self.progress_percent = 0
                self._render()
                return None
            self.active_file = path
            self.machine_status = "Ready"
            self.current_line = 0
            self.selected_line = 0
            self.progress_percent = 0
            self._render()
            return {
                "active_file": self.active_file,
                "execution_lines": self.execution_lines,
                "settings": settings,
                "simulation_mode": self.simulation_mode,
            }
        return None

    def _save_program(self, event):
        path = filedialog.asksaveasfilename(
            title="Save Program",
            defaultextension=".cnc",
            filetypes=[("CNC program", "*.cnc"), ("G-code", "*.gcode"), ("All files", "*.*")],
        )
        if path:
            with open(path, "w", encoding="utf-8") as program_file:
                program_file.write("\n".join(self.execution_lines))
            self.active_file = path
            self.machine_status = "Saved"
            self._render()

    def _start_process(self, event):
        if not self._can_send_to_machine():
            return None
        if self.simulation_mode:
            start_index = self.current_line if self.machine_status == "Paused" else 0
            self._start_simulation(start_index)
            return self._current_command_payload()
        self._cancel_simulation()
        self.machine_status = "Running"
        self.progress_percent = max(self.progress_percent, 5)
        self._refresh_execution_progress()
        return self._current_command_payload()

    def _start_from_selected_line(self, event):
        if not self._can_send_to_machine():
            return None
        if self.execution_lines:
            self.current_line = self.selected_line
            if self.simulation_mode:
                self._start_simulation(self.current_line)
                return self._current_command_payload()
            self._cancel_simulation()
            self.machine_status = "Running"
            self._update_progress_from_current_line()
        self._refresh_execution_progress()
        return self._current_command_payload()

    def _pause_process(self, event):
        self._cancel_simulation()
        self._set_status("Paused")
        return self._current_command_payload()

    def _stop_process(self, event):
        self._cancel_simulation()
        self.machine_status = "Stopped"
        self.progress_percent = 0
        self.current_line = 0
        self.selected_line = 0
        self._refresh_execution_progress()
        return self._current_command_payload()

    def _step_line(self, event):
        if not self._can_send_to_machine():
            return None
        self._cancel_simulation()
        if self.execution_lines:
            self.current_line = min(self.current_line + 1, len(self.execution_lines) - 1)
            self.selected_line = self.current_line
            self._update_progress_from_current_line()
            self.machine_status = "Sim Step" if self.simulation_mode else "Stepping"
            self._refresh_execution_progress()
        return self._current_command_payload()

    def _toggle_simulation(self, event):
        self._cancel_simulation()
        self.simulation_mode = not self.simulation_mode
        if self.simulation_mode:
            self.machine_status = "Simulation"
        else:
            self.machine_status = "Ready" if self.execution_lines else "Idle"
        self._render()
        return None

    def _start_simulation(self, start_index):
        self._cancel_simulation()
        if not self.execution_lines:
            self.machine_status = "No program"
            self._refresh_execution_progress()
            return

        self.current_line = min(max(start_index, 0), len(self.execution_lines) - 1)
        self.selected_line = self.current_line
        self.machine_status = "Simulating"
        self._update_progress_from_current_line()
        self._refresh_execution_progress()
        if self.current_line < len(self.execution_lines) - 1:
            self._schedule_simulation_tick()
        else:
            self.machine_status = "Complete"
            self.progress_percent = 100
            self._refresh_execution_progress()

    def _schedule_simulation_tick(self):
        self._simulation_after_id = self.canvas.after(self._simulation_interval_ms, self._simulation_tick)

    def _simulation_tick(self):
        self._simulation_after_id = None
        if self.machine_status != "Simulating" or not self.execution_lines:
            return

        self.current_line = min(self.current_line + 1, len(self.execution_lines) - 1)
        self.selected_line = self.current_line
        self._update_progress_from_current_line()

        if self.current_line >= len(self.execution_lines) - 1:
            self.machine_status = "Complete"
            self.progress_percent = 100
            self._refresh_execution_progress()
            return

        self._refresh_execution_progress()
        self._schedule_simulation_tick()

    def _cancel_simulation(self):
        if self._simulation_after_id is None:
            return
        try:
            self.canvas.after_cancel(self._simulation_after_id)
        except tk.TclError:
            pass
        self._simulation_after_id = None

    def _select_execution_line(self, event):
        selection = event.widget.curselection()
        if selection:
            self.selected_line = selection[0]
            self._normalize_line_positions()
            self._refresh_execution_progress()

    def _normalize_line_positions(self):
        if not self.execution_lines:
            self.current_line = 0
            self.selected_line = 0
            self.progress_percent = 0
            return

        last_line = len(self.execution_lines) - 1
        self.current_line = min(max(self.current_line, 0), last_line)
        self.selected_line = min(max(self.selected_line, 0), last_line)

    def _update_progress_from_current_line(self):
        if self.execution_lines:
            self.progress_percent = int(self.current_line / max(len(self.execution_lines) - 1, 1) * 100)

    def _extruder_down(self, event):
        self.extruder_percent = max(50, self.extruder_percent - 5)
        self._render()

    def _extruder_up(self, event):
        self.extruder_percent = min(150, self.extruder_percent + 5)
        self._render()
