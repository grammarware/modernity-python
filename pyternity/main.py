from pyternity.plotting import plot_signatures
from pyternity.pypi_crawler import PyPIProject, get_most_popular_projects
from pyternity.utils import *


@measure_time
def main():
    setup_project()

    # TODO Add CLI (arguments) support
    projects = get_most_popular_projects(50)

    for project_name in projects:
        logger.info(f"Calculating signature for {project_name}...")
        project = PyPIProject(project_name)

        signatures = {}

        releases = [release for release in project.releases if release.is_minor]
        for release in releases:
            logger.info(f"Getting features from {release.project_name} {release.version} ...")

            try:
                features = release.get_features()
            except RecursionError:
                # Python files of pybullet cause this error; skip it
                logger.warning(f"Maximum recursion depth exceeded for {release.project_name} {release.version}")
                continue

            features_per_version = {version: sum(features.values()) for version, features in features.items()}
            total_features = sum(features_per_version.values())
            signature = {version: features_per_version[version] / total_features for version, features in features.items()}

            # plot_signature(signature, release)
            signatures[release] = signature

        if releases:
            plot_signatures(project, signatures)
        else:
            logger.warning(f"No major versions found for {project.name:30}: "
                           f"{[release.version for release in project.releases]}")


if __name__ == '__main__':
    main()
