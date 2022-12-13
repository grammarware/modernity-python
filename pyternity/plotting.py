from pyternity.pypi_crawler import Release
from pyternity.python_versions import PYTHON_RELEASE_DATES, possible_versions
import matplotlib.pyplot as plt

from pyternity.utils import *


def plot_signature(signature: Signature, release: Release):
    # Color Python versions red if they weren't released yet when this Release came out
    # TODO Also color versions red that are above the python_required
    valid_versions = possible_versions(release.upload_date)

    fig, ax = plt.subplots()
    fig.suptitle(
        f"Modernity Signature for {release.project_name} {release.version} "
        f"({release.upload_date.isoformat()}) [{release.requires_python}]"
    )
    ax.set_xlabel("Python version")
    ax.set_ylabel("Amount of version-specific features")
    bar_colors = ['tab:blue' if version in valid_versions else 'tab:red' for version in PYTHON_RELEASE_DATES]
    ax.bar(
        list(PYTHON_RELEASE_DATES), [signature.get(version, 0) for version in PYTHON_RELEASE_DATES],
        color=bar_colors
    )

    plt.tick_params(axis='x', which='major', labelsize=8)

    plt.show()
