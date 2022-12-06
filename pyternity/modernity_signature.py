import os
from collections import defaultdict
from operator import attrgetter

from pyternity.github_crawler import get_all_tags
from pyternity.plotting import plot_signature
from pyternity.utils import *


def generate_signature(minimum_versions: dict[str, list[tuple[int, int] | None]], weights: dict[str, int]):
    signature: ModernitySignature = defaultdict(float)

    for file, versions in minimum_versions.items():
        for version in versions:
            if version:
                major, minor = version
                for i in range(minor + 1):
                    signature[(major, i)] += weights[file]

    return {v: signature[v] for v in sorted(signature)}


def calculate_signature_project(project_folder: Path):
    logger.debug(f"Calculating signature for project: {project_folder.parent.name} - {project_folder.name}")
    assert project_folder.exists()

    # Get all Python files in this folder
    py_paths = vermin.detect_paths(str(project_folder.absolute()), config=VERMIN_CONFIG)
    # py_paths.sort()
    logger.debug(f"Found {len(py_paths)} python files.")

    minimum_versions_per_file = {}
    weights_per_file = {}

    for path in py_paths:
        res = vermin.process_individual((path, VERMIN_CONFIG))

        if res.text:
            # TODO Handles files with errors
            logger.error(f"ERROR for {res.path}:\n{res.text}")
            continue

        # Don't include files which can be any version
        if res.mins == [(0, 0), (0, 0)]:
            continue

        minimum_versions_per_file[path] = res.mins
        weights_per_file[path] = os.path.getsize(path)

    # [(0, 0), (0, 0)] means it can be any python 2/3 version
    # min_required_version = reduce(lambda a, b: vermin.combine_versions(a, b, config), min_versions, [(0, 0), (0, 0)])
    # print(min_required_version)

    signature = generate_signature(minimum_versions_per_file, weights_per_file)

    logger.debug("\nSignature:")
    for version in signature:
        logger.debug(f"{version}: {signature[version]}")

    return signature


if __name__ == '__main__':
    setup_project()

    projects = [("django", "django")]

    for (owner, repo) in projects:
        tags = get_all_tags(owner, repo)

        for major_tag in filter(attrgetter("is_major_version"), tags):
            path = major_tag.download_tarball("django")
            sign = calculate_signature_project(path)
            plot_signature(sign, f"Modernity Signature for {repo}:{major_tag.name}")
