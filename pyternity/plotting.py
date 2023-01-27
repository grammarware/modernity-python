from itertools import chain

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.axes import Axes
from matplotlib.figure import FigureBase
from mpl_toolkits.mplot3d import Axes3D

from pyternity.pypi_crawler import Release, PyPIProject
from pyternity.utils import *


def plot_3d_graph(X, Y, Z, name: str, show_plot: bool) -> None:
    fig: FigureBase = plt.figure(figsize=(10, 10))

    ax: Axes3D = fig.add_subplot(projection='3d')
    ax.set_xlabel("Python version", fontsize=12, labelpad=10)
    ax.set_ylabel("Release date", fontsize=12)
    ax.set_zlabel("Amount of version-specific features", fontsize=12)
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_box_aspect((8, 4, 3))

    # Matplotlib tries to convert the Python versions to floats, to fix that just use integers and custom labels
    ax.set_xticks(list(range(len(PYTHON_RELEASES))), labels=list(PYTHON_RELEASES))

    ax.plot_trisurf(X, Y, Z, cmap=cm.get_cmap('Blues'))

    years = [datetime(y, 1, 1) for y in range(2008, datetime.now().year + 1, 3)]
    ax.set_yticks(years)

    # Plot line with Python releases with dates (after 2008)
    releases_after_2008 = {
        i: r_date for i, r_date in enumerate(PYTHON_RELEASES.values()) if r_date >= datetime(2008, 1, 1)
    }
    ax.plot(list(releases_after_2008), mdates.date2num(list(releases_after_2008.values())), color='red')

    plt.savefig(PLOTS_DIR / f"{name}.svg", bbox_inches='tight', pad_inches=.3, metadata={'Date': ''})

    if show_plot:
        fig.suptitle(f"Modernity Signature for {name}")
        plt.show()
    plt.close()


def get_x_y_z(signatures: dict[Release, Signature]):
    versions = list(range(len(PYTHON_RELEASES))) * len(signatures)
    dates = list(chain.from_iterable(
        [mdates.date2num(release.upload_date)] * len(PYTHON_RELEASES) for release in signatures
    ))
    data = list(chain.from_iterable(
        [signature.get(version, 0) for version in PYTHON_RELEASES] for signature in signatures.values()
    ))

    return versions, dates, data


def plot_project_signatures(project: PyPIProject, signatures: dict[Release, Signature], show_plot: bool) -> None:
    plot_3d_graph(*get_x_y_z(signatures), project.name, show_plot)


def plot_all_projects_signatures(projects: list[dict[Release, dict]], show_plot: bool) -> None:
    all_versions, all_dates, all_data = [], [], []
    for project in projects:
        versions, dates, data = get_x_y_z(project)
        all_versions += versions
        all_dates += dates
        all_data += data

    plot_3d_graph(all_versions, all_dates, all_data, "All Projects", show_plot)


def plot_vermin_vs_test_features(vermin_features: dict[str, list[str]], test_features: dict[str, set[str]],
                                 failed_per_version: dict[str, int]):
    fig: FigureBase = plt.figure(figsize=(10, 7))
    ax: Axes = fig.add_subplot()
    ax.set_xlabel("Python version", fontsize=14)
    ax.set_ylabel("Amount of version-specific features", fontsize=14)

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

    plt.tick_params(which='major')
    plt.legend(loc='upper right', fontsize=14)

    plt.savefig(PLOTS_DIR / "Vermin Validation.svg", bbox_inches='tight')

    fig.suptitle(f"Detected features by Vermin vs Test")
    plt.show()
