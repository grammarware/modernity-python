# Pyternity

## Setup

1. Make sure to use Python 3.11.0 (other version may not work properly)
2. Clone repository
3. Install dependencies: `pip install .` (or for development: `pip install -e .`)

## Using Pyternity

Note: For security reasons, only use this tool on trusted PyPI projects.

```console
>>> .\pyternity\main.py -h 

options:
  -h, --help            show this help message and exit
  --max-release-date MAX_RELEASE_DATE
                        Maximum date (in ISO 8601 format) any release of any project can have, e.g. 2023-01-31
  --most-popular-projects MOST_POPULAR_PROJECTS
                        Calculate the signature for the given amount of most popular PyPI projects
  --biggest-projects BIGGEST_PROJECTS
                        Calculate the signature for the given amount of biggest (in size) PyPI projects
  --projects PROJECTS [PROJECTS ...]
                        Calculate signature for specific PyPI projects
  --most-popular-projects-hash MOST_POPULAR_PROJECTS_HASH
                        Hash of the top-pypi-packages to use (default: 'main')
  --release-type {major,minor}
                        Calculate the signature for given type of releases of the projects (leave out to calculate for all releases)
  --show-plots          Whether to show the plots (will pause program until closed; plots are always saved to file regardless)
```

## Replicate Research

Calculate the signatures:

```console
.\pyternity\main.py --most-popular-projects 50 --release-type minor --max-release-date 2022-12-31 --most-popular-projects-hash fa998b797a5300a240e2b4c042f9a438ab91c7f5
```

Intermediate results of this can be found in `results` folder. All plots can be found in `plots` folder,
including `All Projects.svg`:

<img src="https://github.com/cpAdm/Pyternity/blob/master/plots/All%20Projects.svg" alt="All project plot">

To validate Vermin run its test, this will also generate `plots/Vermin Validation.svg`:

`python -m unittest tests.vermin_test.TestFeatures.test_from_changelog`

