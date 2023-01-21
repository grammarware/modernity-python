import datetime
from itertools import chain

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.axes import Axes
from matplotlib.figure import FigureBase
from mpl_toolkits.mplot3d import Axes3D

from pyternity.pypi_crawler import Release, PyPIProject
from pyternity.python_versions import PYTHON_RELEASES, possible_versions
from pyternity.utils import *


def plot_signature(signature: Signature, release: Release):
    ax: Axes
    fig: FigureBase
    fig, ax = plt.subplots()

    fig.suptitle(
        f"Modernity Signature for {release.project_name} {release.version} "
        f"({release.upload_date.isoformat()}) [{release.requires_python}]"
    )
    ax.set_xlabel("Python version")
    ax.set_ylabel("Amount of version-specific features")

    # Color Python versions red if they weren't released yet when this Release came out
    # TODO Also color versions red that are above the python_required
    valid_versions = possible_versions(release.upload_date)
    bar_colors = ['tab:blue' if version in valid_versions else 'tab:red' for version in PYTHON_RELEASES]
    ax.scatter(
        list(PYTHON_RELEASES), [signature.get(version, 0) for version in PYTHON_RELEASES],
        color=bar_colors
    )

    plt.tick_params(axis='x', which='major', labelsize=8)

    plt.show()


def plot_signatures_3d(project: PyPIProject, release_and_signatures: dict[Release, Signature]):
    fig: FigureBase = plt.figure(figsize=(10, 10))

    ax: Axes3D = fig.add_subplot(projection='3d')
    ax.set_xlabel("Python version")
    ax.set_ylabel("Release date")
    ax.set_zlabel("Amount of version-specific features")
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%Y'))

    # Matplotlib tries to convert the Python versions to floats, to fix that just use integers and custom labels
    ax.xaxis.set_ticks(list(range(len(PYTHON_RELEASES))), labels=list(PYTHON_RELEASES))

    dates = list(chain.from_iterable(
        [mdates.date2num(r.upload_date)] * len(PYTHON_RELEASES) for r in release_and_signatures
    ))
    versions = list(range(len(PYTHON_RELEASES))) * len(release_and_signatures)
    data = list(chain.from_iterable(
        [signature.get(version, 0) for version in PYTHON_RELEASES] for signature in release_and_signatures.values()
    ))
    ax.plot_trisurf(versions, dates, data, cmap=cm.get_cmap('Blues'))

    years = [datetime.datetime(y, 1, 1) for y in range(2008, datetime.datetime.now().year + 1, 3)]
    ax.set_yticks(years)

    # Plot line with Python releases with dates (after 2008)
    releases_after_2008 = {
        i: r_date for i, r_date in enumerate(PYTHON_RELEASES.values()) if r_date >= datetime.datetime(2008, 1, 1)
    }
    ax.plot(list(releases_after_2008), mdates.date2num(list(releases_after_2008.values())), color='red')

    plt.savefig(PLOTS_DIR / f"{project.name}_3d.svg", bbox_inches='tight', pad_inches=.2)

    fig.suptitle(f"Modernity Signature for {project.name}", fontsize=18)
    plt.show()


def plot_signatures(project: PyPIProject, release_and_signatures: dict[Release, Signature]):
    ax: Axes
    fig: FigureBase
    fig, ax = plt.subplots(figsize=(20, 14))

    fig.suptitle(f"Modernity Signature for {project.name}", fontsize=24)
    ax.set_xlabel("Python version", fontsize=18)
    ax.set_ylabel("Amount of version-specific features", fontsize=18)

    for i, (release, signature) in enumerate(release_and_signatures.items()):
        # Color Python versions red if they weren't released yet when this Release came out
        # TODO Also color versions red that are above the python_required
        valid_versions = possible_versions(release.upload_date)
        # bar_colors = ['tab:blue' if version in valid_versions else 'tab:red' for version in PYTHON_RELEASES]

        ax.plot(
            list(PYTHON_RELEASES), [signature.get(version, 0) for version in PYTHON_RELEASES],
            label=f"{release.version: <7} ({release.upload_date.isoformat()}) "
                  f"[{release.requires_python[:8]} "
                  f"{'..' if release.requires_python and len(release.requires_python) >= 8 else ''}]",
            color=plt.cm.hsv(i / len(release_and_signatures)),
        )

    plt.tick_params(which='major', labelsize=18)
    plt.legend(loc='upper right', fontsize=14)

    plt.savefig(PLOTS_DIR / f"{project.name}.svg")
    plt.show()


def plot_vermin_vs_test_features(vermin_features: dict[str, list[str]], test_features: dict[str, set[str]],
                                 failed_per_version: dict[str, int]):
    fig: FigureBase = plt.figure(figsize=(20, 14))
    ax: Axes = fig.add_subplot()
    ax.set_xlabel("Python version", fontsize=18)
    ax.set_ylabel("Amount of version-specific features", fontsize=18)

    ax.plot(
        list(PYTHON_RELEASES), [len(vermin_features.get(version, [])) for version in PYTHON_RELEASES],
        label='Vermin'
    )

    ax.plot(
        list(PYTHON_RELEASES), [len(test_features.get(version, [])) for version in PYTHON_RELEASES],
        label='All tests'
    )

    ax.plot(
        list(PYTHON_RELEASES), [failed_per_version.get(version, 0) for version in PYTHON_RELEASES],
        label='Failed tests', color='red'
    )

    plt.tick_params(which='major', labelsize=18)
    plt.legend(loc='upper right', fontsize=18)

    plt.savefig(PLOTS_DIR / "Vermin VS Test.svg", bbox_inches='tight')

    fig.suptitle(f"Detected features by Vermin vs Test", fontsize=24)
    plt.show()
