from pyternity.python_versions import PYTHON_RELEASE_DATES
import matplotlib.pyplot as plt


def plot_signature(signature, title: str):
    fig, ax = plt.subplots()
    fig.suptitle(title)
    ax.bar(list(PYTHON_RELEASE_DATES), [signature.get(version, 0) for version in PYTHON_RELEASE_DATES])
    plt.tick_params(axis='x', which='major', labelsize=8)

    plt.show()
