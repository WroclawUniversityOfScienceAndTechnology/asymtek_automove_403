#!/usr/bin/env python3


import os
import sys
import re
import fileinput
import datetime

from argparse import ArgumentParser

file_extensions = (".py", ".cpp", ".h", ".c", ".txt", ".sh", "Dockerfile")


def option_parser_init():
    parser = ArgumentParser(
        epilog="The scripts checks if copyright info in files is correct."
    )

    parser.add_argument(
        "-d",
        "--diff",
        action="store_true",
        default=False,
        dest="diff",
        help="check only changed files (git based)",
    )

    parser.add_argument(
        "-f", "--fix", action="store_true", dest="fix", help="Fix copyright info"
    )

    parser.add_argument(
        "-C",
        "--workdir",
        action="append",
        nargs="+",
        dest="workdir",
        required=True,
        help="Root repository directory",
    )

    parser.add_argument(
        "-e",
        "--exclude",
        type=str,
        action="append",
        help="exclude repository directory",
    )

    return parser.parse_known_args()


# copyright doxygen tag
COPYRIGHT_DOXYGEN = "@copyright "
# text before year
COPYRIGHT_BEGIN_STRING = "Copyright (C) "
# text after year
COPYRIGHT_END_STRING = "All rights reserved."
# merged text with current year (default copyright that will be inserted in fix mode)
COPYRIGHT_ADD_STRING = (
    COPYRIGHT_BEGIN_STRING + str(datetime.datetime.now().year) + COPYRIGHT_END_STRING
)
# with doxygen tag
COPYRIGHT_ADD_STRING_DOXYGEN = COPYRIGHT_DOXYGEN + COPYRIGHT_ADD_STRING
# regex that will verify if ours correct copyright is present for all files
COPYRIGHT_CHECK_REGEX = (
    re.escape(COPYRIGHT_BEGIN_STRING) + r"[0-9]{4}" + re.escape(COPYRIGHT_END_STRING)
)
# regex that will verify if ours correct copyright is present for all files
COPYRIGHT_CHECK_WITH_DOXYGEN_REGEX = (
    re.escape(COPYRIGHT_DOXYGEN) + COPYRIGHT_CHECK_REGEX
)
# regex that will verify if ours correct copyright is present for new or changed files
COPYRIGHT_CHECK_REGEX_FOR_DIFF = (
    re.escape(COPYRIGHT_BEGIN_STRING)
    + str(datetime.datetime.now().year)
    + re.escape(COPYRIGHT_END_STRING)
)
# regex that will verify if ours correct copyright is present for new or changed files
COPYRIGHT_CHECK_WITH_DOXYGEN_REGEX_FOR_DIFF = (
    re.escape(COPYRIGHT_DOXYGEN) + COPYRIGHT_CHECK_REGEX_FOR_DIFF
)
# regex that will verify any copyright embedded (to reduce probability of placing ours copyright above other)
COPYRIGHT_ANY_CHECK_REGEX = re.compile("copyright", re.IGNORECASE)
# Lang C /**/-style comment copyright with doxygen tag
COPYRIGHT_HEADER_LANG_C_STRING = (
    "/**\n" + " * " + COPYRIGHT_ADD_STRING_DOXYGEN + "\n" + " */\n\n"
)
# CMAKE #-style comment with doxygen tag
COPYRIGHT_HEADER_LANG_CMAKE_STRING = (
    "# #\n" + "# " + COPYRIGHT_ADD_STRING + "\n" + "# #\n\n"
)
# Python and SH #-style comment with doxygen tag
COPYRIGHT_HEADER_LANG_PYTHON_STRING = (
    "# #\n" + "# " + COPYRIGHT_ADD_STRING_DOXYGEN + "\n" + "# #\n\n"
)
COPYRIGHT_HEADER_LANG_SH_STRING = COPYRIGHT_HEADER_LANG_PYTHON_STRING
# Files with extension "data"
COPYRIGHT_HEADER_LANG_DATA_STRING = "\n//" + COPYRIGHT_ADD_STRING + "\n\n"

PRINT_PREFIX = sys.argv[0] + " :"

SHEBANG_REGEX = r"^#!"


