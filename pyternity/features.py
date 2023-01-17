import contextlib
import multiprocessing

from pyternity.utils import *


# TODO Check we if we need Backports, see --help
@measure_time
def get_features(project_folder: Path, processes: int = Config.vermin.processes()) -> Features:
    logger.debug(f"Calculating signature for project: {project_folder.parent.name} {project_folder.name}")
    assert project_folder.exists()

    # Get all Python files in this folder
    py_paths = vermin.detect_paths(str(project_folder.absolute()), config=Config.vermin, processes=processes)
    logger.debug(f"Found {len(py_paths)} python files.")

    # Per version, per feature
    detected_features = defaultdict(lambda: defaultdict(int))
    with multiprocessing.Pool(processes) if processes != 1 else contextlib.nullcontext() as pool:
        mapping = map if processes == 1 else pool.imap_unordered
        results = mapping(vermin.process_individual, ((path, Config.vermin) for path in py_paths))

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

                    # Some features are both specified in 2.7 and 3.1 (like argparse module)
                    # But don't include general 3.0, if features was already added by a python 2.x version
                    min_v2, min_v3 = parse_vermin_version(py2), parse_vermin_version(py3)

                    if min_v2:
                        detected_features[min_v2][feature] += 1
                    if min_v3 and (not min_v2 or min_v3 != '3.0'):
                        detected_features[min_v3][feature] += 1

                except ValueError:
                    # TODO Handle files with errors
                    logger.error(f"ERROR for {res.path}:\n{line}")
                    continue

    return detected_features


def most_popular_per_version(all_features: Features):
    return {version: max(features, key=features.get) for version, features in sorted(all_features.items())}
