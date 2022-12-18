import multiprocessing
from collections import defaultdict
from pyternity.utils import *


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
                # It also dumps the whole AST, skip that
                # But we need print_visits=yes, else it will only output unique missing features
                if line[0] == '|':
                    continue

                try:
                    # Grab the features that were detected which belong to a specific version
                    # Format: file:line:column:py2:py3:feature
                    _, py2, py3, feature = line.rsplit(':', maxsplit=3)

                    if min_v2 := parse_vermin_version(py2):
                        detected_features[min_v2][feature] += 1
                    elif min_v3 := parse_vermin_version(py3):
                        detected_features[min_v3][feature] += 1
                    else:
                        logger.error(f"ERROR for {res.path}:\n{line}")

                except ValueError:
                    # TODO Handle files with errors
                    logger.error(f"ERROR for {res.path}:\n{line}")
                    continue

    return detected_features


def most_popular_per_version(all_features: Features):
    return {version: max(features, key=features.get) for version, features in sorted(all_features.items())}
