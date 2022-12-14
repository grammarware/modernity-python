from pyternity.features import most_popular_per_version
from pyternity.plotting import plot_signature
from pyternity.pypi_crawler import PyPIProject, get_most_popular_projects
from pyternity.utils import *


@measure_time
def main():
    setup_project()

    # TODO Add CLI (arguments) support
    projects = get_most_popular_projects()

    for project_name in projects:
        project = PyPIProject(project_name)

        releases = [release for release in project.releases if release.is_major]
        for release in releases:
            try:
                features = release.get_features()
            except RecursionError:
                # Python files of pybullet cause this error; skip it
                logger.warning(f"Maximum recursion depth exceeded for {release.project_name} {release.version}")
                continue

            signature = {version: sum(features.values()) for version, features in features.items()}
            plot_signature(signature, release)

        if not releases:
            logger.warning(f"No major versions found for {project.name:30}: "
                           f"{[release.version for release in project.releases]}")


if __name__ == '__main__':
    main()
