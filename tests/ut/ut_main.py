import importlib


app_main = importlib.import_module("src.main")


def test_main_does_not_reset_persisted_settings(monkeypatch):
    calls = []

    class LoggerSpy:
        def logger_init(self, **kwargs):
            calls.append(("logger_init", kwargs))

    class ControllerSpy:
        def mainloop(self):
            calls.append("mainloop")

    config_values = {
        "language": "en",
        "log_file_path": "program.log",
        "file_log_level": 40,
        "console_log_level": 10,
    }

    monkeypatch.setattr(app_main.Configuration, "reset_settings", staticmethod(lambda: calls.append("reset")))
    monkeypatch.setattr(app_main.Configuration, "update_settings", staticmethod(lambda: calls.append("update")))
    monkeypatch.setattr(app_main.Configuration, "check_config", staticmethod(lambda: calls.append("check")))
    monkeypatch.setattr(
        app_main.Configuration,
        "install_language",
        staticmethod(lambda language: calls.append(("install_language", language))),
    )
    monkeypatch.setattr(
        app_main.Configuration,
        "get",
        staticmethod(lambda key, section="USER": config_values[key]),
    )
    monkeypatch.setattr(app_main, "Logger", LoggerSpy)
    monkeypatch.setattr(app_main, "MainController", ControllerSpy)

    app_main.main()

    assert "reset" not in calls
    assert calls[0:2] == ["update", "check"]
    assert "mainloop" in calls
