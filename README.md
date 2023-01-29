# Pyternity

> Tool to generate modernity signatures for PyPI projects.
> Uses [Vermin](https://github.com/netromdk/vermin) in order to detect features

## Getting started

### Windows (Sandbox):

In PowerShell:

```shell
# MSVC is needed for matplotlib
# Also see: https://github.com/matplotlib/matplotlib/issues/18292
wget https://aka.ms/vs/17/release/vs_BuildTools.exe -OutFile vs_BuildTools.exe
.\vs_BuildTools.exe --passive --add "Microsoft.VisualStudio.Workload.VCTools;includeRecommended;includeOptional"
```

```shell
# Download and install Python 3.11.0
wget https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe -OutFile python-3.11.0-amd64.exe -UseBasicParsing
.\python-3.11.0-amd64.exe /passive InstallAllUsers=1 PrependPath=1
```

```shell
# Clone repo and install requirements
wget https://github.com/cpAdm/Pyternity/archive/refs/heads/master.zip -OutFile pyternity.zip
Expand-Archive pyternity.zip
cd pyternity\Pyternity-master
pip install .
```

### Any other OS:

1. Install Python 3.11.0 (other versions may not work properly)
2. Clone this repository
3. Install dependencies: `pip install .` (or for development: `pip install -e .`)

## Using Pyternity

Note: For security reasons, only use this tool on trusted PyPI projects.

```console
>>> .\pyternity\main.py -h

usage: main.py [-h] (--most-popular-projects MOST_POPULAR_PROJECTS | --biggest-projects BIGGEST_PROJECTS | --projects PROJECTS [PROJECTS ...])
               [--max-release-date MAX_RELEASE_DATE] [--most-popular-projects-hash MOST_POPULAR_PROJECTS_HASH] [--release-type {major,minor}]
               [--re-download-projects] [--re-calculate-features]

Calculate modernity signatures for PyPI projects

options:
  -h, --help            show this help message and exit
  --most-popular-projects MOST_POPULAR_PROJECTS
                        Calculate the signature for the given amount of most popular PyPI projects
  --biggest-projects BIGGEST_PROJECTS
                        Calculate the signature for the given amount of biggest (in size) PyPI projects
  --projects PROJECTS [PROJECTS ...]
                        Calculate signature for specific PyPI projects
  --max-release-date MAX_RELEASE_DATE
                        Maximum date (in ISO 8601 format) any release of any project can have, e.g. 2023-01-31
  --most-popular-projects-hash MOST_POPULAR_PROJECTS_HASH
                        Hash of the top-pypi-packages to use (default: 'main')
  --release-type {major,minor}
                        Calculate the signature for given type of releases of the projects (leave out to calculate for all releases)
  --re-download-projects
                        With this flag, all projects are always re-downloaded
  --re-calculate-features
                        With this flag, ignore the 'results' folder and instead process the PyPI files

```

## Reproduce Research

Re-calculate the signatures:

```shell
.\pyternity\main.py --most-popular-projects 50 --release-type minor --max-release-date 2022-12-31 --most-popular-projects-hash fa998b797a5300a240e2b4c042f9a438ab91c7f5 --re-calculate-features
```

Intermediate results of this can be found in `results` folder. All plots can be found in `plots` folder,
including `All Projects.svg`:

<img src="https://github.com/cpAdm/Pyternity/blob/master/plots/All%20Projects.svg" alt="All project plot">

To validate Vermin run its test, this will also generate `plots/Vermin Validation.svg`:

`python -m unittest tests.vermin_test.TestFeatures.test_from_changelog`

