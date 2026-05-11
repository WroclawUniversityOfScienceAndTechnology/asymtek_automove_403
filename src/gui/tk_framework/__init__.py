
# pylint: disable=C0114
try:
    import tkinter as tk  # python3
except ImportError:
    import Tkinter as tk  # python2

from src.gui.tk_framework.base_pages import Base
from src.gui.tk_framework.base_elem import *
from src.gui.tk_framework.base_dialogs import *
