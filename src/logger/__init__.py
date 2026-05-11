#!/usr/bin/env python3

# pylint: disable=C0114

import logging
import sys
from enum import Enum, unique


class SingletonMeta(type):
    """
    The Singleton class can be implemented in different ways in Python. Some
    possible methods include: base class, decorator, metaclass. We will use the
    metaclass because it is best suited for this purpose.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]


@unique
class LogLevel(Enum):
    """
    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0
    """

    LOG_CRITICAL = logging.CRITICAL
    LOG_ERROR = logging.ERROR
    LOG_WARNING = logging.WARNING
    LOG_INFO = logging.INFO
    LOG_DEBUG = logging.DEBUG


class Logger(metaclass=SingletonMeta):
    """
    test loggin methods:
        log("error message", LogLevel.LOG_ERROR)
        log("info message", LogLevel.LOG_INFO)
    """

    LOGGER_NAME = "uiprogram"
    LOGGER_FILE = LOGGER_NAME + ".log"
    LOGGER_FILE_DEF_LEVEL = LogLevel.LOG_ERROR
    LOGGER_CONSOLE_DEF_LEVEL = LogLevel.LOG_DEBUG

    @classmethod
    def log_critical(cls, message):
        """
        Log message on criticla level

        Args:
            message (string): log message
        """
        logger = logging.getLogger(Logger.LOGGER_NAME)
        logger.critical(message)

    @classmethod
    def log_error(cls, message):
        """
        Log message on error level

        Args:
            message (string): log message
        """
        logger = logging.getLogger(Logger.LOGGER_NAME)
        logger.error(message)

    @classmethod
    def log_warning(cls, message):
        """
        Log message on warning level

        Args:
            message (string): log message
        """
        logger = logging.getLogger(Logger.LOGGER_NAME)
        logger.warning(message)

    @classmethod
    def log_info(cls, message):
        """
        Log message on info level

        Args:
            message (string): log message
        """
        logger = logging.getLogger(Logger.LOGGER_NAME)
        logger.info(message)

    @classmethod
    def log_debug(cls, message):
        """
        Log message on debug level

        Args:
            message (string): log message
        """
        logger = logging.getLogger(Logger.LOGGER_NAME)
        logger.debug(message)

    @classmethod
    def logger_init(
        cls,
        log_path=LOGGER_FILE,
        file_log_level=LOGGER_FILE_DEF_LEVEL,
        console_log_level=LOGGER_CONSOLE_DEF_LEVEL,
    ):
        """
        Init logging to console and file sinks with appropraite level
        and format

        Args:
            log_path (string, optional): path to log file. Defaults to LOGGER_FILE.
            file_log_level (string, optional): Defaults to LOGGER_FILE_DEF_LEVEL.
            console_log_level (string, optional): Defaults to LOGGER_CONSOLE_DEF_LEVEL.
        """
        logger = logging.getLogger(Logger.LOGGER_NAME)
        logger.setLevel(logging.DEBUG)
        # create file handler
        file_logger = logging.FileHandler(log_path)
        file_logger.setLevel(int(file_log_level))
        # create console handler with a higher log level
        console_logger = logging.StreamHandler()
        console_logger.setLevel(int(console_log_level))
        # create formatter and add it to the handlers
        formatter = logging.Formatter("%(asctime)s-%(name)s-%(levelname)s-%(message)s")
        file_logger.setFormatter(formatter)
        console_logger.setFormatter(formatter)
        # add the handlers to logger
        logger.addHandler(console_logger)
        logger.addHandler(file_logger)
