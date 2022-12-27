import json
import unittest
from collections import defaultdict
from pathlib import Path
from uuid import uuid4

from pyternity import features
from pyternity.utils import TMP_DIR, Features, ROOT_DIR

TEST_CASES_FILE_PY2 = ROOT_DIR / 'tests' / 'generated_test_cases_py2.json'
TEST_CASES_FILE_PY3 = ROOT_DIR / 'tests' / 'generated_test_cases_py3.json'


def msg_features(code: str, actual: Features, expected: Features):
    sorting = lambda d: {k: dict(sorted(v.items())) for k, v in sorted(d.items())}
    return f"\n\n{code=!r}\n --> Actual: {sorting(actual)}\n --> Expect: {sorting(expected)}"


def test_code(test_case: unittest.TestCase, code: str, test_result: Features):
    actual = get_features_from_test_code(code)
    with test_case.subTest(code):
        test_case.assertDictEqual(actual, test_result, msg_features(code, actual, test_result))


def get_features_from_test_code(code: str) -> Features:
    # Note: tempfile library cannot be used here, since Vermin reopens the file
    # Do make the file name random, such that this function can be called concurrently
    tmp_file = TMP_DIR / f"{uuid4()}.py"

    with tmp_file.open('w') as f:
        f.write(code)

    result = features.get_features(tmp_file)
    tmp_file.unlink()
    return result


def save_test_cases(output_file: Path, test_cases: defaultdict[str, Features]) -> None:
    # Save in separate files, such that they can run in parallel
    with output_file.open('w') as f:
        json.dump(test_cases, f, indent=2)


def get_test_cases() -> dict[str, Features]:
    # Combine test cases from python 2 and 3
    with TEST_CASES_FILE_PY2.open() as f2, TEST_CASES_FILE_PY3.open() as f3:
        test_cases = json.load(f2)

        for code, expected in json.load(f3).items():
            test_cases[code] = test_cases.get(code, {}) | expected

        return test_cases


def combine_features(features0: Features, features1: Features) -> Features:
    for version, version_features in features1.items():
        for name in version_features.keys():
            # Don't actually increase the count, since you will count 'double' then
            features0[version][name] = 1

    return features0


def normalize_expected(expected: Features) -> None:
    # Normalize expected first: remove python 1.x.x, and generalize x.y.z to x.y
    for version, expected_per_version in list(expected.items()):
        if version.startswith('1'):
            del expected[version]

        elif version.count('.') == 2:
            new_version = version.rsplit('.', 1)[0]
            expected[new_version] |= expected_per_version
            del expected[version]