class FilesToCheck:
    lang_c = []
    lang_python = []
    lang_cmake = []
    lang_sh = []
    lang_data = []
    lang_other = []

    def add_file_to_check(self, file, repo_path):
        if os.path.islink(file):
            # ignore symbolic links (they are likely to be found as file again)
            return 0
        if os.path.isfile(file) == False:
            # ignore directories etc
            return 0
        if re.match(r".*/\.", file) != None:
            # ignore hidden dot files/dirs
            return 0
        if re.match(r"^" + repo_path + r"/build", file) != None:
            # ignore build dir
            return 0
        if re.match(r"^" + repo_path + r"/doc", file) != None:
            # ignore doc dir
            return 0
        if file.endswith((".png", ".supp", ".config", ".patch", ".md")):
            # ignore above file extensions
            return 0
        if file.endswith((".data")):
            self.lang_data.append(file)
            return 0
        if file.endswith((".h", ".c", ".cpp")):
            self.lang_c.append(file)
            return 0
        if file.endswith(".py"):
            self.lang_python.append(file)
            return 0
        if file.endswith(".sh"):
            self.lang_sh.append(file)
            return 0
        if re.match(
            r".*CMakeLists.*.txt", file, re.IGNORECASE
        ) != None or file.endswith((".cmake", ".cmake.in")):
            self.lang_cmake.append(file)
            return 0

        # not supported lang, return 1
        self.lang_other.append(file)
        # print(PRINT_PREFIX + "No supported file extension")
        return 1


def get_all_files(repo_path, exclude_dir):
    files_to_check = FilesToCheck()
    files = []
    for root, d_names, f_names in os.walk(repo_path):
        for f in f_names:
            fname = os.path.join(root, f)
            if args.exclude:
                if any(elem in fname for elem in exclude_dir):
                    continue
            files.append(fname)

    for file in files:
        files_to_check.add_file_to_check(file, repo_path)
    return files_to_check


def get_changed_files(repo_path):
    files_to_check = FilesToCheck()
    for file in common_dev.get_changed_files(repo_path):
        files_to_check.add_file_to_check(file, repo_path)
    return files_to_check


def check_correct_copyright_embedded(
    file,
    require_doxygen_tag=False,
    enable_verbose_print=False,
    check_only_diff_files=False,
):
    if file.endswith(file_extensions):
        for line in open(file, "r", encoding="utf-8"):
            if only_diff_files:
                copyright_regex = COPYRIGHT_CHECK_REGEX_FOR_DIFF
                copyright_check_with_doxygen = (
                    COPYRIGHT_CHECK_WITH_DOXYGEN_REGEX_FOR_DIFF
                )
            else:
                copyright_regex = COPYRIGHT_CHECK_REGEX
                copyright_check_with_doxygen = COPYRIGHT_CHECK_WITH_DOXYGEN_REGEX
            if require_doxygen_tag:
                copyright_regex = copyright_check_with_doxygen
            if re.search(copyright_regex, line) != None:
                # matching copyright found
                return 0
        if enable_verbose_print:
            print(PRINT_PREFIX + "No matching copyright found in file: " + file)
        # no matching copyright found
        return 1


def check_copyrights(files_to_check, only_diff_files):
    fail_count = 0
    for file in list(
        files_to_check.lang_c + files_to_check.lang_python + files_to_check.lang_sh
    ):
        if (
            check_correct_copyright_embedded(
                file,
                require_doxygen_tag=True,
                enable_verbose_print=True,
                check_only_diff_files=only_diff_files,
            )
            != 0
        ):
            fail_count += 1
    for file in list(files_to_check.lang_cmake):
        if (
            check_correct_copyright_embedded(
                file,
                require_doxygen_tag=False,
                enable_verbose_print=True,
                check_only_diff_files=only_diff_files,
            )
            != 0
        ):
            fail_count += 1
    for file in list(files_to_check.lang_data):
        if (
            check_correct_copyright_embedded(
                file,
                require_doxygen_tag=False,
                enable_verbose_print=True,
                check_only_diff_files=only_diff_files,
            )
            != 0
        ):
            fail_count += 1

    if fail_count > 0:
        return 1
    else:
        return 0


def is_any_copyright_embedded(file):
    for line in open(file):
        if re.search(COPYRIGHT_ANY_CHECK_REGEX, line) != None:
            # some copyright found
            return True
    # no copyright found
    return False


def is_correct_copyright_with_any_year_embedded(file):
    for line in open(file):
        if re.search(COPYRIGHT_CHECK_REGEX, line) != None:
            # some copyright found
            return True
    # no copyright found
    return False


class FixStats:
    correct_count = 0
    risky_count = 0
    fixed_count = 0
    unsupported_extensions_count = 0


def check_copyright_before_fix(file, fix_stats, require_doxygen_tag=False):
    if is_any_copyright_embedded(file):
        if is_correct_copyright_with_any_year_embedded(file):
            return 3
        # skip and display warning, attempt to fix file with some copyright info already present
        print(
            PRINT_PREFIX
            + "Copyright fix in: "
            + file
            + " skipped. Some copyright info found, please verify and correct it manually if needed."
        )
        # fix is risky, it is likely to add double copyright info
        fix_stats.risky_count += 1
        return 2
    # copyright fix is safe
    return 0


def fix_copyright_common(file, fix_stats, copyright_string, check_shebang=True):
    with fileinput.input(files=(file), inplace=True) as f:
        for line in f:
            if f.isfirstline():
                if (False == check_shebang) or (re.match(SHEBANG_REGEX, line) == None):
                    # start with copyright if no shebang matched
                    print(copyright_string + line, end=""),
                else:
                    # keep shebang first before copyright
                    print(line + copyright_string, end=""),
            else:
                # rewrite file
                print(line, end="")
    fix_stats.fixed_count += 1


