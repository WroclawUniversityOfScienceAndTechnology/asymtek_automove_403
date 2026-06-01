from src.business_logic.models.engine_room_model import EngineRoomModel


def test_engine_room_model_reads_serial_settings_from_config(monkeypatch):
    config_values = {
        "TIME_PER_SQMM": 0.5,
        "Z_OFFSET_PER_SEC": 0.25,
        "Z_SAFE_HEIGHT": 12.0,
        "STEPSXY_PER_MM": 88.8,
        "STEPSZ_PER_MM": 22.0,
        "PROGRAM_STEP_DELAY_SEC": 0.1,
        "jog_distance_mm": 2.5,
        "SERIAL_PORT": "COM7",
        "BAUD_RATE": 115200,
    }

    monkeypatch.setattr(EngineRoomModel, "get_language", classmethod(lambda cls: "en"))
    monkeypatch.setattr(
        "src.business_logic.models.engine_room_model.Configuration.get",
        staticmethod(lambda key, section="USER": config_values[key]),
    )

    data = EngineRoomModel.get_model_data()

    assert data["machine_settings"]["SERIAL_PORT"] == "COM7"
    assert data["machine_settings"]["BAUD_RATE"] == 115200
    assert data["machine_settings"]["TIME_PER_SQMM"] == 0.5
    assert data["machine_settings"]["Z_OFFSET_PER_SEC"] == 0.25
    assert data["machine_settings"]["Z_SAFE_HEIGHT"] == 12.0
    assert data["machine_settings"]["STEPSXY_PER_MM"] == 88.8
    assert data["machine_settings"]["STEPSZ_PER_MM"] == 22.0
    assert data["machine_settings"]["PROGRAM_STEP_DELAY_SEC"] == 0.1
    assert data["machine_settings"]["jog_distance_mm"] == 2.5


def test_engine_room_model_restores_editable_machine_defaults_without_serial(monkeypatch):
    config_values = {
        "TIME_PER_SQMM": 0.5,
        "Z_OFFSET_PER_SEC": 0.25,
        "Z_SAFE_HEIGHT": 12.0,
        "STEPSXY_PER_MM": 88.8,
        "STEPSZ_PER_MM": 22.0,
        "PROGRAM_STEP_DELAY_SEC": 0.1,
        "jog_distance_mm": 2.5,
        "SERIAL_PORT": "COM7",
        "BAUD_RATE": 115200,
    }
    saved_values = []

    monkeypatch.setattr(
        "src.business_logic.models.engine_room_model.Configuration.get",
        staticmethod(lambda key, section="USER": config_values[key]),
    )
    monkeypatch.setattr(
        "src.business_logic.models.engine_room_model.Configuration.set",
        staticmethod(lambda key, value, section="USER": saved_values.append((key, value, section))),
    )

    settings = EngineRoomModel.restore_default_machine_settings()

    assert settings["SERIAL_PORT"] == "COM7"
    assert settings["BAUD_RATE"] == 115200
    assert settings["Z_SAFE_HEIGHT"] == 5
    assert settings["STEPSXY_PER_MM"] == 39.37
    assert saved_values == [
        ("TIME_PER_SQMM", 1.0, "USER"),
        ("Z_OFFSET_PER_SEC", 0.2, "USER"),
        ("Z_SAFE_HEIGHT", 5, "USER"),
        ("STEPSXY_PER_MM", 39.37, "USER"),
        ("STEPSZ_PER_MM", 10, "USER"),
        ("PROGRAM_STEP_DELAY_SEC", 0.25, "USER"),
        ("jog_distance_mm", 1.0, "USER"),
    ]
