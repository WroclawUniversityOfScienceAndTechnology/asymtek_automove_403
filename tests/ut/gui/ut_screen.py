#!/usr/bin/env python3

# pylint: disable=C0114

from src.gui.screen import format_resolution, get_resolution_scale


def test_format_resolution():
    assert format_resolution(1280, 720) == "1280x720"


def test_get_resolution_scale_for_default_smaller_screen():
    assert get_resolution_scale(1280, 720) == 2 / 3


def test_get_resolution_scale_uses_dimension_that_fits():
    assert get_resolution_scale(800, 600) == 800 / 1920
