import inspect
import logging
import sys
from argparse import ArgumentParser
from dataclasses import dataclass
from typing import List

from src.cli.subcommand import ISubcommand


def _get_sys_args(start: int, end: int):
    return sys.argv[start:end]


class MainCommand:
    def __init__(self) -> None:
        self._arg_parser = ArgumentParser(description="Main command description")
        self._subparsers = self._arg_parser.add_subparsers(
            description="List of available subcommands"
        )
        self._subcommand_parsers = dict()
        self._subcommands = []
        self._add_main_args()

    def _add_main_args(self) -> None:
        """
        Arguments for main function.
        """
        self._arg_parser.add_argument(
            "-v", "--version", action="version", version="%(prog)s 0.0.1"
        )
        self._arg_parser.add_argument(
            "-l",
            "--loglevel",
            help="logging level, suppress messages of lower severity",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="INFO",
            metavar="SEVERITY",
        )

    def add_subcommand(self, subcommand: ISubcommand) -> None:
        """
        Add subcommand to main command. Creates subparser using Subcommands CLI_NAME
        and DESCRIPTION atributes and ISubcommand add_arguments method.
        """
        if not inspect.isclass(subcommand):
            raise ValueError("subcommand must be class, not an object")
        subparser = self._subparsers.add_parser(
            subcommand.CLI_NAME, help=subcommand.DESCRIPTION
        )
        self._subcommand_parsers[subcommand.CLI_NAME] = (subcommand, subparser)
        subcommand.add_arguments(subparser)

    def add_subcommands(self, subcommands: set) -> None:
        """
        Set of ISubcommand subclasses that shell be added as subcommands.
        """
        for subcommand in subcommands:
            self.add_subcommand(subcommand)

    def parse_args(self) -> None:
        """
        Parse arguments and add members accordingly to the classes.
        Main command arguments will become part of MainCommand object and
        subcommand arguments will become part of each respective subcommand object.
        """
        subcommands_data = self._get_subcommand_data()
        main_end_arg_index = self._get_main_command_end_index(subcommands_data)

        # Parse main command arguments and set up logger
        self._arg_parser.parse_args(_get_sys_args(1, main_end_arg_index), self)

        for subcommand_data in subcommands_data:
            # Create subcommand object and pass it as namespace when parsing args
            subcommand_obj = subcommand_data.command_class()
            subcommand_data.parser.parse_args(
                subcommand_data.get_args(), subcommand_obj
            )
            self._subcommands.append(subcommand_obj)

    def execute(self) -> None:
        """
        Calls execution of main command and all subcommands.
        """
        self.__main_execute()
        for subcommand in self._subcommands:
            subcommand.execute()

    def execute_subcommand(self, subcommand: ISubcommand) -> None:
        """
        Execute all subcommands of passed type subcommand.
        """
        for _subcommand in self._subcommands:
            if _subcommand.__class__ == subcommand:
                subcommand.execute()

    @dataclass
    class __CommandArgsData:
        command_class: ISubcommand
        arg_start_index: int
        arg_end_index: int
        parser: ArgumentParser

        def get_args(self):
            return _get_sys_args(self.arg_start_index, self.arg_end_index)

    def _get_subcommand_data(self) -> List[__CommandArgsData]:
        """
        Finds subcommand arguments and assignes subparser for each command.
        returns List of subcommand data
        """
        total_arg_count = len(sys.argv)
        subcommands_data = []
        last_command_with_args = None
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg in self._subcommand_parsers:
                subcommand_class, subparser = self._subcommand_parsers[arg]
                subcommand_data = MainCommand.__CommandArgsData(
                    subcommand_class, i + 1, total_arg_count, subparser
                )
                subcommands_data.append(subcommand_data)
                if last_command_with_args:
                    last_command_with_args.arg_end_index = i
                last_command_with_args = subcommand_data
        return subcommands_data

    def _get_main_command_end_index(
        self, subcommands_data: List[__CommandArgsData] = None
    ):
        """
        Gets index of main commands last argument.
        """
        if subcommands_data:
            return subcommands_data[0].arg_start_index - 1
        return len(sys.argv)

    def __main_execute(self) -> None:
        # Currently nothing is done
        logging.warning("Executing main command")
        pass
