<<<<<<< HEAD
#!/usr/bin/env python3

import argparse
import subprocess
import sys
import os
import PyInstaller.__main__

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
OUT = SCRIPT_DIR + "/out"


def get_cmdline_arguments():
    parser = argparse.ArgumentParser(epilog="Script compiles and links source code.")
    parser.add_argument(
        "-a",
        "--build_all",
        action="store_true",
        default=False,
        dest="build_all",
        help="Build all available features",
    )

    return parser.parse_args()


def main():
    args = get_cmdline_arguments()

    if not len(sys.argv) > 1:
        args.build_all = True

    if args.build_all:
        PyInstaller.__main__.run(
            [
                "./src/main.py",
                "--onefile",
                "--distpath",
                "./out",
                "--workpath",
                "./out/build",
                "--specpath",
                "./out",
                "--name",
                "program",
                "--add-data",
                "../src/cfg/AppData/:cfg/AppData/",
                "--add-data",
                "/usr/local/lib/python3.8/dist-packages/PIL/:PIL",
                "--uac-admin",
                "--clean",
                "--exclude-module",
                "qt5",
                "--exclude-module",
                "qt4",
                "--exclude-module",
                "gtk3",
                "--exclude-module",
                "web",
                "--exclude-module",
                "PySide2",
                "--exclude-module",
                "PyQt5",
                "--exclude-module",
                "Qt4Agg",
                "--exclude-module",
                "Qt4Cairo",
                "--exclude-module",
                "WebAgg",
                "--exclude-module",
                "PySide2",
            ]
        )
    return args


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e.returncode}")
        sys.exit(1)
=======
# #!/usr/bin/env python3
#
# import argparse
# import subprocess
# import sys
# import os
# import PyInstaller.__main__
#
# SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
# OUT = SCRIPT_DIR + "/out"
#
#
# def get_cmdline_arguments():
#     parser = argparse.ArgumentParser(epilog="Script compiles and links source code.")
#     parser.add_argument(
#         "-a",
#         "--build_all",
#         action="store_true",
#         default=False,
#         dest="build_all",
#         help="Build all available features",
#     )
#
#     return parser.parse_args()
#
#
# def main():
#     args = get_cmdline_arguments()
#
#     if not len(sys.argv) > 1:
#         args.build_all = True
#
#     if args.build_all:
#         PyInstaller.__main__.run(
#             [
#                 "./src/main.py",
#                 "--onefile",
#                 "--distpath",
#                 "./out",
#                 "--workpath",
#                 "./out/build",
#                 "--specpath",
#                 "./out",
#                 "--name",
#                 "program",
#                 "--add-data",
#                 "../src/cfg/AppData/:cfg/AppData/",
#                 "--add-data",
#                 "/usr/local/lib/python3.8/dist-packages/PIL/:PIL",
#                 "--uac-admin",
#                 "--clean",
#                 "--exclude-module",
#                 "qt5",
#                 "--exclude-module",
#                 "qt4",
#                 "--exclude-module",
#                 "gtk3",
#                 "--exclude-module",
#                 "web",
#                 "--exclude-module",
#                 "PySide2",
#                 "--exclude-module",
#                 "PyQt5",
#                 "--exclude-module",
#                 "Qt4Agg",
#                 "--exclude-module",
#                 "Qt4Cairo",
#                 "--exclude-module",
#                 "WebAgg",
#                 "--exclude-module",
#                 "PySide2",
#             ]
#         )
#     return args
#
#
# if __name__ == "__main__":
#     try:
#         main()
#     except subprocess.CalledProcessError as e:
#         print(f"Build failed: {e.returncode}")
#         sys.exit(1)
>>>>>>> 403da82a9568376a66d360052cddefc2147e8107
