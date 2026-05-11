# ACL CNC UI

Tkinter-based Python UI for controlling and previewing ACL CNC workflows.

## Requirements

- Python `>=3.10,<3.13`
- Poetry
- Tk support for your Python installation

Optional tools:

- install allure manually with `brew install allure`, `pip install allure-docx`
- Allure CLI and `allure-docx`, only if you want generated Allure HTML/DOCX reports from `run.py -a`

## Setup

Create virtual env:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
poetry install
```

Activate the virtual environment if you prefer an interactive shell:

```bash
poetry shell
```

## Run The Program

Preferred local command:

```bash
poetry run python -m src.main
```

Alternative through the project runner:

```bash
poetry run python run.py -p
```

The UI stores runtime configuration under `~/AppData/cfg/conf.ini`. Default assets and default settings live in `src/cfg/AppData/`.

## Screen Resolution

The application starts at `1280x720`, which is scaled down by one-third from the original `1920x1080` layout.

Use the top menubar item `Screen resolution` to switch between supported resolutions:

- `640x480`
- `800x600`
- `1024x768`
- `1280x720`
- `1366x768`
- `1600x900`
- `1920x1080`

The selected resolution is saved to the config file and the active screen is redrawn with matching element scale.

## Tests

Run unit tests:

```bash
poetry run pytest tests/ut
```

Run integration tests:

```bash
poetry run pytest tests/it
```

Run one focused test file:

```bash
poetry run pytest tests/ut/gui/ut_screen.py -q
```

Some integration tests create a real Tk window, so they need a desktop/display session.

## Code Checks

Format code:

```bash
poetry run black src tests common_dev run.py build.py clean.py
```

Run pylint:

```bash
poetry run pylint src/ -r y -f colorized --ignore-patterns "tests/*.py"
```

Run the full legacy checker:

```bash
poetry run python run.py -a
```

`run.py -a` runs unit and integration tests with coverage, copyright checks, TODO checks, Black, cyclomatic complexity, documentation generation, and pylint. It expects `common_dev/` to exist and may also require external report tools such as Allure.

## Build

Create a PyInstaller bundle:

```bash
poetry run python build.py -a
```

Build output is written to `out/`.

## Clean

Remove generated output and Python cache files:

```bash
poetry run python clean.py
```

## Repository Cleanup

These folders are optional depending on your workflow:

- `ci/`: Docker and CI helper files. Keep it if you use Docker or GitLab CI.
- `tools/`: legacy bundled VS Code files used by the Docker workflow. It can be removed if you do not run the containerized IDE workflow.
- `common_dev/`: development scripts and Sphinx docs used by `run.py -a`. Keep it unless you also simplify `run.py` and `clean.py`.

For a Poetry-only local workflow, the important folders are usually `src/`, `tests/`, and `src/cfg/AppData/`, plus `pyproject.toml`, `poetry.lock`, `run.py`, `build.py`, and `clean.py`.
