import json
import unittest
from collections import defaultdict
from pathlib import Path

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
    tmp_file = TMP_DIR / "test_file.py"

    with tmp_file.open('w') as f:
        f.write(code)

    return features.get_features(tmp_file)


def save_test_cases(output_file: Path, test_cases: defaultdict[str, Features]) -> None:
    # Save in separate files, such that they can run in parallel
    with output_file.open('w') as f:
        json.dump(test_cases, f)


def get_test_cases() -> dict[str, Features]:
    # Combine test cases from python 2 and 3
    with TEST_CASES_FILE_PY2.open() as f2, TEST_CASES_FILE_PY3.open() as f3:
        test_cases = json.load(f2)

        for code, expected in json.load(f3).items():
            test_cases[code] = test_cases.get(code, {}) | expected

        return test_cases


def save_doc_tree(out_dir: str, tree_name: str, doc_tree: str):
    doc_trees_dir = Path(out_dir) / 'doctrees'
    doc_trees_dir.mkdir(exist_ok=True)

    doc_tree_file = doc_trees_dir / (tree_name + '.xml')
    with doc_tree_file.open('w', encoding='utf-8') as f:
        f.write(doc_tree)


def combine_features(features0: Features, features1: Features) -> Features:
    for version, version_features in features1.items():
        for name in version_features.keys():
            # Don't actually increase the count, since you will count 'double' then
            features0[version][name] = 1

    return features0
