import json
import shutil
import sys
import tarfile
import unittest
from collections import defaultdict
from pathlib import Path
from typing import Mapping
from urllib import request
from uuid import uuid4

from pyternity import features
from pyternity.utils import TMP_DIR, Features, ROOT_DIR, logger

PYTHON_2_VERSION = '2.7.18'
PYTHON_3_VERSION = f"3.{sys.version_info.minor}.{sys.version_info.micro}"

TESTS_DIR = ROOT_DIR / 'tests'
TEST_CASES_FILE_PY2 = TESTS_DIR / 'generated_test_cases_py2.json'
TEST_CASES_FILE_PY3 = TESTS_DIR / 'generated_test_cases_py3.json'
TEST_CASES_FILE_OVERWRITES = TESTS_DIR / 'generated_test_cases_overwrites.json'


def msg_features(code: str, actual: Features, expected: Features):
    sorting = lambda d: {k: dict(sorted(v.items())) for k, v in sorted(d.items())}
    return f"\n\n{code=!r}\n --> Actual: {sorting(actual)}\n --> Expect: {sorting(expected)}"


def test_code(test_case: unittest.TestCase, code: str, test_result: Features):
    actual = get_features_from_test_code(code)
    test_case.assertDictEqual(actual, test_result, msg_features(code, actual, test_result))


def get_features_from_test_code(code: str) -> Features:
    """
    Get all features detected in the given `code`. Can be called concurrently
    :param code: String with the code
    :return: The detected features
    """
    # Note: tempfile.NamedTemporaryFile cannot be used here, since Vermin reopens the file
    # Do make the file name random, such that this function can be called concurrently
    tmp_file = TMP_DIR / f"{uuid4()}.py"

    with tmp_file.open('w') as f:
        f.write(code)

    # Only use 1 process for detecting features, since this function itself is already called in a subprocess
    result = features.get_features(tmp_file, processes=1)
    tmp_file.unlink()
    return result


def save_test_cases(output_file: Path, test_cases: Mapping[str, Features]) -> None:
    """
    Save the `test_cases` to the `output_file`.
    Save these files separately such that Sphinx can run in parallel.
    :param output_file:
    :param test_cases:
    """
    with output_file.open('w') as f:
        json.dump(test_cases, f, indent=2)


def get_test_cases() -> dict[str, Features]:
    """
    Reads generated test cases from file and combines it with the manual (overwritten) test cases
    :return: Combined test cases from Python 2 and 3 (read from files)
    """
    with (
        TEST_CASES_FILE_PY2.open() as py_2_file,
        TEST_CASES_FILE_PY3.open() as py_3_file,
        TEST_CASES_FILE_OVERWRITES.open() as overwrites_file
    ):
        test_cases = json.load(py_2_file)
        for code, expected in json.load(py_3_file).items():
            test_cases[code] = test_cases.get(code, {}) | expected

        overwrites = json.load(overwrites_file)

        return test_cases | overwrites


def tested_features_per_python_version(test_cases: dict[str, Features]) -> dict[str, set[str]]:
    unique_features = defaultdict(set)
    for code, fts in test_cases.items():
        for version, feature in fts.items():
            unique_features[version].update(feature.keys())

    return unique_features


def combine_features(features0: Features, features1: dict[str, dict[str, int]]) -> Features:
    """
    Note: This function does and should *not* combine in-place
    :param features0:
    :param features1:
    :return: The features combined
    """
    new_features = Features(Features, features0)
    for version, version_features in features1.items():
        for name in version_features.keys():
            # Don't actually increase the count, since you will count 'double' then
            new_features[version][name] = 1

    return new_features


def normalize_expected(expected: Features) -> None:
    """
    Remove Python versions 1.x.x and generalize version x.y.z to x.y
    :param expected: The Features to normalize inplace
    """
    for version, expected_per_version in list(expected.items()):
        if version.startswith('1'):
            del expected[version]

        elif version.count('.') == 2:
            new_version = version.rsplit('.', 1)[0]
            expected[new_version] |= expected_per_version
            del expected[version]


def download_latest_python_source(version: str, overwrite: bool = False) -> None:
    """
    Download the Python source code from the given `version`
    :param version: The Python version, e.g. '2.7.1'
    :param overwrite: If *False*, only download if it is not already downloaded
    :return:
    """
    source_dir = TMP_DIR / f"Python-{version}"
    if source_dir.exists():
        if not overwrite:
            return
        shutil.rmtree(source_dir)

    tgz_url = f"https://www.python.org/ftp/python/{version}/Python-{version}.tgz"
    logger.info(f"Downloading Python source from {tgz_url} ...")
    temp_file, _ = request.urlretrieve(tgz_url)
    logger.info("Extracting Python source ...")
    with tarfile.open(temp_file) as tar:
        tar.extractall(TMP_DIR)
