from traceback import TracebackException

from pyternity.plotting import plot_signatures_3d
from pyternity.pypi_crawler import PyPIProject, get_most_popular_projects
from pyternity.utils import *


@measure_time
def main():
    setup_project()

    # TODO Add CLI (arguments) support
    projects = get_most_popular_projects(50)

    for project_name in projects:
        logger.info(f"Calculating signatures for {project_name} ...")
        project = PyPIProject(project_name)

        signatures = {}

        releases = [release for release in project.releases if release.is_minor]
        logger.info(f"Found {len(releases)} minor releases: {', '.join(r.version for r in releases)}")
        for release in releases:
            logger.info(f"Getting features from {release.project_name} {release.version} ...")

            features = release.get_features()

            features_per_version = {version: sum(features.values()) for version, features in features.items()}
            total_features = sum(features_per_version.values())
            signature = {version: features_per_version[version] / total_features for version in features}

            # plot_signature(signature, release)
            signatures[release] = signature

        if len(signatures) >= 5:
            plot_signatures_3d(project, signatures)
        else:
            logger.warning(f"Not enough minor versions found for {project.name:30}, all versions are: "
                           f"{[release.version for release in project.releases]}")


if __name__ == '__main__':
    main()
