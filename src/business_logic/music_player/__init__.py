#!/usr/bin/env python3

# pylint: disable=C0114
import glob
import simpleaudio as sa

from src.logger import SingletonMeta, Logger
from src.cfg import Configuration


class MusicPlayer(metaclass=SingletonMeta):
    """
    Singleton for music playing
    """

    def __init__(self):
        """
        Constructor
        """
        self.play_obj = None

    def __del__(self):
        """
        Stop all audio
        """
        sa.stop_all()

    def play(self, sound_no=0):
        """
        Play wav of the chosen index

        Args:
            sound_no (int, optional): index. Defaults to 0.
        """
        if self.is_playing():
            Logger().log_info("audio is playing already")
            return

        audio_files = self.get_all_audio_files()
        sound_no = str(sound_no) + ".wav"
        for path in audio_files:
            if sound_no not in path:
                continue
            wave_obj = sa.WaveObject.from_wave_file(path)

            self.play_obj = wave_obj.play()

    def stop(self):
        """
        Stop all audio
        """
        sa.stop_all()
        if self.play_obj is not None:
            self.play_obj.wait_done()

    def is_playing(self):
        """
        Check is audio is playing

        Returns:
            bool: True is audio is playing
        """
        # pylint: disable=R1705
        if self.play_obj is not None:
            return self.play_obj.is_playing()
        else:
            return False

    @classmethod
    def get_all_audio_files(cls):
        """
        Get all audio files path from chosen dir set up in configuration

        Returns:
            list: list of audio files paths
        """
        audio_dir = Configuration.get("audio_dir", section="GENERAL")
        return glob.glob(audio_dir + "/*.wav")
