import re
from collections import defaultdict
from operator import attrgetter
from pprint import pprint

from pyternity.plotting import plot_signature
from pyternity.pypi_crawler import PyPIProject
from pyternity.utils import *

VERMIN_REQUIRE_LOG = re.compile(r"(.+) requires? (.+)")


# TODO Check we if we need Backports, see --help
def get_features(project_folder: Path):
    logger.debug(f"Calculating signature for project: {project_folder.parent.name} {project_folder.name}")
    assert project_folder.exists()

    # Get all Python files in this folder
    py_paths = vermin.detect_paths(str(project_folder.absolute()), config=VERMIN_CONFIG)
    # py_paths.sort()
    logger.debug(f"Found {len(py_paths)} python files.")

    # Per version, per feature
    detected_features = defaultdict(lambda: defaultdict(int))

    for py_path in py_paths:
        res = vermin.process_individual((py_path, VERMIN_CONFIG))

        if not res.text:
            continue

        for line in res.text.splitlines():
            # Grab the features that were detected which belong to a specific version
            require_log = VERMIN_REQUIRE_LOG.fullmatch(line)
            if not require_log:
                # TODO Handles files with errors
                logger.error(f"ERROR for {res.path}:\n{line}")
                continue

            feature, min_versions = require_log.groups()
            min_v2, min_v3 = map(parse_vermin_version, min_versions.split(', '))

            if min_v2:
                detected_features[min_v2][feature] += 1
            elif min_v3:
                detected_features[min_v3][feature] += 1

    for version, features in sorted(detected_features.items()):
        print(version, max(features, key=features.get))

    return detected_features


if __name__ == '__main__':
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
