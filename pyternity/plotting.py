from pyternity.utils import *
import matplotlib.pyplot as plt


def plot_signature(signature: ModernitySignature, title: str):
    fig, ax = plt.subplots()
    fig.suptitle(title)
    ax.bar([f"{major}.{minor}" for major, minor in signature], list(signature.values()))

    plt.show()
