from itertools import chain

import matplotlib
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.axes import Axes
from matplotlib.figure import FigureBase
from matplotlib.transforms import Bbox
from mpl_toolkits.mplot3d import Axes3D

from pyternity.pypi_crawler import Release, PyPIProject
from pyternity.utils import *

matplotlib.use('Agg')


def plot_3d_graph(X, Y, Z, name: str, z_axis_color: str = '') -> None:
    fig: FigureBase = plt.figure(figsize=(10, 10))

    ax: Axes3D = fig.add_subplot(projection='3d')
    ax.set_xlabel("Python version", fontsize=12, labelpad=10)
    ax.set_ylabel("Release date", fontsize=12)
    ax.set_zlabel("Amount of version-specific features", fontsize=12)
    ax.yaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_box_aspect((8, 4, 3))

    if z_axis_color:
        ax.zaxis.set_pane_color(z_axis_color)

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

    
    # plt.savefig(PLOTS_DIR / f"{name}.svg", bbox_inches=Bbox.from_extents(1.3, 2, 9.9, 7.7), metadata={'Date': ''})
    plt.savefig(PLOTS_DIR / f"{name}_max.svg", bbox_inches=Bbox.from_extents(1.3, 2, 9.9, 7.7), metadata={'Date': ''})

    # plt.savefig(PLOTS_DIR / f"{name}_robust.svg", bbox_inches=Bbox.from_extents(1.3, 2, 9.9, 7.7), metadata={'Date': ''})

    fig.clear()
    plt.close(fig)

def plot_3d_graph_b(X, Y, Z, name: str, z_axis_color: str = '') -> None:
    fig: FigureBase = plt.figure(figsize=(10, 10))

    ax: Axes3D = fig.add_subplot(projection='3d')
    ax.set_ylabel("Python version", fontsize=12, labelpad=10)  
    ax.set_xlabel("Release date", fontsize=12)  
    ax.set_zlabel("Amount of version-specific features", fontsize=12)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))  
    ax.set_box_aspect((4, 8, 3))
    ax.set_title("something")
    if z_axis_color:
        ax.zaxis.set_pane_color(z_axis_color)

    # Reversed the order of Python versions
    ax.set_yticks(list(range(len(PYTHON_RELEASES))), labels=list(PYTHON_RELEASES))

    ax.plot_trisurf(Y, X, Z, cmap=cm.get_cmap('Blues')) 

    years = [datetime(y, 1, 1) for y in range(2008, datetime.now().year + 1, 3)]
    ax.set_xticks(years)

    # Now just simply enumerating the releases after 2008, not reversing
    releases_after_2008 = {
        i: r_date for i, r_date in enumerate(PYTHON_RELEASES.values()) if r_date >= datetime(2008, 1, 1)
    }
    ax.plot(mdates.date2num(list(releases_after_2008.values())), list(releases_after_2008), color='red')
   
    plt.savefig(PLOTS_DIR / f"{name}_max_backwards.svg", bbox_inches=Bbox.from_extents(1.3, 2, 9.9, 7.7), metadata={'Date': ''})
    #plt.savefig(PLOTS_DIR / f"{name}_default_max_backwards.svg", bbox_inches='tight', metadata={'Date': ''})
 
    fig.clear()
    plt.close(fig)



def get_x_y_z(signatures: dict[Release, Signature]):
    versions = list(range(len(PYTHON_RELEASES))) * len(signatures)
    dates = list(chain.from_iterable(
        [mdates.date2num(release.upload_date)] * len(PYTHON_RELEASES) for release in signatures
    ))
    data = list(chain.from_iterable(
        [signature.get(version, 0) for version in PYTHON_RELEASES] for signature in signatures.values()
    ))

    return versions, dates, data


def plot_project_signatures(project: PyPIProject, signatures: dict[Release, Signature]) -> None:
    X,Y,Z = get_x_y_z(signatures)
    plot_3d_graph(X,Y,Z, project.name)
    plot_3d_graph_b(X,Y,Z, project.name)


def plot_all_projects_signatures(projects: list[dict[Release, dict]]) -> None:
    all_versions, all_dates, all_data = [], [], []
    for project in projects:
        versions, dates, data = get_x_y_z(project)
        all_versions += versions
        all_dates += dates
        all_data += data

    plot_3d_graph(all_versions, all_dates, all_data, "All Projects", 'lightgrey')


def plot_vermin_vs_test_features(vermin_features: dict[str, list[str]], all_test_features: dict[str, set[str]],
                                 failed_per_version: dict[str, int]):
    fig: FigureBase = plt.figure(figsize=(10, 7))
    ax: Axes = fig.add_subplot()
    ax.set_xlabel("Python version", fontsize=14)
    ax.set_ylabel("Amount of version-specific features", fontsize=14)

    failed_features = [failed_per_version.get(version, 0) for version in PYTHON_RELEASES]
    test_features = [len(all_test_features.get(version, [])) for version in PYTHON_RELEASES]
    vermin_features = [len(vermin_features.get(version, [])) for version in PYTHON_RELEASES]

    logger.debug(f"{failed_features=}\n{test_features=}\n{vermin_features=}\npercentages_failed=" +
                 ', '.join(f"{x / y * 100:.2f}" for x, y in zip(failed_features, test_features)))

    ax.plot(list(PYTHON_RELEASES), vermin_features, label='Vermin')
    ax.plot(list(PYTHON_RELEASES), test_features, label='All tests')
    ax.plot(list(PYTHON_RELEASES), failed_features, label='Failed tests', color='red')

    plt.tick_params(which='major')
    plt.legend(loc='upper right', fontsize=14)

    plt.savefig(PLOTS_DIR / "Vermin Validation.svg", bbox_inches='tight')

    fig.suptitle(f"Detected features by Vermin vs Test")
    plt.show()
