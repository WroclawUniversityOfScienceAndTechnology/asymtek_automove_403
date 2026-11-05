#!/usr/bin/env python3

# pylint: disable=C0114
from src.backend.machine_management import DEFAULT_MACHINE_SETTINGS as BACKEND_DEFAULT_MACHINE_SETTINGS
from src.business_logic.models.manager_model_base import ManagerModelBase
from src.cfg import Configuration


class EngineRoomModel(ManagerModelBase):
    """
    Engin room data preparation
    TODO! need implementation

    Returns:
        [type]: [description]
    """

    MACHINE_PARAMETER_KEYS = (
        "TIME_PER_SQMM",
        "DISPENSE_LARGE_PAD_MULTIPLIER",
        "Z_OFFSET_PER_SEC",
        "Z_SAFE_HEIGHT",
        "STEPSXY_PER_MM",
        "STEPSZ_PER_MM",
        "PROGRAM_STEP_DELAY_SEC",
    )
    JOG_DISTANCE_KEY = "jog_distance_mm"
    EDITABLE_MACHINE_SETTING_KEYS = MACHINE_PARAMETER_KEYS + (JOG_DISTANCE_KEY,)
    SERIAL_CONFIG_KEYS = ("SERIAL_PORT", "BAUD_RATE")
    CALIBRATION_KEYS = ("Z_BED_POINTS",)
    ORIGIN_CONFIG_KEYS = ("MACHINE_ORIGIN",)
    DEFAULT_MACHINE_SETTINGS = {
        "TIME_PER_SQMM": BACKEND_DEFAULT_MACHINE_SETTINGS["TIME_PER_SQMM"],
        "DISPENSE_LARGE_PAD_MULTIPLIER": BACKEND_DEFAULT_MACHINE_SETTINGS["DISPENSE_LARGE_PAD_MULTIPLIER"],
        "Z_OFFSET_PER_SEC": BACKEND_DEFAULT_MACHINE_SETTINGS["Z_OFFSET_PER_SEC"],
        "Z_SAFE_HEIGHT": BACKEND_DEFAULT_MACHINE_SETTINGS["Z_SAFE_HEIGHT"],
        "STEPSXY_PER_MM": BACKEND_DEFAULT_MACHINE_SETTINGS["STEPSXY_PER_MM"],
        "STEPSZ_PER_MM": BACKEND_DEFAULT_MACHINE_SETTINGS["STEPSZ_PER_MM"],
        "PROGRAM_STEP_DELAY_SEC": BACKEND_DEFAULT_MACHINE_SETTINGS["PROGRAM_STEP_DELAY_SEC"],
        "jog_distance_mm": 1.0,
        "SERIAL_PORT": BACKEND_DEFAULT_MACHINE_SETTINGS["SERIAL_PORT"],
        "BAUD_RATE": BACKEND_DEFAULT_MACHINE_SETTINGS["BAUD_RATE"],
        "Z_BED_POINTS": [],
        "MACHINE_ORIGIN": {"x": 0.0, "y": 0.0},
    }

    @classmethod
    def get_model_data(cls):
        """
        Get frontend data for the ACL CNC dashboard.

        Returns:
            [type]: [description]
        """
        _dict = {
            "background": False,
            "machine_status": "Idle",
            "active_file": "No Gerber loaded",
            "program_name": "ACL CNC",
            "extruder_percent": 100,
            "progress_percent": 0,
            "simulation_mode": False,
            "machine_settings": cls.get_machine_settings(),
            "execution_lines": [],
            "language": cls.get_language(),
        }
        return _dict

    @classmethod
    def get_machine_settings(cls):
        settings = cls.DEFAULT_MACHINE_SETTINGS.copy()
        for key in cls.EDITABLE_MACHINE_SETTING_KEYS + cls.SERIAL_CONFIG_KEYS + cls.CALIBRATION_KEYS + cls.ORIGIN_CONFIG_KEYS:
            try:
                settings[key] = Configuration.get(key, section="USER")
            except RuntimeError:
                pass
        return settings

    @classmethod
    def save_machine_settings(cls, settings, keys=None):
        keys = keys or cls.EDITABLE_MACHINE_SETTING_KEYS
        for key in keys:
            if key in settings:
                Configuration.set(key, settings[key], section="USER")

    @classmethod
    def restore_default_machine_settings(cls):
        settings = cls.get_machine_settings()
        for key in cls.EDITABLE_MACHINE_SETTING_KEYS:
            settings[key] = cls.DEFAULT_MACHINE_SETTINGS[key]
        cls.save_machine_settings(settings, keys=cls.EDITABLE_MACHINE_SETTING_KEYS)
        return settings

    @classmethod
    def _get_execution_lines(cls):
        commands = [
            "LOAD GERBER board_top.gbr",
            "HOME X Y Z",
            "SET EXTRUDER 100%",
            "MOVE X12.500 Y8.000 F1800",
            "DISPENSE T0.180",
            "MOVE X18.250 Y8.000 F1800",
            "DISPENSE T0.180",
            "MOVE X18.250 Y13.500 F1800",
            "DISPENSE T0.160",
            "MOVE X26.100 Y13.500 F1800",
            "DISPENSE T0.160",
            "MOVE X26.100 Y21.250 F1800",
            "DISPENSE T0.140",
            "MOVE X34.750 Y21.250 F1800",
            "DISPENSE T0.140",
            "MOVE X34.750 Y28.000 F1800",
            "DISPENSE T0.120",
            "MOVE X42.500 Y28.000 F1800",
            "DISPENSE T0.120",
            "MOVE X42.500 Y36.400 F1800",
            "DISPENSE T0.100",
            "MOVE X50.250 Y36.400 F1800",
            "DISPENSE T0.100",
            "RAISE Z2.000",
            "MOVE X0.000 Y0.000 F2200",
            "WAIT FOR BACKEND",
        ]
        return ["N{:03d} {}".format((idx + 1) * 10, command) for idx, command in enumerate(commands)]
