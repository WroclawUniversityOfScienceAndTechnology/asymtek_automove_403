#!/usr/bin/env python3

# pylint: disable=C0114

BASE_SCREEN_WIDTH = 1920
BASE_SCREEN_HEIGHT = 1080

DEFAULT_SCREEN_WIDTH = 1280
DEFAULT_SCREEN_HEIGHT = 720

SUPPORTED_RESOLUTIONS = (
    (640, 480),
    (800, 600),
    (1024, 768),
    (1280, 720),
    (1366, 768),
    (1600, 900),
    (1920, 1080),
)


def get_resolution_scale(width, height):
    """
    Return the scale needed to fit the base UI into a selected resolution.
    """
    return min(width / BASE_SCREEN_WIDTH, height / BASE_SCREEN_HEIGHT)


def format_resolution(width, height):
    """
    Format a resolution for Tk geometry strings and menu labels.
    """
    return "{}x{}".format(width, height)
