#!/usr/bin/env python

# pylint: disable=C0114, W0613
import math
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from src.backend.machine_management import (
    build_machine_origin_command,
    fit_fiducial_transform,
    generate_acl_from_gerber,
    get_serial_preflight_error,
    list_serial_ports,
    parse_acl_toolpath,
)
from src.business_logic.models.engine_room_model import EngineRoomModel
from src.cfg import Configuration, ConfigVerificator
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
        self.gerber_path = None
        self.gerber_mirrored = False
        self._gerber_mirror_var = tk.BooleanVar(master=self.canvas, value=False)
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
        self._nozzle_cleaning_time_entry = None
        self.nozzle_cleaning_time = 1.0
        self._machine_position_text_items = {}
        self._serial_settings_dialog = None
        self._z_compensation_dialog = None
        self._xy_fiducial_dialog = None
        self._program_origin_dialog = None
        self.xy_calibration_active = False
        self.xy_transform = None
        self._calibration_move_callback = None
        self._status_text_item = None
        self._progress_bar_item = None
        self._progress_text_item = None
        self._selected_line_text_item = None
        self._current_line_text_item = None
        self._progress_summary_text_item = None
        self._execution_line_list = None
        self._displayed_current_line = None
        self._preview_dynamic_items = []
        self._machine_settings_autosave_after_id = None
        self._machine_settings_autosave_delay_ms = 500
        self.machine_settings = EngineRoomModel.DEFAULT_MACHINE_SETTINGS.copy()
        self.machine_setting_fields = [
            ("TIME_PER_SQMM", "TIME_PER_SQMM", "s/mm2"),
            ("Z_OFFSET_PER_SEC", "Z_OFFSET_PER_SEC", "mm/s"),
            ("Z_SAFE_HEIGHT", "Z_SAFE_HEIGHT", "mm"),
            ("STEPSXY_PER_MM", "STEPSXY_PER_MM", "steps/mm"),
            ("STEPSZ_PER_MM", "STEPSZ_PER_MM", "steps/mm"),
            ("PROGRAM_STEP_DELAY_SEC", "PROGRAM_STEP_DELAY_SEC", "s"),
        ]
        self._position_poll_id = None
        self._position_poll_interval_ms = 5000

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
        self._schedule_position_poll()

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
        self._close_z_compensation_dialog()
        self._close_xy_fiducial_calibration_dialog()
        self._close_program_origin_dialog()
        self._cancel_machine_settings_autosave()
        self._cancel_simulation()
        self._cancel_position_poll()
        super().finish()

    def _add_raw(self, item):
        self.canvas_items.append(item)
        return item

    def _add_preview_dynamic_raw(self, item):
        self.canvas_items.append(item)
        self._preview_dynamic_items.append(item)
        return item

    def delete_canvas_items(self):
        self._cancel_machine_settings_autosave()
        for widget in self._embedded_widgets:
            try:
                widget.destroy()
            except tk.TclError:
                pass
        self._embedded_widgets = []
        self._machine_setting_entries = {}
        self._nozzle_cleaning_time_entry = None
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
        self._button(52, 184, 304, 42, "Load Gerber", "load_gerber", callback=self._load_gerber)
        self._button(
            52,
            234,
            304,
            42,
            "Reload Gerber",
            "load_gerber",
            fill="#0b6e99",
            outline="#0b6e99",
            callback=self._reload_gerber,
            emit_on_none=False,
        )
        self._button(
            52,
            284,
            304,
            42,
            "Save Program",
            "save_program",
            fill="#40536d",
            outline="#40536d",
            callback=self._save_program,
        )
        self._gerber_mirror_var.set(self.gerber_mirrored)
        mirror_checkbox = tk.Checkbutton(
            self.canvas,
            text="Mirror Gerber",
            variable=self._gerber_mirror_var,
            command=self._toggle_gerber_mirror,
            anchor=tk.W,
            bg="#ffffff",
            fg="#172033",
            activebackground="#ffffff",
            activeforeground="#172033",
            selectcolor="#ffffff",
            font=self._font((self.default_font or "Helvetica", 12)),
            padx=self._scaled(4),
            pady=0,
        )
        self._window(52, 330, 304, 30, mirror_checkbox, anchor=tk.NW)

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
            140,
            58,
            "INIT",
            "machine_init",
            fill="#16833a",
            outline="#16833a",
            callback=self._machine_init,
            emit_on_none=False,
        )
        self._button(
            216,
            728,
            140,
            58,
            "HOME",
            "machine_home",
            fill="#16833a",
            outline="#16833a",
            callback=self._machine_home,
            emit_on_none=False,
        )

        self._button(
            52,
            806,
            140,
            58,
            "SET ORIGIN",
            "set_origin",
            fill="#16833a",
            outline="#16833a",
            callback=self._set_origin,
            emit_on_none=False,
        )
        self._button(
            216,
            806,
            140,
            58,
            "GO ORIGIN",
            "go_origin",
            fill="#16833a",
            outline="#16833a",
            callback=self._go_machine_origin,
            emit_on_none=False,
        )

        self._text(52, 870, "Extruder time", fill="#526071", font=(self.default_font or "Helvetica", 16, "bold"))
        self._button(52, 914, 74, 58, "-5%", "extruder_minus", fill="#40536d", callback=self._extruder_down)
        self._rect(144, 914, 264, 912, fill="#ffffff", outline="#cad5e3", width=2)
        self._text(
            204,
            943,
            str(self.extruder_percent) + "%",
            fill="#172033",
            font=(self.default_font or "Helvetica", 22, "bold"),
            anchor=tk.CENTER,
        )
        self._button(282, 914, 74, 58, "+5%", "extruder_plus", fill="#40536d", callback=self._extruder_up)
        self._text(
            52,
            982,
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
            self._preview_oval(x - 4, y - 4, x + 4, y + 4, fill="#f97316", outline="#fed7aa")

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
            nozzle_y - 11,
            nozzle_x - 7,
            nozzle_y + 7,
            nozzle_x + 7,
            nozzle_y + 7,
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
            808,
            72,
            54,
            "Z-",
            "machine_jog_z_plus",
            fill="#40536d",
            callback=lambda event: self._jog("Z", 1),
            emit_on_none=False,
        )
        self._button(
            1222,
            744,
            72,
            54,
            "Z+",
            "machine_jog_z_minus",
            fill="#40536d",
            callback=lambda event: self._jog("Z", -1),
            emit_on_none=False,
        )
        self._text(902, 870, "Nozzle cleaning", fill="#526071", font=(self.default_font or "Helvetica", 16, "bold"))
        self._text(902, 920, "Open time (s)", fill="#172033", font=(self.default_font or "Helvetica", 13, "bold"))
        self._nozzle_cleaning_time_entry = tk.Entry(
            self.canvas,
            font=self._font((self.default_font or "Helvetica", 13)),
            justify=tk.CENTER,
        )
        self._nozzle_cleaning_time_entry.insert(0, str(self.nozzle_cleaning_time))
        self._window(1030, 910, 84, 34, self._nozzle_cleaning_time_entry, anchor=tk.NW)
        self._button(
            1126,
            902,
            168,
            50,
            "Nozzle Cleaning",
            "nozzle_cleaning",
            fill="#40536d",
            outline="#40536d",
            font=(self.default_font or "Helvetica", 12, "bold"),
            callback=self._nozzle_cleaning,
            emit_on_none=False,
        )
        self._add_machine_position_row(y=966)

    def _add_machine_position_row(self, y=924):
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
        entry.bind("<KeyRelease>", self._schedule_machine_settings_autosave)
        entry.bind("<FocusOut>", self._autosave_machine_settings_from_entries)
        entry.bind("<Return>", self._autosave_machine_settings_from_entries)
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

    def open_z_compensation_dialog(self, parent=None):
        if self._z_compensation_dialog is not None:
            try:
                self._z_compensation_dialog.lift()
                self._z_compensation_dialog.focus_force()
                return
            except tk.TclError:
                self._z_compensation_dialog = None
        parent = parent or self.canvas.winfo_toplevel()
        dialog = tk.Toplevel(parent)
        self._z_compensation_dialog = dialog
        dialog.title("Z Compensation")
        dialog.resizable(False, False)
        dialog.transient(parent)
        width_var = tk.StringVar(value="100")
        height_var = tk.StringVar(value="100")
        edge_offset_var = tk.StringVar(value="5")
        count_var = tk.StringVar(value="9")
        save_calibration_var = tk.BooleanVar(value=True)
        content = ttk.Frame(dialog, padding=16)
        content.grid(row=0, column=0, sticky="nsew")
        for row, (label, var) in enumerate((
            ("Board width (mm)", width_var),
            ("Board height (mm)", height_var),
            ("Edge offset (mm)", edge_offset_var),
        )):
            ttk.Label(content, text=label).grid(row=row, column=0, padx=(0, 12), pady=6, sticky="w")
            ttk.Entry(content, textvariable=var, width=12).grid(row=row, column=1, pady=6, sticky="w")
        ttk.Label(content, text="Control points").grid(row=3, column=0, padx=(0, 12), pady=6, sticky="w")
        ttk.Combobox(content, textvariable=count_var, values=("4", "9", "16", "25"), state="readonly", width=9).grid(row=3, column=1, pady=6, sticky="w")
        save_calibration_checkbox = ttk.Checkbutton(
            content,
            text="Save calibration after app restart",
            variable=save_calibration_var,
            command=lambda: save_completed_calibration_preference(),
        )
        save_calibration_checkbox.grid(row=4, column=0, columnspan=2, pady=(6, 0), sticky="w")
        status_var = tk.StringVar(value="Set machine origin at the board corner, enter board size, then start calibration.")
        ttk.Label(content, textvariable=status_var, wraplength=390).grid(row=5, column=0, columnspan=2, pady=(8, 12), sticky="w")
        points = []
        index = {"value": 0}
        calibration = {"save_after_restart": True, "complete": False}

        def send_calibration_command(command, on_success, command_timeout=0.5, on_failure=None):
            settings = self._read_machine_settings(update_status=False)
            if settings is None:
                if on_failure and dialog.winfo_exists():
                    on_failure()
                return
            settings["COMMAND_TIMEOUT_SEC"] = command_timeout

            def after_command(completed_progress):
                if not dialog.winfo_exists() or self._z_compensation_dialog is not dialog:
                    return
                if completed_progress.get("status") == "sent":
                    on_success(completed_progress)
                    return
                error = completed_progress.get("error", "No ACL response")
                status_var.set("Machine response error: {}. Restart calibration or retry the Z read.".format(error))
                if on_failure:
                    on_failure()

            self._calibration_move_callback = after_command
            self._emit("calibration_command", payload={"command": command, "settings": settings})

        def close_dialog():
            self._z_compensation_dialog = None
            self._calibration_move_callback = None
            dialog.destroy()

        def save_completed_calibration_preference():
            if not calibration["complete"]:
                return
            persisted_points = (
                self.machine_settings.get("Z_BED_POINTS", [])
                if save_calibration_var.get()
                else []
            )
            EngineRoomModel.save_machine_settings(
                {"Z_BED_POINTS": persisted_points},
                keys=("Z_BED_POINTS",),
            )

        def start():
            try:
                board_w = float(width_var.get())
                board_h = float(height_var.get())
                edge_offset = float(edge_offset_var.get())
                count = int(count_var.get())
                if board_w <= 0 or board_h <= 0 or edge_offset < 0 or board_w <= 2 * edge_offset or board_h <= 2 * edge_offset or count not in (4, 9, 16, 25):
                    raise ValueError
            except ValueError:
                messagebox.showerror("Z Compensation", "Enter positive board dimensions and select a supported point count.", parent=dialog)
                return
            side = int(count ** 0.5)
            points.clear()
            for row in range(side):
                for col in range(side):
                    points.append((
                        edge_offset + (board_w - 2 * edge_offset) * col / (side - 1),
                        edge_offset + (board_h - 2 * edge_offset) * row / (side - 1),
                    ))
            index["value"] = 0
            self._z_bed_points = []
            calibration["complete"] = False
            calibration["save_after_restart"] = save_calibration_var.get()
            save_calibration_checkbox.configure(state=tk.DISABLED)
            if not calibration["save_after_restart"]:
                # Clear a previous persistent calibration so an interrupted run
                # with saving disabled cannot restore stale bed measurements.
                EngineRoomModel.save_machine_settings({"Z_BED_POINTS": []}, keys=("Z_BED_POINTS",))
            status_var.set("Reading current Z before moving to the first point…")
            send_calibration_command("OC; OZ;", visit_point)

        def visit_point(_completed_progress=None):
            i = index["value"]
            if i >= len(points):
                status_var.set("Calibration complete. {} points recorded.".format(len(points)))
                self.machine_settings["Z_BED_POINTS"] = list(self._z_bed_points)
                persisted_points = self._z_bed_points if calibration["save_after_restart"] else []
                EngineRoomModel.save_machine_settings(
                    {"Z_BED_POINTS": persisted_points},
                    keys=("Z_BED_POINTS",),
                )
                calibration["complete"] = True
                save_calibration_checkbox.configure(state=tk.NORMAL)
                return
            x, y = points[i]
            settings = self._read_machine_settings(update_status=False)
            if settings is None:
                return
            target_x_steps = x * settings["STEPSXY_PER_MM"]
            target_y_steps = y * settings["STEPSXY_PER_MM"]
            safe = settings["Z_SAFE_HEIGHT"] * settings["STEPSZ_PER_MM"]
            confirm_button.configure(state=tk.DISABLED)
            status_var.set("Moving to point {} / {} at X {:.2f}, Y {:.2f} mm…".format(i + 1, len(points), x, y))

            def arrived(_completed_progress=None):
                confirm_button.configure(state=tk.NORMAL)
                status_var.set("Point {} / {} at X {:.2f}, Y {:.2f} mm. Lower Z manually, then confirm to continue.".format(i + 1, len(points), x, y))

            # ACL XY coordinates are sent in motor steps: 1 mm = 39.37 steps.
            # The move task's response is the only arrival signal; XY is not polled
            # or compared against the target.
            command = "MZ -{:.3f}; MA {:.3f}, {:.3f};".format(
                safe,
                target_x_steps,
                target_y_steps,
            )
            # The task reads position once after MA. Give the controller time to
            # finish the physical move before its response is expected.
            send_calibration_command(command, arrived, command_timeout=30.0)

        def record_confirmed_height(completed_progress=None):
            if not points or index["value"] >= len(points):
                return
            if not completed_progress or completed_progress.get("status") != "sent":
                status_var.set("Could not read machine position. Check the connection and try again.")
                confirm_button.configure(state=tk.NORMAL)
                return
            machine_position = completed_progress.get("machine_position") or {}
            position = machine_position.get("Z", machine_position.get("z"))
            try:
                z_steps = float(position) * float(self.machine_settings.get("STEPSZ_PER_MM", 1))
            except (TypeError, ValueError):
                messagebox.showerror("Z Compensation", "Current Z position is not available. Wait for the position display to update.", parent=dialog)
                confirm_button.configure(state=tk.NORMAL)
                return
            x, y = points[index["value"]]
            self._z_bed_points.append({"x": x, "y": y, "z_steps": z_steps})
            index["value"] += 1
            visit_point()

        def confirm_point():
            if not points or index["value"] >= len(points):
                return
            confirm_button.configure(state=tk.DISABLED)
            status_var.set("Reading current Z position from the machine…")
            send_calibration_command(
                "OC; OZ;",
                record_confirmed_height,
                on_failure=lambda: confirm_button.configure(state=tk.NORMAL),
            )

        buttons = ttk.Frame(content)
        buttons.grid(row=6, column=0, columnspan=2, sticky="e")
        ttk.Button(buttons, text="Start / restart", command=start).grid(row=0, column=0, padx=(0, 8))
        confirm_button = ttk.Button(buttons, text="Confirm height / next point", command=confirm_point, state=tk.DISABLED)
        confirm_button.grid(row=0, column=1, padx=(0, 8))
        ttk.Button(buttons, text="Close", command=close_dialog).grid(row=0, column=2)
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.grab_set()
        dialog.update_idletasks()
        x = parent.winfo_rootx() + max((parent.winfo_width() - dialog.winfo_width()) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - dialog.winfo_height()) // 2, 0)
        dialog.geometry("+{}+{}".format(x, y))

    def _close_z_compensation_dialog(self):
        dialog = self._z_compensation_dialog
        self._z_compensation_dialog = None
        self._calibration_move_callback = None
        if dialog is not None:
            try:
                if dialog.winfo_exists():
                    dialog.destroy()
            except tk.TclError:
                pass

    def open_xy_fiducial_calibration_dialog(self, parent=None):
        """Guide the operator through origin setup and manual XY fiducial alignment."""
        if self._xy_fiducial_dialog is not None:
            try:
                self._xy_fiducial_dialog.lift()
                self._xy_fiducial_dialog.focus_force()
                return
            except tk.TclError:
                self._xy_fiducial_dialog = None
        parent = parent or self.canvas.winfo_toplevel()
        dialog = tk.Toplevel(parent)
        self._xy_fiducial_dialog = dialog
        dialog.title("XY fiducial calibration")
        dialog.resizable(False, False)
        dialog.transient(parent)
        content = ttk.Frame(dialog, padding=16)
        content.grid(row=0, column=0, sticky="nsew")
        count_var = tk.StringVar(value="2")
        ttk.Label(content, text="Fiducials").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=5)
        count_combo = ttk.Combobox(content, textvariable=count_var, values=("2", "3", "4"), state="readonly", width=6)
        count_combo.grid(row=0, column=1, sticky="w", pady=5)
        ttk.Label(content, text="Set origin on the machine panel before calibration. Enter fiducial coordinates in mm.", wraplength=500).grid(
            row=1, column=0, columnspan=4, sticky="w", pady=(4, 10)
        )
        x_var, y_var = tk.StringVar(), tk.StringVar()
        ttk.Label(content, text="X (mm)").grid(row=2, column=0, sticky="e", padx=4, pady=5)
        ttk.Entry(content, textvariable=x_var, width=12).grid(row=2, column=1, sticky="w", pady=5)
        ttk.Label(content, text="Y (mm)").grid(row=2, column=2, sticky="e", padx=4, pady=5)
        ttk.Entry(content, textvariable=y_var, width=12).grid(row=2, column=3, sticky="w", pady=5)
        status_var = tk.StringVar(value="Enter fiducial 1 coordinates, then choose Go to fiducial.")
        ttk.Label(content, textvariable=status_var, wraplength=500).grid(row=3, column=0, columnspan=4, sticky="w", pady=(10, 8))
        points = []
        state = {
            "index": 0,
            "count": None,
            "z_mm": None,
            "z_reference_mm": None,
            "safe_z_target_mm": None,
            "busy": False,
            "point_ready": False,
            "complete": False,
        }

        def close_dialog():
            if self._xy_fiducial_dialog is dialog:
                self._xy_fiducial_dialog = None
                self.xy_calibration_active = False
                self._calibration_move_callback = None
            dialog.destroy()

        def read_settings():
            settings = self._read_machine_settings(update_status=False)
            if settings is None:
                status_var.set("Check machine settings before continuing.")
                return None
            if self.simulation_mode:
                status_var.set("Turn off simulation mode to move the real machine.")
                return None
            error = get_serial_preflight_error(settings)
            if error:
                status_var.set("Machine connection error: {}".format(error))
                return None
            return settings

        def dispatch(command, on_success, timeout=30.0):
            settings = read_settings()
            if settings is None or state["busy"]:
                return
            settings["COMMAND_TIMEOUT_SEC"] = timeout
            state["busy"] = True

            def completed(progress):
                if not dialog.winfo_exists() or self._xy_fiducial_dialog is not dialog:
                    return
                state["busy"] = False
                if progress.get("status") != "sent":
                    status_var.set("Machine error: {}. Retry the last step.".format(progress.get("error", "No ACL response")))
                    return
                position = progress.get("machine_position") or {}
                try:
                    state["z_mm"] = float(position.get("z", position.get("Z")))
                except (TypeError, ValueError):
                    pass
                on_success(progress)

            self._calibration_move_callback = completed
            self._emit("calibration_command", payload={"command": command, "settings": settings})

        def go_to_fiducial():
            if not self.gerber_path:
                messagebox.showerror("XY calibration", "Load a Gerber file before calibrating fiducials.", parent=dialog)
                return
            try:
                count = int(count_var.get())
                x_mm = float(x_var.get().replace(",", "."))
                y_mm = float(y_var.get().replace(",", "."))
                if count not in (2, 3, 4) or not math.isfinite(x_mm) or not math.isfinite(y_mm):
                    raise ValueError
            except ValueError:
                messagebox.showerror("XY calibration", "Enter valid X and Y coordinates for this fiducial.", parent=dialog)
                return

            if state["complete"] or state["count"] != count:
                points.clear()
                state["index"] = 0
                state["count"] = count
                state["complete"] = False
                state["z_reference_mm"] = None
                state["safe_z_target_mm"] = None
                if self.xy_transform is not None:
                    self.xy_transform = None
                    self._generate_gerber_program(self.gerber_path)
            # A retry replaces the active nominal point and discards later samples.
            del points[state["index"]:]
            points.append({"x": x_mm, "y": y_mm})
            state["point_ready"] = False
            self.xy_calibration_active = True
            index = state["index"]
            settings = read_settings()
            if settings is None:
                return

            status_var.set("Moving safely to fiducial {} / {} at X {:.3f}, Y {:.3f} mm…".format(index + 1, count, x_mm, y_mm))

            def move_after_position_read(progress):
                position = progress.get("machine_position") or {}
                try:
                    current_z_mm = float(position.get("z", position.get("Z")))
                except (TypeError, ValueError):
                    status_var.set("Current Z position is unavailable. Check the machine panel and retry.")
                    return
                if state["z_reference_mm"] is None:
                    state["z_reference_mm"] = current_z_mm
                    state["safe_z_target_mm"] = current_z_mm - float(settings["Z_SAFE_HEIGHT"])
                z_delta_steps = (
                    state["safe_z_target_mm"] - current_z_mm
                ) * float(settings["STEPSZ_PER_MM"])
                target_x = x_mm * float(settings["STEPSXY_PER_MM"])
                target_y = y_mm * float(settings["STEPSXY_PER_MM"])
                z_command = "MZ {:.3f}; ".format(z_delta_steps) if abs(z_delta_steps) > 1e-6 else ""
                command = "{}MA {:.3f}, {:.3f};".format(z_command, target_x, target_y)
                dispatch(command, lambda _result: arrived(index, x_mm, y_mm), timeout=30.0)

            # OC reports coordinates in the operator-set origin. OA reports
            # raw microsteps from machine home, so it would add the board's
            # distance from home to the fitted XY translation.
            dispatch("OC; OZ;", move_after_position_read, timeout=5.0)

        def arrived(index, x_mm, y_mm):
            state["point_ready"] = True
            status_var.set("Fiducial {} / {}: use the machine panel to position XY over its center, then choose Save fiducial.".format(index + 1, state["count"]))

        def record_point():
            if state["busy"] or not state["point_ready"] or state["index"] >= len(points):
                return
            status_var.set("Reading machine coordinates for fiducial {}…".format(state["index"] + 1))

            def recorded(progress):
                position = progress.get("machine_position") or {}
                try:
                    points[state["index"]]["machine_x"] = float(position.get("x", position.get("X")))
                    points[state["index"]]["machine_y"] = float(position.get("y", position.get("Y")))
                except (TypeError, ValueError):
                    status_var.set("XY position unavailable. Check the machine position readout and retry.")
                    return
                state["index"] += 1
                state["point_ready"] = False
                if state["index"] < state["count"]:
                    x_var.set("")
                    y_var.set("")
                    status_var.set("Fiducial saved. Enter fiducial {} / {} coordinates, then choose Go to fiducial.".format(
                        state["index"] + 1, state["count"]
                    ))
                    return
                try:
                    transform = fit_fiducial_transform(points)
                except ValueError as exc:
                    status_var.set("Calibration could not be calculated: {}".format(exc))
                    return
                self.xy_transform = transform
                generated_program = self._generate_gerber_program(self.gerber_path)
                state["complete"] = True
                angle_deg = math.degrees(transform["angle_rad"])
                if generated_program is None:
                    status_var.set(
                        "Calibration complete. Rotation {:+.4f}°, translation X {:+.3f} mm, Y {:+.3f} mm; Gerber commands could not be regenerated.".format(
                            angle_deg,
                            transform["offset_x_mm"],
                            transform["offset_y_mm"],
                        )
                    )
                else:
                    status_var.set(
                        "Calibration complete. Rotation {:+.4f}°, translation X {:+.3f} mm, Y {:+.3f} mm. Machine commands regenerated.".format(
                            angle_deg,
                            transform["offset_x_mm"],
                            transform["offset_y_mm"],
                        )
                    )

            dispatch("OC; OZ;", recorded, timeout=5.0)

        buttons = ttk.Frame(content)
        buttons.grid(row=4, column=0, columnspan=4, sticky="ew", pady=(6, 0))
        for label, command in (
            ("Go to fiducial", go_to_fiducial),
            ("Save fiducial", record_point),
            ("Close", close_dialog),
        ):
            ttk.Button(buttons, text=label, command=command).pack(
                side=tk.LEFT, expand=True, fill=tk.X, padx=6
            )
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.grab_set()
        dialog.update_idletasks()
        x = parent.winfo_rootx() + max((parent.winfo_width() - dialog.winfo_width()) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - dialog.winfo_height()) // 2, 0)
        dialog.geometry("+{}+{}".format(x, y))

    def open_program_origin_dialog(self, parent=None):
        if self._program_origin_dialog is not None:
            try:
                self._program_origin_dialog.lift()
                self._program_origin_dialog.focus_force()
                return
            except tk.TclError:
                self._program_origin_dialog = None
        parent = parent or self.canvas.winfo_toplevel()
        dialog = tk.Toplevel(parent)
        self._program_origin_dialog = dialog
        dialog.title("Set Program Origin")
        dialog.resizable(False, False)
        dialog.transient(parent)
        content = ttk.Frame(dialog, padding=16)
        content.grid(row=0, column=0, sticky="nsew")
        ttk.Label(content, text="Saved machine origin coordinates from home (mm):").grid(
            row=0, column=0, columnspan=4, sticky="w", pady=(0, 8)
        )
        origin = self.machine_settings["MACHINE_ORIGIN"]
        x_var = tk.StringVar(value=str(origin["x"]))
        y_var = tk.StringVar(value=str(origin["y"]))
        ttk.Label(content, text="X (mm)").grid(row=1, column=0, sticky="e", padx=4, pady=5)
        ttk.Entry(content, textvariable=x_var, width=12).grid(row=1, column=1, sticky="w", pady=5)
        ttk.Label(content, text="Y (mm)").grid(row=1, column=2, sticky="e", padx=4, pady=5)
        ttk.Entry(content, textvariable=y_var, width=12).grid(row=1, column=3, sticky="w", pady=5)
        status_var = tk.StringVar(value="Adjust X and Y, then save and send the origin to the machine.")
        ttk.Label(content, textvariable=status_var, wraplength=520).grid(
            row=2, column=0, columnspan=4, sticky="w", pady=(8, 10)
        )
        state = {"busy": False}

        def close_dialog():
            if self._program_origin_dialog is dialog:
                self._program_origin_dialog = None
            dialog.destroy()

        def save_origin():
            if state["busy"] or self._calibration_move_callback is not None:
                status_var.set("Wait for the current machine command to finish.")
                return
            try:
                new_origin = {"x": float(x_var.get().replace(",", ".")),
                              "y": float(y_var.get().replace(",", "."))}
            except ValueError:
                messagebox.showerror("Set Program Origin", "Enter valid X and Y coordinates in mm.", parent=dialog)
                return
            settings = self._read_machine_settings(update_status=False)
            if settings is None or self.simulation_mode:
                status_var.set("Check machine settings and turn off simulation mode before saving the origin.")
                return
            state["busy"] = True
            status_var.set("Saving and sending the machine origin…")

            def completed(success, status):
                if self._program_origin_dialog is not dialog:
                    return
                state["busy"] = False
                status_var.set(status)
                if success:
                    saved_origin = self.machine_settings["MACHINE_ORIGIN"]
                    x_var.set(str(saved_origin["x"]))
                    y_var.set(str(saved_origin["y"]))

            self._save_and_set_machine_origin(new_origin, settings, completed)

        buttons = ttk.Frame(content)
        buttons.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(4, 0))
        for label, command in (
            ("Save and send to machine", save_origin),
            ("Close", close_dialog),
        ):
            ttk.Button(buttons, text=label, command=command).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=4)
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
        dialog.bind("<Escape>", lambda _event: close_dialog())
        dialog.bind("<Return>", lambda _event: save_origin())
        dialog.grab_set()
        dialog.update_idletasks()
        x = parent.winfo_rootx() + max((parent.winfo_width() - dialog.winfo_width()) // 2, 0)
        y = parent.winfo_rooty() + max((parent.winfo_height() - dialog.winfo_height()) // 2, 0)
        dialog.geometry("+{}+{}".format(x, y))

    def _close_program_origin_dialog(self):
        dialog = self._program_origin_dialog
        self._program_origin_dialog = None
        if dialog is not None:
            try:
                if dialog.winfo_exists():
                    dialog.destroy()
            except tk.TclError:
                pass

    def _close_xy_fiducial_calibration_dialog(self):
        dialog = self._xy_fiducial_dialog
        self._xy_fiducial_dialog = None
        self.xy_calibration_active = False
        self._calibration_move_callback = None
        if dialog is not None:
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

        ttk.Label(content, text="7 data bits, even parity, 2 stop bits, RTS/CTS").grid(
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
            self._cancel_position_poll()
            self._poll_position()

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

    def _cancel_machine_settings_autosave(self):
        after_id = getattr(self, "_machine_settings_autosave_after_id", None)
        canvas = getattr(self, "canvas", None)
        if after_id is None or canvas is None:
            self._machine_settings_autosave_after_id = None
            return
        try:
            canvas.after_cancel(after_id)
        except tk.TclError:
            pass
        self._machine_settings_autosave_after_id = None

    def _schedule_machine_settings_autosave(self, event=None):
        self._cancel_machine_settings_autosave()
        canvas = getattr(self, "canvas", None)
        if canvas is None:
            self._autosave_machine_settings_from_entries(event)
            return
        self._machine_settings_autosave_after_id = canvas.after(
            getattr(self, "_machine_settings_autosave_delay_ms", 500),
            self._autosave_machine_settings_from_entries,
        )

    def _autosave_machine_settings_from_entries(self, event=None):
        self._machine_settings_autosave_after_id = None
        self._read_machine_settings(update_status=False, persist=True)

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

    def _read_machine_settings(self, update_status=True, persist=True):
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
                if ConfigVerificator.check(key) and not ConfigVerificator.verify(key, updated_settings[key]):
                    raise ValueError
            except ValueError:
                if update_status:
                    self.machine_status = "Invalid input"
                return None
        self.machine_settings = updated_settings
        if persist and self._machine_setting_entries:
            try:
                self._store_machine_settings(updated_settings)
            except RuntimeError:
                if update_status:
                    self.machine_status = "Invalid input"
                return None
        return updated_settings.copy()

    def _store_machine_settings(self, settings):
        EngineRoomModel.save_machine_settings(
            settings,
            keys=EngineRoomModel.EDITABLE_MACHINE_SETTING_KEYS,
        )

    def apply_machine_settings(self, settings, status=None):
        self.machine_settings.update(settings)
        if status:
            self.machine_status = status
        self._render()

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
        self.machine_status = "Initializing"
        self._render()
        return {"settings": settings}

    def _machine_home(self, event):
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

    def _set_origin(self, event):
        if self._calibration_move_callback is not None:
            return None
        settings = self._read_machine_settings()
        if settings is None:
            self._render()
            return None
        if self.simulation_mode:
            self.machine_status = "Simulation"
            self._render()
            return {"settings": settings, "simulation_mode": True}
        self.machine_status = "Setting origin"
        self._render()
        self._dispatch_machine_origin_command(
            "OA; OZ;",
            settings,
            lambda progress: self._apply_set_machine_origin(progress, settings),
            timeout=5.0,
        )
        return None

    def _apply_set_machine_origin(self, progress, settings):
        position = progress.get("machine_position") or {}
        try:
            origin = {"x": float(position.get("x", position.get("X"))),
                      "y": float(position.get("y", position.get("Y")))}
        except (TypeError, ValueError, KeyError):
            self.machine_status = "Origin failed: position unavailable"
            self._render()
            return
        self._save_and_set_machine_origin(origin, settings)

    def _save_and_set_machine_origin(self, origin, settings, on_complete=None):
        def completed(success, status):
            self._finish_machine_origin_command(status)
            if on_complete is not None:
                on_complete(success, status)

        try:
            command = build_machine_origin_command(origin, settings)
        except (TypeError, ValueError, KeyError) as exc:
            completed(False, "Origin failed: {}".format(exc))
            return
        origin = dict(origin)

        def save_origin(_progress):
            try:
                Configuration.set("MACHINE_ORIGIN", origin, section="USER")
            except (OSError, RuntimeError) as exc:
                completed(False, "Machine origin set, but local save failed: {}".format(exc))
                return
            self.machine_settings["MACHINE_ORIGIN"] = origin
            completed(True, "Machine origin set and saved")

        self._dispatch_machine_origin_command(
            command + " OA; OZ;",
            dict(settings, MACHINE_ORIGIN=origin),
            save_origin,
            on_error=lambda progress: completed(False, "Origin failed: {}".format(progress.get("error", "No ACL response"))),
        )

    def _go_machine_origin(self, event):
        if self._calibration_move_callback is not None:
            return None
        settings = self._read_machine_settings()
        if settings is None:
            self._render()
            return None
        if self.simulation_mode:
            self.machine_status = "Simulation"
            self._render()
            return {"settings": settings, "simulation_mode": True}
        try:
            origin_command = build_machine_origin_command(settings["MACHINE_ORIGIN"], settings)
        except (TypeError, ValueError, KeyError) as exc:
            self._finish_machine_origin_command("Origin move failed: {}".format(exc))
            return None
        self.machine_status = "Moving to origin"
        self._render()

        def move_from_position(progress):
            position = progress.get("machine_position") or {}
            try:
                current_z = float(position.get("z", position.get("Z")))
                safe_z = current_z - float(settings["Z_SAFE_HEIGHT"])
                z_delta_steps = (safe_z - current_z) * float(settings["STEPSZ_PER_MM"])
                if not math.isfinite(current_z) or not math.isfinite(z_delta_steps):
                    raise ValueError
            except (TypeError, ValueError, KeyError):
                self.machine_status = "Origin move failed: Z unavailable"
                self._render()
                return
            commands = []
            if abs(z_delta_steps) > 1e-6:
                commands.append("MZ {:.3f};".format(z_delta_steps))
            commands.append("MA 0, 0; OA; OZ;")
            self._dispatch_machine_origin_command(
                " ".join(commands),
                settings,
                lambda _result: self._finish_machine_origin_command("At machine origin"),
            )

        self._dispatch_machine_origin_command(origin_command + " OA; OZ;", settings, move_from_position, timeout=5.0)
        return None

    def _dispatch_machine_origin_command(self, command, settings, callback, timeout=30.0, on_error=None):
        settings = dict(settings)
        settings["COMMAND_TIMEOUT_SEC"] = timeout

        def completed(progress):
            if progress.get("status") != "sent":
                self._finish_machine_origin_command("Machine error: {}".format(progress.get("error", "No ACL response")))
                if on_error is not None:
                    on_error(progress)
                return
            callback(progress)

        error = get_serial_preflight_error(settings)
        if error:
            completed({"status": "error", "error": error})
            return
        self._calibration_move_callback = completed
        self._emit("calibration_command", payload={"command": command, "settings": settings})

    def _finish_machine_origin_command(self, status):
        self.machine_status = status
        self._render()

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

    def _nozzle_cleaning(self, event):
        settings = self._read_machine_settings()
        if settings is None:
            self._render()
            return None
        try:
            duration_sec = float(self._nozzle_cleaning_time_entry.get().strip().replace(",", "."))
            if not math.isfinite(duration_sec) or duration_sec <= 0:
                raise ValueError
        except (AttributeError, ValueError):
            self.machine_status = "Invalid valve time"
            self._render()
            return None
        self.nozzle_cleaning_time = duration_sec
        if self.simulation_mode:
            self.machine_status = "Simulation"
            self._render()
            return None
        serial_error = get_serial_preflight_error(settings)
        if serial_error:
            self.machine_status = "Machine offline"
            self._render()
            return None
        self.machine_status = "Cleaning nozzle"
        self._render()
        return {
            "execution_lines": [
                "CD2;",
                "WA {:.3f};".format(duration_sec),
                "CD0; OA; OZ;",
            ],
            "line_index": 0,
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
        if self.machine_progress.get("status") == "poll_error":
            return
        if self.machine_progress.get("status") == "poll_success":
            self._apply_machine_position(self.machine_progress)
            self._refresh_machine_position_fields()
            return
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
        elif status == "paused":
            self.machine_status = "Paused"
        elif status == "stopped":
            self.machine_status = "Stopped"
        elif self.machine_progress.get("done"):
            if status == "sent" and self.machine_progress.get("event") == "machine_initialized":
                self.machine_status = "Initialized"
            else:
                self.machine_status = "Complete" if status == "sent" else "Machine done"
        elif line_index is not None:
            self.machine_status = "Sending"
        self._refresh_execution_progress()
        if self.machine_progress.get("done") and self._calibration_move_callback:
            callback = self._calibration_move_callback
            completed_progress = dict(self.machine_progress)
            self._calibration_move_callback = None
            try:
                # The controller guards task IDs when a callback immediately
                # dispatches the next command, so run the completion handler now.
                callback(completed_progress)
            except tk.TclError:
                pass

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
            return self._generate_gerber_program(path)
        return None

    def _reload_gerber(self, event):
        if not self.gerber_path:
            self.machine_status = "No Gerber loaded"
            self._render()
            return None
        return self._generate_gerber_program(self.gerber_path)

    def _toggle_gerber_mirror(self):
        self.gerber_mirrored = bool(self._gerber_mirror_var.get())
        if self.gerber_path:
            self._generate_gerber_program(self.gerber_path)
        else:
            self._render()

    def _generate_gerber_program(self, path):
        if path != self.gerber_path:
            self.xy_transform = None
        settings = self._read_machine_settings()
        if settings is None:
            self._render()
            return {"simulation_mode": self.simulation_mode}
        try:
            execution_lines = generate_acl_from_gerber(
                path,
                settings=settings,
                xy_transform=self.xy_transform,
                mirror_x=self.gerber_mirrored,
            )
        except Exception as exc:  # pylint: disable=W0718
            self.machine_status = "Load failed"
            self.execution_lines = [str(exc)]
            self.current_line = 0
            self.selected_line = 0
            self.progress_percent = 0
            self._render()
            return {"simulation_mode": self.simulation_mode, "error": str(exc)}
        self.gerber_path = path
        self.active_file = path
        self.execution_lines = execution_lines
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
        if self.simulation_mode:
            self.machine_status = "Stopped"
            self.progress_percent = 0
            self.current_line = 0
            self.selected_line = 0
        else:
            self.machine_status = "Stopping"
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
        if not self.simulation_mode:
            self._cancel_position_poll()
            self._poll_position()
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

    def _schedule_position_poll(self):
        self._cancel_position_poll()
        self._position_poll_id = self.canvas.after(self._position_poll_interval_ms, self._poll_position)

    def _poll_position(self):
        self._position_poll_id = None

        idle_statuses = ("Idle", "Ready", "Complete", "Stopped", "Initialized", "Sim Jog", "Jogging",
                         "Serial set", "Machine origin set and saved", "At machine origin")

        if (
            self._z_compensation_dialog is None
            and self._xy_fiducial_dialog is None
            and self._program_origin_dialog is None
            and self._calibration_move_callback is None
            and not self.simulation_mode
            and self.machine_status in idle_statuses
        ):
            settings = self._read_machine_settings()
            if settings is not None:
                self._emit("machine_get_position", event={"settings": settings})
        self._schedule_position_poll()

    def _cancel_position_poll(self):
        if self._position_poll_id is not None:
            try:
                self.canvas.after_cancel(self._position_poll_id)
            except tk.TclError:
                pass
            self._position_poll_id = None
