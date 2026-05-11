#!/usr/bin/env python3

import argparse
import os
import shutil
import pathlib


def init_argparse():
    parser = argparse.ArgumentParser(
        epilog="Remove all generated artifacts and create out dir."
    )
    parser.add_argument(
        "--directory",
        "-d",
        metavar="<directory>",
        help="Set custom directory for cleaning. " "Defalut: out",
        default="out",
    )
    return parser


def main():
    parser = init_argparse()
    args = parser.parse_args()

    directory = os.path.expanduser(args.directory)
    _autosummary = directory + "/../common_dev/doc/source/_autosummary"

    if os.path.isdir(directory):
        shutil.rmtree(directory)
        os.makedirs(directory)
    else:
        os.makedirs(directory)

    if os.path.isdir(_autosummary):
        shutil.rmtree(_autosummary)

    # clean all python outputs
    [p.unlink() for p in pathlib.Path(".").rglob("*.py[co]")]
    [p.rmdir() for p in pathlib.Path(".").rglob("__pycache__")]


if __name__ == "__main__":
    main()