def fix_copyright_year(file, fix_stats):
    copyright_fixed = False
    with fileinput.input(files=(file), inplace=True) as f:
        for line in f:
            if copyright_fixed != True:
                [line, modification_count] = re.subn(
                    COPYRIGHT_CHECK_REGEX, COPYRIGHT_ADD_STRING, line
                )
                if modification_count > 0:
                    copyright_fixed = True
            print(line, end="")
    if copyright_fixed:
        fix_stats.fixed_count += 1


def fix_copyright_lang_c(file, fix_stats):
    fix_copyright_common(
        file, fix_stats, COPYRIGHT_HEADER_LANG_C_STRING, check_shebang=True
    )


def fix_copyright_lang_python(file, fix_stats):
    fix_copyright_common(file, fix_stats, COPYRIGHT_HEADER_LANG_PYTHON_STRING)


def fix_copyright_lang_sh(file, fix_stats):
    fix_copyright_common(file, fix_stats, COPYRIGHT_HEADER_LANG_SH_STRING)


def fix_copyright_lang_data(file, fix_stats):
    fix_copyright_common(file, fix_stats, COPYRIGHT_HEADER_LANG_DATA_STRING)


def fix_copyright_lang_cmake(file, fix_stats):
    fix_copyright_common(file, fix_stats, COPYRIGHT_HEADER_LANG_CMAKE_STRING)


def fix_copyright_lang_other(file, fix_stats):
    print(
        PRINT_PREFIX + " fix copyright not supported for this file extension: " + file
    )
    fix_stats.unsupported_extensions_count += 1


def fix_copyright(
    files,
    lang_func,
    fix_stats,
    check_before_fix=True,
    check_doxygen_copyright_tag=False,
):
    copyright_check_status = 0
    update_copyright_year_only = False
    for file in files:
        if (
            check_correct_copyright_embedded(
                file,
                require_doxygen_tag=check_doxygen_copyright_tag,
                enable_verbose_print=False,
                check_only_diff_files=False,
            )
            == 0
        ):
            # fix not needed
            fix_stats.correct_count += 1
            continue

        if check_before_fix:
            # skip risky files or files with correct copyright
            copyright_check_status = check_copyright_before_fix(
                file, fix_stats, require_doxygen_tag=check_doxygen_copyright_tag
            )
            if copyright_check_status == 3:
                update_copyright_year_only = True
            elif copyright_check_status != 0:
                continue
        if update_copyright_year_only:
            fix_copyright_year(file, fix_stats)
        else:
            lang_func(file, fix_stats)


def fix_copyrights(files_to_check):
    fix_stats = FixStats()
    fix_copyright(
        files_to_check.lang_c,
        fix_copyright_lang_c,
        fix_stats,
        check_before_fix=True,
        check_doxygen_copyright_tag=True,
    )
    fix_copyright(
        files_to_check.lang_python,
        fix_copyright_lang_python,
        fix_stats,
        check_before_fix=True,
        check_doxygen_copyright_tag=True,
    )
    fix_copyright(
        files_to_check.lang_cmake,
        fix_copyright_lang_cmake,
        fix_stats,
        check_before_fix=True,
        check_doxygen_copyright_tag=False,
    )
    fix_copyright(
        files_to_check.lang_sh,
        fix_copyright_lang_sh,
        fix_stats,
        check_before_fix=True,
        check_doxygen_copyright_tag=True,
    )
    fix_copyright(
        files_to_check.lang_data,
        fix_copyright_lang_data,
        fix_stats,
        check_before_fix=False,
        check_doxygen_copyright_tag=False,
    )
    fix_copyright(
        files_to_check.lang_other,
        fix_copyright_lang_other,
        fix_stats,
        check_before_fix=False,
    )

    if fix_stats.risky_count > 0 or fix_stats.unsupported_extensions_count > 0:
        print(
            PRINT_PREFIX
            + " Not fixed "
            + str(fix_stats.risky_count + fix_stats.unsupported_extensions_count)
            + " files."
        )
        return 1

    return 0


if __name__ == "__main__":
    (args, unknown_args) = option_parser_init()

    if args.diff:
        files_to_check = get_changed_files(args.workdir)
        only_diff_files = True
    else:
        for workdir in args.workdir:
            files_to_check = get_all_files(workdir[0], args.exclude)
        only_diff_files = False

    if args.fix:
        if fix_copyrights(files_to_check):
            print(
                PRINT_PREFIX
                + " Copyright fix ended with warnings. Not all files were fixed."
            )
        sys.exit(0)

    sys.exit(check_copyrights(files_to_check, only_diff_files))
