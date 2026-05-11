import sys
from unittest import mock

import pytest
from src.cli.main_command import MainCommand
from tests.ut.cli.subcommands_example import BarSubcommand, FooSubcommand

LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


@pytest.mark.parametrize("loglevel", LOG_LEVELS)
def test_debug_level_set(loglevel):
    with mock.patch.object(sys, "argv", ["main.py", "-l", loglevel]):
        main_command = MainCommand()
        main_command.parse_args()
        assert main_command.loglevel == loglevel


@mock.patch.object(sys, "argv", ["main.py", "-l", "something"])
def test_incorrect_debug_level(capsys):
    main_command = MainCommand()
    with pytest.raises(SystemExit) as sys_exit:
        main_command.parse_args()
    out, err = capsys.readouterr()
    assert "usage: main.py [-h] [-v] [-l SEVERITY] {} ..." in err
    assert "main.py: error: argument -l/--loglevel: invalid choice: 'something'" in err
    for loglevel in LOG_LEVELS:
        assert loglevel in err


@mock.patch.object(
    sys,
    "argv",
    ["main.py", "foo", "one", "-s", "two", "foo", "two", "-s", "three", "bar"],
)
def test_multiple_subcommands(capsys):
    main_command = MainCommand()
    main_command.add_subcommands([BarSubcommand, FooSubcommand])
    main_command.parse_args()
    main_command.execute()

    expected_lines = [
        "Executing foo with args {'positional_argument': 'one', 'string_arg': 'two'}",
        "Executing foo with args {'positional_argument': 'two', 'string_arg': 'three'}",
        "Executing bar with args {'a_argument': None, 'b_argument': 'b value'}",
    ]

    out, err = capsys.readouterr()
    for expected_line in expected_lines:
        assert expected_line in out


@mock.patch.object(sys, "argv", ["main.py", "foo", "--unknown", "212"])
def test_unknown_subcommand_args():
    main_command = MainCommand()
    main_command.add_subcommands([FooSubcommand])
    with pytest.raises(SystemExit) as sys_exit:
        main_command.parse_args()
