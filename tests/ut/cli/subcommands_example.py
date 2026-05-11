from argparse import ArgumentParser

from src.cli.subcommand import ISubcommand


class FooSubcommand(ISubcommand):
    CLI_NAME = "foo"
    DESCRIPTION = "Do something when foo subcommand is called"

    @classmethod
    def add_arguments(cls, subparser: ArgumentParser):
        subparser.add_argument(
            choices=["one", "two", "three"], dest="positional_argument"
        )
        subparser.add_argument("-s", "--string-arg", type=str)

    def execute(self):
        print(f"Executing {self.CLI_NAME} with args {self.__dict__}")


class BarSubcommand(ISubcommand):
    CLI_NAME = "bar"
    DESCRIPTION = "bar does something when called"

    @classmethod
    def add_arguments(cls, subparser: ArgumentParser):
        subparser.add_argument("-a", "--a-argument")
        subparser.add_argument("-b", "--b-argument", default="b value")

    def execute(self):
        print(f"Executing {self.CLI_NAME} with args {self.__dict__}")
