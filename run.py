#!/usr/bin/env python3

import argparse
import os
import signal
import subprocess
import sys
import time
import src

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
REPO_DIR = SCRIPT_DIR  # '/repo'

SCRIPTS_DIR = SCRIPT_DIR + "/common_dev/scripts"
SCRIPT_SH = ".sh"
OUT = SCRIPT_DIR + "/out"
UT_DIR = REPO_DIR + "/tests/ut"
IT_DIR = REPO_DIR + "/tests/it"
CELERY_WORKER_COMMAND = [
    "poetry",
    "run",
    "celery",
    "-A",
    "src.backend.celery_app",
    "worker",
    "--loglevel=info",
    "--pool=solo",
]


def get_cmdline_arguments():
    parser = argparse.ArgumentParser(epilog="Run options include tests")

    parser.add_argument(
        "-a",
        "--run_all",
        action="store_true",
        default=False,
        dest="run_all",
        help="Run all available features",
    )

    parser.add_argument(
        "-u",
        "--unit_test",
        action="store_true",
        default=False,
        dest="unit_test",
        help="Run all unit test only",
    )

    parser.add_argument(
        "-t",
        "--tests",
        action="store_true",
        default=False,
        help="Run integration tests only",
    )

    parser.add_argument(
        "-f",
        "--format",
        action="store_true",
        default=False,
        dest="format",
        help="Format with black",
    )

    parser.add_argument("-p", "--program", action="store_true", help="Run program")
    args = parser.parse_args()

    return args


def perform_tests(test_path, test_postfix="ut"):
    out_test_doc_dir = OUT + "/test_doc"
    allure_result = out_test_doc_dir + "/allure_result"
    allure_report = out_test_doc_dir + "/allure_report"

    try:
        subprocess.check_call(
            [
                "pytest",
                test_path,
                "--alluredir=" + allure_result + "_" + test_postfix,
                "--cov-branch",
                "--cov-report",
                "html:" + out_test_doc_dir + "/coverage" + "_" + test_postfix,
                "--cov=src",
                "--gherkin-terminal-reporter",
                "-v",
                test_path,
            ]
        )
    except subprocess.CalledProcessError as e:
        return test_postfix + " tests fail: " + str(e) + "\n"

    subprocess.check_call(
        [
            "allure",
            "generate",
            allure_result + "_" + test_postfix,
            "--clean",
            "-o",
            allure_report + "_" + test_postfix,
        ]
    )
    subprocess.check_call(
        [
            "allure-docx",
            allure_result + "_" + test_postfix,
            allure_report + "_" + test_postfix + "/report.docx",
            "--detail-level=compact",
        ]
    )

    return ""


def run_all_code_checkers(build_dir):
    checker_exception_message = ""

    checker_exception_message += perform_tests(UT_DIR, "ut")
    checker_exception_message += perform_tests(IT_DIR, "it")

    try:
        command = [
            SCRIPT_DIR + "/common_dev/scripts/copyrights.py",
            "-C",
            "src/" "-e",
            "src/cfg/AppData/",
        ]
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        checker_exception_message += (
            "Copyrights check failed run: " + " ".join(command) + "\n"
        )

    try:
        command = ["common_dev/scripts/todo_check.py", "-C", "src", "-C", "tests"]
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        checker_exception_message += (
            "TODO check failed run: " + " ".join(command) + "\n"
        )

    try:
        command = [
            "black",
            "--check",
            "--diff",
            "src",
            "tests",
            "common_dev",
            "run.py",
            "build.py",
            "clean.py",
        ]
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        checker_exception_message += (
            "Format check fail run: " + " ".join(command) + "\n"
        )

    try:
        command = [SCRIPT_DIR + "/common_dev/scripts/cyclomatic.py"]
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        checker_exception_message += (
            "Cyclomatic check fail run: " + " ".join(command) + "\n"
        )

    try:
        command = ["make", "-C./common_dev/doc", "html"]
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        checker_exception_message += (
            "Docu generation fail run: " + " ".join(command) + "\n"
        )

    try:
        # can add "tests",  optionally
        command = [
            "pylint",
            "src/",
            "-r",
            "y",
            "-f",
            "colorized",
            "--ignore-patterns",
            "tests/*.py",
        ]
        subprocess.check_call(command)
    except subprocess.CalledProcessError:
        checker_exception_message += (
            "Pylint check failed run: " + " ".join(command) + "\n"
        )

    if checker_exception_message:
        print("Check exception message:\n" + checker_exception_message)
        return False

    return True


def start_celery_worker():
    worker = subprocess.Popen(CELERY_WORKER_COMMAND, cwd=REPO_DIR)
    time.sleep(1)
    if worker.poll() is not None:
        raise subprocess.CalledProcessError(worker.returncode, CELERY_WORKER_COMMAND)
    return worker


def stop_celery_worker(worker):
    if worker.poll() is not None:
        return

    worker.send_signal(signal.SIGTERM)
    try:
        worker.wait(timeout=10)
    except subprocess.TimeoutExpired:
        worker.kill()
        worker.wait()


def run_program():
    celery_worker = start_celery_worker()
    try:
        src.main()
    finally:
        stop_celery_worker(celery_worker)


def main():
    args = get_cmdline_arguments()

    if not len(sys.argv) > 1:
        args.run_all = True

    if args.run_all:
        run_all_code_checkers(OUT)

    if args.tests:
        perform_tests(IT_DIR, "it")

    if args.unit_test:
        perform_tests(UT_DIR, "ut")

    if args.format:
        subprocess.check_call(
            ["black", "src", "tests", "common_dev", "run.py", "build.py", "clean.py"]
        )

    if args.program:
        run_program()


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as e:
        print(f"Build failed: {e.returncode}")
        sys.exit(1)
