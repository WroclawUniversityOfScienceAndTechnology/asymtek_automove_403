#!/usr/bin/env python3

# pylint: disable=C0114
from src.business_logic.models.manager_model_base import ManagerModelBase
from src.cfg import Configuration


class EngineRoomModel(ManagerModelBase):
    """
    Engin room data preparation
    TODO! need implementation

    Returns:
        [type]: [description]
    """

    DEFAULT_MACHINE_SETTINGS = {
        "TIME_PER_SQMM": 1.0,
        "Z_OFFSET_PER_SEC": 0.2,
        "Z_SAFE_HEIGHT": 100.0,
        "STEPSXY_PER_MM": 100.0,
        "STEPSZ_PER_MM": 100.0,
        "jog_distance_mm": 1.0,
        "SERIAL_PORT": "/dev/ttyUSB0",
        "BAUD_RATE": 9600,
    }
    SERIAL_CONFIG_KEYS = ("SERIAL_PORT", "BAUD_RATE")

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
        for key in cls.SERIAL_CONFIG_KEYS:
            try:
                settings[key] = Configuration.get(key, section="USER")
            except RuntimeError:
                pass
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
