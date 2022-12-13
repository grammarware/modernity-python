from operator import attrgetter

from pyternity.features import most_popular_per_version
from pyternity.plotting import plot_signature
from pyternity.pypi_crawler import PyPIProject
from pyternity.utils import *


@measure_time
def main():
    setup_project()

    projects = ("django",)

    for project_name in projects:
        project = PyPIProject(project_name)

        for release in filter(attrgetter("is_major"), project.releases):
            features = release.get_features()
            print(most_popular_per_version(features))

            signature = {version: sum(features.values()) for version, features in features.items()}
            plot_signature(signature, release)


if __name__ == '__main__':
    main()
