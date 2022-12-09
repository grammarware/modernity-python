from pyternity.python_versions import PYTHON_RELEASE_DATES
from pyternity.utils import *
import matplotlib.pyplot as plt


def plot_signature(signature: ModernitySignature, title: str):
    fig, ax = plt.subplots()
    fig.suptitle(title)
    ax.bar(
        [f"{major}.{minor}" for major, minor in PYTHON_RELEASE_DATES],
        [signature.get(version, 0.0) for version in PYTHON_RELEASE_DATES]
    )
    plt.tick_params(axis='x', which='major', labelsize=8)

    plt.show()
