# SysML v2 Semantics

A project to experiment with and validate semantics for `KerML` and `SysML v2`.

# Installation


## 1. Clone this repo

```bash
git clone https://github.com/sanbales/sysmlv2-semantics.git
cd sysmlv2-semantics
```

## 2. Get `mamba`

> or stick to `conda` if you like...

If you have anaconda or miniconda, install `mamba` (it's faster and better than conda):

```bash
conda install mamba
```

If you don't have `anaconda` or `miniconda`, just get [Mambaforge](https://github.com/conda-forge/miniforge/releases/tag/4.9.2-5).

## Get `anaconda-project`

If you don't have `anaconda-project`, install [anaconda-project](https://anaconda-project.readthedocs.io):

```bash
mamba install anaconda-project=0.8.4
```

## Configure `mamba` as default

> This will make `anaconda-project` use `mamba` instead of `conda`, making it faster to solve and install the environments.

```bash
CONDA_EXE=mamba        # linux
set CONDA_EXE=mamba    # windows
```

# ... and get going!

You can then get a running instance of JupyterLab by running:

```bash
anaconda-project run lab
```

Copy the URL where JupyterLab is running into your preferred browser, and you should be good to go!
