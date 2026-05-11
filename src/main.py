#!/usr/bin/env python3

# pylint: disable=C0114

from src.cfg import Configuration
from src.controller import MainController
from src.logger import Logger


def main():
    """
    Configure all crucial components and pass the controller
    """
    Configuration.update_settings()
    Configuration.check_config()
    Configuration.install_language(Configuration.get("language", section="USER"))
    Logger().logger_init(
        log_path=Configuration.get("log_file_path", section="GENERAL"),
        file_log_level=Configuration.get("file_log_level", section="GENERAL"),
        console_log_level=Configuration.get("console_log_level", section="GENERAL"),
    )
    app = MainController()
    app.mainloop()


if __name__ == "__main__":
    main()
