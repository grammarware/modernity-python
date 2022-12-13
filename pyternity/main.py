from operator import attrgetter
from pprint import pprint

from pyternity.features import get_features
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
            path = release.download_files(project.name)
            features_per_version = get_features(path)

            signature = {version: sum(features.values()) for version, features in features_per_version.items()}
            pprint(signature)
            plot_signature(
                signature,
                f"Modernity Signature for {project.name} {release.version} ({release.upload_time.date().isoformat()}) [{release.requires_python}]"
            )


if __name__ == '__main__':
    main()
