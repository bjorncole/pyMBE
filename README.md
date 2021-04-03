# PyMBE

A project to experiment with and validate semantics for `KerML` and `SysML v2`. Running core semantics and interpreting models is a foundational capability for any modeling software.

# Get set up...

## 1. Clone this repo

```bash
git clone https://github.com/bjorncole/pymbe.git
cd pymbe
```

## 2. Get `mamba`

> or stick to `conda` if you like...  just change `mamba` to `conda` in the instructions below.

If you have anaconda or miniconda, install `mamba` (it's faster and better than conda):

```bash
conda install mamba
```

If you don't have `anaconda` or `miniconda`, just get [Mambaforge](https://github.com/conda-forge/miniforge/releases/tag/4.9.2-5).

## 3. Get `anaconda-project`

If you don't have `anaconda-project`, install [anaconda-project](https://anaconda-project.readthedocs.io):

```bash
mamba install anaconda-project=0.8.4
```

## 4. Configure `mamba` as default

> This will make `anaconda-project` use `mamba` instead of `conda`, making it faster to solve and install the environments.

> You will have to do this when you start your shell unless you set these environment variables permanently.

```bash
CONDA_EXE=mamba        # linux
set CONDA_EXE=mamba    # windows
```

## 5. Setup the Development Environment

> This will install the non-packaged dependencies and `pymbe` in editable mode.

```bash
anaconda-project run setup
```

# ... and get going!

You can then get a running instance of JupyterLab by running:

```bash
anaconda-project run lab
```

Copy the URL where JupyterLab is running into your preferred browser, and you should be good to go!

## Widgets

You can compose a widget as illustrated in the Widget Example notebook.
![Simple Example](https://user-images.githubusercontent.com/1438114/113459048-50a7d380-93e2-11eb-912e-5bc327545ea8.gif)
