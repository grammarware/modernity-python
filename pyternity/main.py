import argparse
import math
from collections import Counter

from pyternity.plotting import plot_project_signatures, plot_all_projects_signatures
from pyternity.pypi_crawler import PyPIProject, get_most_popular_projects, get_biggest_projects, Release
from pyternity.utils import *


def range_int(minimum: int = -math.inf, maximum: int = math.inf):
    def max_int_check(n: str) -> int:
        n_int = int(n)
        if n_int < minimum:
            raise argparse.ArgumentTypeError(f"Should at least be {minimum}")
        if n_int > maximum:
            raise argparse.ArgumentTypeError(f"Should at most be {maximum}")
        return n_int

    return max_int_check


def parse_arguments():
    parser = argparse.ArgumentParser(description="Calculate modernity signatures for PyPI projects")
    parser.add_argument('--max-release-date', type=datetime.fromisoformat, default=datetime.today(),
                        help="Maximum date (in ISO 8601 format) any release of any project can have, e.g. 2023-01-31")

    type_group = parser.add_mutually_exclusive_group(required=True)
    type_group.add_argument('--most-popular-projects', type=range_int(minimum=1, maximum=5000),
                            help="Calculate the signature for the given amount of most popular PyPI projects")
    type_group.add_argument('--biggest-projects', type=range_int(minimum=1, maximum=100),
                            help="Calculate the signature for the given amount of biggest (in size) PyPI projects")
    type_group.add_argument('--projects', action='extend', nargs='+', type=str,
                            help="Calculate signature for specific PyPI projects")

    parser.add_argument('--most-popular-projects-hash', default='main',
                        help="Hash of the top-pypi-packages to use (default: 'main')")

    parser.add_argument('--release-type', choices=['major', 'minor'], default='',
                        help="Calculate the signature for given type of releases of the projects "
                             "(leave out to calculate for all releases)")

    parser.add_argument('--show-plots', action='store_true', default=False,
                        help="Whether to show the plots (will pause program until closed; "
                             "plots are always saved to file regardless)")

    # TODO add option to set logging level

    return parser.parse_args()


def main():
    args = parse_arguments()
    setup_project()

    # Either get nth biggest or nth most popular projects from PyPI
    if args.most_popular_projects:
        projects = get_most_popular_projects(args.most_popular_projects, args.most_popular_projects_hash)
    elif args.biggest_projects:
        projects = get_biggest_projects(args.biggest_projects)
    else:
        projects = args.projects

    # Determine what versions of the releases the user wants
    match args.release_type:
        case 'minor':
            version_check = Release.is_minor
        case 'major':
            version_check = Release.is_major
        case _:
            version_check = lambda *_: True

    all_signatures_per_project = []
    features_count_per_version = defaultdict(Counter)

    for project_name in projects:
        logger.info(f"Calculating signatures for {project_name} ...")
        project = PyPIProject(project_name)

        signatures = {}

        releases = [r for r in project.releases if version_check(r) and r.upload_date <= args.max_release_date]
        logger.info(f"Found {len(releases)} {args.release_type} releases: {', '.join(r.version for r in releases)}")
        for release in releases:
            logger.info(f"Calculating signature for {release.project_name} {release.version} ...")

            all_features = release.get_features()
            features_per_version = {version: sum(features.values()) for version, features in all_features.items()}
            total_features = sum(features_per_version.values())

            if total_features == 0:
                logger.info(f"Did not found any features for {release.project_name} {release.version}")
                continue

            signature = {version: features_per_version[version] / total_features for version in all_features}
            signatures[release] = signature

            # Log all those features that were detected before its Python version released
            for version, features in all_features.items():
                features_count_per_version[version].update(features)

                if features and version not in possible_versions(release.upload_date):
                    logger.warning(f"Following Python {version} ({PYTHON_RELEASES[version].date()}) features "
                                   f"should not be able to be detected on {release.upload_date.date()}: \n{features}")

        all_signatures_per_project.append(signatures)

        # Don't render the plot if we (statistically) do not have enough
        if len(signatures) >= 5:
            plot_project_signatures(project, signatures, args.show_plots)
        else:
            logger.warning(f"Not enough {args.release_type} releases found for {project.name:30}, all releases are: "
                           f"{[release.version for release in project.releases]}")

    amount_of_features_detected = sum(map(Counter.total, features_count_per_version.values()))
    logger.info(f"In total {amount_of_features_detected} features were detected")

    logger.info("5 most common features detected per Python version:")
    for version, features_count in features_count_per_version.items():
        logger.info(f"Python {version}: {features_count.most_common(5)}")

    logger.info("Plotting 'All Projects' plot ...")
    plot_all_projects_signatures(all_signatures_per_project, args.show_plots)


if __name__ == '__main__':
    main()
