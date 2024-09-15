This intellectual work is Copyright (C) 2021 Bjorn Cole. It is licensed under GPL v3 with intent to retain strong copyleft properties. Contributions are welcome with the understanding that code contributed directly back to this repository via merges or pull requests will also be understood to have copyright ownership transferred to Bjorn Cole.

Forking the code is welcome, as is creating derivative work for SysML v2 semantic interpretation. In order to contribute to this repository, please contact Bjorn at bjorn.cole@gmail.com.

Pull requests are the preferred method of code modification submission.

# Getting Setup

Before contributing your pull requests, please run:

    pixi run precommit

This commit is basically what is run by the CI pipeline, and your PR will not pass CI until you can pass all checks and tests.

This command will run the automatic code formatter, the notebook cleaner, the code linter, the static type checker, and the unit tests.

These commands can be run in isolation.

| __Task__ | __Description__ | __Re-run Conditions__ |
|---|---|---|
| `build-dist` | Creates a source distribution (`sdist`) of `pymbe` in [`./build/sdist/`](./build/sdist) |
| `build-docs` | Builds the documentation for `pymbe` (Future Work) | All `.py` files in [`./src/`](./src) and [`./docs/`](./docs) and `.md` files in [`./docs/`](./docs) |
| `./build-wheel` | Creates a built python package (i.e., a `wheel`) in [`./build/wheel/`](./build/wheel) | 
| `build` | Packages and Builds the python package (`build-dist`) and the documentation (`build-docs`) |
| `clean-notebooks` | Strips outputs from all Jupyter notebooks in the [`./docs/`](./docs) folder | All `*.ipynb` in [`./docs`](./docs)  folder
| `fmt-docs` | Automatically formats all DOCSTRINGS in `.py` files in the [`./src/`](./src) and [`./tests/`](./tests) folders | All `*.py` in the [`./src/`](./src) and [`./tests/`](./tests) folders
| `fmt-py` | Automatically formats all python code in `.py` files in the [`./src/`](./src) and [`./tests/`](./tests) folders | All `*.py` in the [`./src/`](./src) and [`./tests/`](./tests) folders
| `fmt` | Automatically formats all `.py` files in the [`./src/`](./src) and [`./tests/`](./tests) folders | All `*.py` in the [`./src/`](./src) and [`./tests/`](./tests) folders
| `lint` | Tries to fix linter issues and checks there are no linter errors in [`./src/`](./src) and [`./tests/`](./tests) folders | All `*.py` in the [`./src/`](./src) and [`./tests/`](./tests) folders
| `precommit` | Runs the `fmt`, `lint`, `typing`, `test`, and `clean-notebooks` tasks
| `style` | Runs the `fmt` and `lint` tasks | All `*.py` in the [`./src/`](./src/) and [`./tests/`](./tests/) folders
| `test-nb` | Runs notebooks in [`./docs/`](./docs) folder | All `*.py` in the [`./src/`](./src/) and `*.ipynb` in the [`./docs/`](./docs/) folders
| `test-py` | Runs tests and creates coverage report | All `*.py` in the [`./src/`](./src/) and [`./tests/`](./tests/) folders
| `test` | Runs the python (`test-py`) tests (in the future, this should also run the notebooks `test-nb`) |
| `typing` | Runs `mypy` in the [`./src`](./src/) folder | All `*.py` in the [`./src`](./src/) folder
| `update-submodules` | Updates `git` submodules | [`.git/HEAD`](.git/HEAD)
| `vscode` | Launched Visual Studio Code from the appropriate environment
