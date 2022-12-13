import multiprocessing
import re
from collections import defaultdict
from pyternity.utils import *

VERMIN_REQUIRE_LOG = re.compile(r"(.+) requires? (.+)")


# TODO Check we if we need Backports, see --help
@measure_time
def get_features(project_folder: Path) -> Features:
    logger.debug(f"Calculating signature for project: {project_folder.parent.name} {project_folder.name}")
    assert project_folder.exists()

    # Get all Python files in this folder
    py_paths = vermin.detect_paths(str(project_folder.absolute()), config=Config.vermin)
    logger.debug(f"Found {len(py_paths)} python files.")

    # Per version, per feature
    detected_features = defaultdict(lambda: defaultdict(int))

    with multiprocessing.Pool(processes=Config.vermin.processes()) as pool:
        results = pool.imap_unordered(vermin.process_individual, ((path, Config.vermin) for path in py_paths))

        for res in results:
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

    return detected_features


def most_popular_per_version(all_features: Features):
    return {version: max(features, key=features.get) for version, features in sorted(all_features.items())}
