import unittest

from pyternity import features
from pyternity.utils import TMP_DIR, Features


def msg_features(code: str, actual: Features, expected: Features):
    sorting = lambda d: {k: dict(sorted(v.items())) for k, v in sorted(d.items())}
    return f"\n\n{code=!r}\n --> Actual: {sorting(actual)}\n --> Expect: {sorting(expected)}"


def test_code(test_case: unittest.TestCase, code: str, test_result: Features):
    print(f"TEST: {code=}")
    actual = get_features_from_test_code(code)
    with test_case.subTest(code):
        try:
            test_case.assertDictEqual(actual, test_result, msg_features(code, actual, test_result))
        except AssertionError as e:
            print(e)


def get_features_from_test_code(code: str) -> Features:
    # Note: tempfile library cannot be used here, since Vermin reopens the file
    tmp_file = TMP_DIR / "test_file.py"

    with tmp_file.open('w') as f:
        f.write(code)

    return features.get_features(tmp_file)


def get_import_feature(module: str):
    pass
