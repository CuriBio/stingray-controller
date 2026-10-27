# Development Setup

This guide walks through setting up a local development environment for the Stingray 96 Controller.

Active development happens on the `beta96` branch. Base new branches and pull requests on it rather than `main`.

## Project layout

| Directory             | What it is                                                                                                   |
| --------------------- | ------------------------------------------------------------------------------------------------------------ |
| `controller/`         | Python backend that talks to the instrument. Managed with Poetry and includes a Cython extension.            |
| `ui/`                 | Vue/Nuxt component library. Built as a package and consumed by Electron as `@curi-bio/ui`.                   |
| `electron/`           | Desktop app shell. In development it launches the controller from source.                                    |
| `virtual-instrument/` | Simulated instrument for running the app without hardware.                                                   |

When the app starts, Electron launches the controller. The controller first looks for a real instrument over serial. If none is found, it connects to the virtual instrument on port `56575`.

## Prerequisites

- **[pyenv](https://github.com/pyenv/pyenv)** with **Python 3.11** (the project requires `~3.11.3`).
- **Poetry 1.4.2** (the version CI uses)
- **[nvm](https://github.com/nvm-sh/nvm)** with **Node.js 16** (`electron/package.json` requires `^16.17.0`; newer versions fail the engine check).
- **A C/C++ compiler** for the Cython extension: Xcode Command Line Tools on macOS, `build-essential` on Linux, or Visual Studio Build Tools on Windows.

## 1. Set up the controller (Python)

Install Python 3.11 with pyenv, select it for this repo, and install Poetry:

```bash
pyenv install 3.11       # installs the latest 3.11.x
pyenv local 3.11         # run from the repo root
pip install poetry==1.4.2
```

Download zlib. It isn't checked into the repo, but the Cython extension compiles against it:

```bash
cd controller/src/controller
curl -LO https://downloads.curibio.com/software/zlib-1.3.zip
unzip zlib-1.3.zip
mv zlib-1.3 zlib
rm -rf zlib-1.3.zip __MACOSX
cd ../..
```

When you're done, `controller/src/controller/zlib/zlib.h` should exist. The `zlib/` folder is git-ignored.

Install the controller and its dependencies. This also builds the Cython extension:

```bash
# from controller/
poetry env use "$(pyenv which python)"
poetry install
```

Poetry creates a virtualenv for the project using the pyenv Python. Activate it whenever you work on the project:

```bash
# from controller/
source "$(poetry env info --path)/bin/activate"
```

Check that everything works:

```bash
poetry run pytest
```

## 2. Build the UI

```bash
nvm use 16
cd ui
npm ci
npm run build
```

This produces `ui/dist/`, which Electron loads through `@curi-bio/ui`.

## 3. Install Electron dependencies

```bash
nvm use 16
cd electron
npm ci
```

> [!IMPORTANT]
> `@curi-bio/ui` is installed as a link to the local `ui/` folder. After changing > anything in `ui/`, rerun `npm run build` there so Electron picks up the changes.

## 4. Run the app

You'll need two terminals, each with the Poetry virtualenv activated (see step 1).

**Terminal 1: virtual instrument.** Skip this if a real instrument is connected.

```bash
cd virtual-instrument/src
PYTHONPATH=.:../../controller/src python entrypoint.py
```

It prints `WAITING` once it is listening.

**Terminal 2: the app**

```bash
cd electron
nvm use 16
npm run dev
```

In development, Electron runs the controller from source with `python3` (`python` on Windows), using whichever interpreter comes first on your `PATH`. That interpreter has to be the Poetry virtualenv. Otherwise the controller fails with errors like `No module named 'stdlib_utils'`. Run `which python3` to check; it should point inside the virtualenv.

### Running the controller on its own

```bash
python controller/src/entrypoint.py --log-level-debug --skip-software-version-verification
```

Other options are `--base-directory`, `--log-directory`, and `--expected-software-version`. They are defined in `_parse_cmd_line_args` in `controller/src/controller/main.py`.

## Tests and linting

```bash
cd controller
poetry run pytest                                # unit tests
poetry run pytest --include-slow-tests           # include slow tests
poetry run pre-commit install                    # install git hooks
poetry run pre-commit run -a                     # run all hooks manually
```

### Testing the UI

You can run tests individually by running jest. For example: 
```bash
npx jest -c jest.config.js tests/unit/store/stimulation.spec.js -t "Duplicate"
```

## Troubleshooting

**`check-engines: command not found`**
You haven't run `npm ci` in `electron/` yet, or you ran it with the wrong Node version.

**`fatal error: '../zlib/zlib.h' file not found` during `poetry install`**
The zlib source is missing. See step 1.

**`can't open file '.../virtualenv/seed/wheels/embed/pip-<version>-py3-none-any.whl/pip'` during `poetry install`**
Poetry 1.4.2 and the installed `virtualenv` disagree about which bundled pip wheel exists. Upgrade virtualenv in the pyenv Python where Poetry is installed with `pip install -U virtualenv`, then run `poetry install` again.

**`No module named 'stdlib_utils'` (or another controller dependency) when the app starts**
Electron launched the controller with a different `python3`, such as the system or Homebrew Python. Activate the Poetry virtualenv in that terminal (step 1) and check `which python3`.

**The controller can't find an instrument**
Make sure the virtual instrument is running and printed `WAITING` before you start the app.
