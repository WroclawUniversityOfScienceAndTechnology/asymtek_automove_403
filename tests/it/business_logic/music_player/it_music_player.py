import pytest
import os

from src.cfg import Configuration
from src.business_logic.music_player import MusicPlayer


def test_play_and_kill():
    MusicPlayer().play()
    assert MusicPlayer().is_playing() == True


def test_play_and_stop():
    MusicPlayer().play()
    assert MusicPlayer().is_playing() == True
    MusicPlayer().stop()
    assert MusicPlayer().is_playing() == False


def test_get_all_audio_files():
    audio_files = MusicPlayer().get_all_audio_files()
    assert len(audio_files) > 0


def test_stop_when_never_played():
    MusicPlayer().stop()
    assert MusicPlayer().is_playing() == False
