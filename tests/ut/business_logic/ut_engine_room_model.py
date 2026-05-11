from src.business_logic.models.engine_room_model import EngineRoomModel


def test_engine_room_model_reads_serial_settings_from_config(monkeypatch):
    config_values = {
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
    assert data["machine_settings"]["PROGRAM_STEP_DELAY_SEC"] == 0.25
