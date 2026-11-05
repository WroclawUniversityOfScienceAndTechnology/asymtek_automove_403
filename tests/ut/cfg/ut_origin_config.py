from pathlib import Path

import pytest

from src.business_logic.models.engine_room_model import EngineRoomModel
from src.cfg import Configuration
from src.cfg.config_files_helper import ConfigFileHelper
from src.cfg.config_wrapper import ConfigWrapper


@pytest.mark.parametrize("origin_text", ['{"x": 12.5, "y": 30.25}', "{'x': 12.5, 'y': 30.25}"])
def test_startup_accepts_saved_origin_with_either_quote_style(monkeypatch, tmp_path, origin_text):
    settings_path = tmp_path / "conf.ini"
    default_text = Path(ConfigFileHelper.DEFAULT_SETTINGS_PATH).read_text()
    settings_path.write_text(default_text.replace("{'x': 0.0, 'y': 0.0}", origin_text))
    monkeypatch.setattr(ConfigFileHelper, "SETTINGS_PATH", str(settings_path))

    # Reproduce startup without resetting existing saved settings.
    ConfigWrapper.update_settings(str(settings_path), ConfigFileHelper.DEFAULT_SETTINGS_PATH)
    Configuration.check_config()

    assert Configuration.get("MACHINE_ORIGIN") == {"x": 12.5, "y": 30.25}
    assert EngineRoomModel.get_machine_settings()["MACHINE_ORIGIN"] == {"x": 12.5, "y": 30.25}


def test_parsing_quoted_strings_keeps_literal_path_characters():
    assert Configuration._parse_value('"C:\\new\\test"') == "C:\\new\\test"
    assert Configuration._parse_value('"ACL CNC"') == "ACL CNC"
