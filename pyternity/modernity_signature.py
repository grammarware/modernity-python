import os
from collections import defaultdict
from operator import attrgetter

import vermin

from pyternity.github_crawler import get_all_tags
from pyternity.plotting import plot_signature
from pyternity.utils import *


def generate_signature(minimum_versions: dict[str, list[tuple[int, int] | None]], weights: dict[str, int]):
    signature: ModernitySignature = defaultdict(int)

    for file, versions in minimum_versions.items():
        for version in versions:
            if version:
                major, minor = version
                for i in range(minor + 1):
                    signature[(major, i)] += weights[file]

    return {v: signature[v] for v in sorted(signature)}


def calculate_signature_project(project_folder: Path):
    logger.debug(project_folder.absolute())
    if not project_folder.exists():
        raise ValueError("Path does not exists")

    config = vermin.Config.parse_file(vermin.Config.detect_config_file())
    logger.debug(config)

    # Get all Python files in this folder
    py_paths = vermin.detect_paths(str(project_folder.absolute()), config=config)
    # py_paths.sort()
    logger.debug(f"Found {len(py_paths)} python files.")

    minimum_versions_per_file = {}
    weights_per_file = {}

    for path in py_paths:
        res = vermin.process_individual((path, config))

        if res.text:
            # TODO Handles files with errors
            logger.error(f"ERROR for {res.path}:\n{res.text}")
            continue

        # Don't include files which can be any version
        if res.mins == [(0, 0), (0, 0)]:
            continue

        minimum_versions_per_file[path] = res.mins
        weights_per_file[path] = os.path.getsize(path)

    logger.info("DONE with files")
    logger.debug(minimum_versions_per_file)

    # [(0, 0), (0, 0)] means it can be any python 2/3 version
    # min_required_version = reduce(lambda a, b: vermin.combine_versions(a, b, config), min_versions, [(0, 0), (0, 0)])
    # print(min_required_version)

    signature = generate_signature(minimum_versions_per_file, weights_per_file)

    for version in signature:
        logger.info(f"{version}: {signature[version]}")

    return signature


if __name__ == '__main__':
    tags = get_all_tags("django", "django")
    for major_tag in filter(attrgetter("is_major_version"), tags):
        print(major_tag)
        major_tag.download_tarball("django")

    for project_path in EXAMPLES_DIR.iterdir():
        for version_path in project_path.iterdir():
            sign = calculate_signature_project(version_path)
            plot_signature(sign, f"Modernity Signature for {project_path.name}:{version_path.name}")
