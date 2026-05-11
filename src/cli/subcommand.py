from abc import ABCMeta, abstractmethod
from argparse import ArgumentParser


class ISubcommand(metaclass=ABCMeta):
    @property
    @classmethod
    @abstractmethod
    def CLI_NAME(cls):
        return NotImplementedError

    @property
    @classmethod
    @abstractmethod
    def DESCRIPTION(cls):
        return NotImplementedError

    @classmethod
    @abstractmethod
    def add_arguments(cls, subparser: ArgumentParser):
        return NotImplementedError

    @abstractmethod
    def execute(self):
        return NotImplementedError
