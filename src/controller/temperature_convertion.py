#!/usr/bin/env python3


"""
Module responsible for temperature convertion
"""


def celc_to_fahrenheit(celsius: float) -> float:
    """
    Convert temperature given in Celcius degrees to Fahrenheit units

    Args:
        celsius : value to be conerted to Fahrenheit degrees (required input to be a float)

    Return:
        value in Fahrenheit degrees (returned type is float)
    """
    return round((celsius * 1.8) + 32, 2)


def fahrenheit_to_celc(fahrenheit: float) -> float:
    """
    Convert temperature given in Fahrenheit degrees to Celcius units

    Args:
        fahrenheit : value to be conerted to Celcius degrees (required input to be a float)

    Return:
        value in Celcius degrees (returned type is float)
    """
    return round((fahrenheit - 32) / 1.8, 2)
