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

Dispense timing uses pad area in **mm²**. `TIME_PER_SQMM` remains the base rate in seconds per mm².
**Large pad boost** defaults to `3.0`: small pads retain their original timing, intermediate pad areas
receive a progressively increasing multiplier, and the 0805 reference area receives three times its
previous duration. Larger areas keep the configured multiplier instead of extrapolating the boost indefinitely.
Set **Large pad boost** to `1.0` to restore linear timing. The setting is saved locally; reload the Gerber
after changing it to regenerate the dispensing commands. This correction changes valve-open time only;
XY positioning and the original Z-height calculation are preserved.

The reference areas are editable constants near the top of `src/backend/machine_management.py`:
`DISPENSE_SMALL_PAD_AREA_MM2 = 0.18 * 0.35` uses the nominal terminal dimensions of the ESP32 QFN48
5×5 mm package from [Espressif's datasheet, Figure 6-2](https://www.espressif.com/sites/default/files/documentation/esp32_datasheet_en.pdf).
This is a package-terminal size reference, not a claim about the PCB's actual paste aperture.
`DISPENSE_LARGE_PAD_AREA_MM2 = 0.90 * 1.45` uses the IPC-7351 reflow pad dimensions for an 0805 resistor in
[Vishay document 28950](https://www.vishay.com/doc/?28950=). These provide starting anchors for the requested
1×/3× timing calibration; the actual dispense-site area still comes from the loaded Gerber.

For area `A`, small reference `S`, large reference `L`, and configured boost `M`, the multiplier is
`1 + (M - 1) * clamp((A - S) / (L - S), 0, 1)` and the duration is `TIME_PER_SQMM * A * multiplier`.
For example, with a base rate of `1.0`, the 0.063 mm² reference remains at 0.063 s and the 1.305 mm²
reference changes from 1.305 s to 3.915 s. The manufacturers supply dimensions; the 3× timing target comes
from the operator's observation and still needs a physical dispensing check.

`SET ORIGIN` captures the current absolute machine X/Y position, sets the programmable origin,
and saves both coordinates in mm as `MACHINE_ORIGIN` in the local configuration after the machine responds.
Use `Machine > Program origin` to edit those saved coordinates and choose **Save and send to machine**.
`GO ORIGIN` restores the saved origin, raises Z by the configured safe height, and moves to program X/Y zero.
Press `INIT` after connecting the machine. The app waits for a successful initialization response
before sending the saved origin, then waits for the origin command to complete before showing `Initialized`.
Opening a communication connection or pressing `HOME` does not send the origin. Origin controls require machine mode.

For the bottom layer, enable **Mirror Gerber** and open **Machine > XY fiducial calibration**.
The program waits for matching fiducial measurements instead of showing a guessed reflected toolpath.
The saved holder origin stays unchanged; no board width or length is required.
Enter the original Gerber X/Y coordinates of each known fiducial, manually center the head over
its physical position on the flipped board, and choose **Save fiducial**. Two points determine
the reflection's placement and rotation relative to the holder. After both are recorded, the complete
mirrored program is regenerated and becomes available for preview, simulation, export, and machine execution.
Changing the mirror option clears the previous alignment so top-side measurements cannot be applied
to the bottom side. The holder's zero is never recalculated from the board's corners or pad boundaries.

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
