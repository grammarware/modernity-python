import json
import unittest
from pathlib import Path

from pyternity import features
from pyternity.utils import TMP_DIR, Features, ROOT_DIR

TEST_CASES_FILE = ROOT_DIR / 'tests' / 'generated_test_cases.json'


def msg_features(code: str, actual: Features, expected: Features):
    sorting = lambda d: {k: dict(sorted(v.items())) for k, v in sorted(d.items())}
    return f"\n\n{code=!r}\n --> Actual: {sorting(actual)}\n --> Expect: {sorting(expected)}"


def test_code(test_case: unittest.TestCase, code: str, test_result: Features):
    print(f"TEST: {code=}")
    actual = get_features_from_test_code(code)
    with test_case.subTest(code):
        test_case.assertDictEqual(actual, test_result, msg_features(code, actual, test_result))


def get_features_from_test_code(code: str) -> Features:
    # Note: tempfile library cannot be used here, since Vermin reopens the file
    tmp_file = TMP_DIR / "test_file.py"

    with tmp_file.open('w') as f:
        f.write(code)

    return features.get_features(tmp_file)


def save_test_case(code: str, expected: Features):
    print(repr(code), expected)

    test_cases = get_test_cases()
    test_cases[code] = expected

    with TEST_CASES_FILE.open('w+') as f:
        json.dump(test_cases, f)


def get_test_cases():
    try:
        with TEST_CASES_FILE.open() as f:
            return json.load(f)
    except FileNotFoundError:
        return {}



def save_doc_tree(out_dir: str, tree_name: str, doc_tree: str):
    doc_trees_dir = Path(out_dir) / 'doctrees'
    doc_trees_dir.mkdir(exist_ok=True)

    with (doc_trees_dir / (tree_name + '.xml')).open('w', encoding='utf-8') as f:
        f.write(doc_tree)
