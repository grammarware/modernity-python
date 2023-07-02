import argparse
import math
from collections import Counter
import numpy as np

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

    type_group = parser.add_mutually_exclusive_group(required=True)
    type_group.add_argument('--most-popular-projects', type=range_int(minimum=1, maximum=5000),
                            help="Calculate the signature for the given amount of most popular PyPI projects")
    type_group.add_argument('--biggest-projects', type=range_int(minimum=1, maximum=100),
                            help="Calculate the signature for the given amount of biggest (in size) PyPI projects")
    type_group.add_argument('--projects', action='extend', nargs='+', type=str,
                            help="Calculate signature for specific PyPI projects")

    parser.add_argument('--max-release-date', type=datetime.fromisoformat, default=datetime.today(),
                        help="Maximum date (in ISO 8601 format) any release of any project can have, e.g. 2023-01-31")

    parser.add_argument('--most-popular-projects-hash', default='main',
                        help="Hash of the top-pypi-packages to use (default: 'main')")

    parser.add_argument('--release-type', choices=['major', 'minor'], default='',
                        help="Calculate the signature for given type of releases of the projects "
                             "(leave out to calculate for all releases)")

    parser.add_argument('--re-download-projects', default=False, action='store_true',
                        help="With this flag, all projects are always re-downloaded")

    parser.add_argument('--re-calculate-features', default=False, action='store_true',
                        help="With this flag, ignore the 'results' folder and instead process the PyPI files")

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
        # logger.info(f"Calculating signatures for {project_name} ...")
        project = PyPIProject(project_name, args.re_download_projects, args.re_calculate_features)

        signatures = {}

        releases = [r for r in project.releases if version_check(r) and r.upload_date <= args.max_release_date]
        # logger.info(f"Found {len(releases)} {args.release_type} releases: {', '.join(r.version for r in releases)}")
        for release in releases:
            # logger.info(f"Calculating signature for {release.project_name} {release.version} ...")

            all_features = release.get_features()
            features_per_version = {version: sum(features.values()) for version, features in all_features.items()}
            total_features = sum(features_per_version.values())

            median_features = np.median(list(features_per_version.values()))

            min_features = min(features_per_version.values())
            max_features = max(features_per_version.values())
            mean_features = np.mean(list(features_per_version.values()))
            std_features = np.std(list(features_per_version.values()))
            squared_sum = sum(value**2 for value in features_per_version.values())

            q1_features = np.percentile(list(features_per_version.values()), 25)  # 1st quartile (25th percentile)
            q3_features = np.percentile(list(features_per_version.values()), 75)  # 3rd quartile (75th percentile)
            iqr_features = q3_features - q1_features  # Interquartile Range (IQR)
           

            if total_features == 0:
                logger.info(f"Did not found any features for {release.project_name} {release.version}")
                continue

         
            # Linear: Max
            signature = {version: features_per_version[version] / max_features for version in all_features}

            # Linear: Max-Min
            # signature = {version: (features_per_version[version] - min_features) / (max_features - min_features) 
            # for version in all_features if max_features != min_features}

            # Linear: Sum
            # signature = {version: features_per_version[version] / total_features for version in all_features}
  
            # Semi-Linear: Vector
            # signature = {version: features_per_version[version] / math.sqrt(squared_sum) for version in all_features}

           # Applying z-score normalization to the signatures.
            # if std_features != 0:
            #     signature = {version: (features_per_version[version] - mean_features) / std_features 
            #         for version in all_features}
            # else:
            #     signature = {version: 0 for version in all_features}  # or some other predefined constant
            
            # Semi-Linear: Log
            # signature = {version: math.log1p(features_per_version[version]) / math.log1p(max_features) for version in all_features}

            # Apply Robust Scaling
            # signature = {}
            # for version in all_features:
            #     if iqr_features != 0:
            #         signature[version] = (features_per_version[version] - median_features) / iqr_features
            #     else:
            #         signature[version] = 0  # or some other predefined constant

            # Semi-Linear: Median
            # signature = {version: (features_per_version[version] - median_features) for version in all_features}

           # Applying VSS normalization to the signatures.
            # if std_features != 0:
            #     signature = {version: ((features_per_version[version] - mean_features) / std_features) * (mean_features/std_features) 
            #         for version in all_features}
            # else:
            #     signature = {version: 0 for version in all_features}  # or some other predefined constant


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
            plot_project_signatures(project, signatures)
        else:
            logger.warning(f"Not enough {args.release_type} releases found for {project.name:30}, all releases are: "
                           f"{[release.version for release in project.releases]}")

    amount_of_features_detected = sum(map(Counter.total, features_count_per_version.values()))
    logger.info(f"In total {amount_of_features_detected} features were detected")

    # logger.info("5 most common features detected per Python version:")
    for version, features_count in features_count_per_version.items():
        logger.info(f"Python {version}: {features_count.most_common(5)}")

    # logger.info("Plotting 'All Projects' plot ...")
    plot_all_projects_signatures(all_signatures_per_project)


if __name__ == '__main__':
    main()
