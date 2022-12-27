import subprocess
import sys
import unittest

from pyternity.utils import setup_project
from tests.test_utils import test_code, get_test_cases, TEST_CASES_FILE_PY2, TEST_CASES_FILE_PY3, \
    download_latest_python_source, PYTHON_2_VERSION, PYTHON_3_VERSION

# Idea; read all doc files, and look for  .. versionchanged / .. versionadded
# https://github.com/python/cpython/tree/main/Doc/library
# Changelogs itself don't always include all changes from the whole documentation, as it turns out


# https://docs.python.org/3/whatsnew/3.9.html
PYTHON_3_9 = {
    # PEP 0584
    "{} | {'spam': 1, 'eggs': 2, 'cheese': 3}":
        {'3.9': {'dict union (dict | dict)': 1}},
    "e |= {'cheese': 'cheddar', 'aardvark': 'Ethel'}":
        {'3.9': {'dict union merge (dict var |= dict)': 1}},

    # PEP 0585 is not recognized by the tool

    # PEP 0614
    "@buttons[0].clicked.connect\ndef spam(): pass":
        {'2.4': {'function decorators': 1}, '3.9': {'relaxed decorators': 1}},

    # PEP 0616 is not recognized by the tool
    "''.removeprefix('.')\n''.removesuffix('.')":
        {'3.9': {"'str.removeprefix' member": 1, "'str.removesuffix' member": 1}},

    # PEP 0593
    "from typing import Annotated\nVec = Annotated[list[int], MaxLen(10)]":
        {'3.5': {"'typing' module": 1}, '3.9': {"'typing.Annotated' member": 1}},

    "import os\nos.pidfd_open(1)":
        {'3.9': {"'os.pidfd_open' member": 1}},

    # PEP 0615
    "import zoneinfo":
        {'3.9': {"'zoneinfo' module": 1}},

    "import graphlib":
        {'3.9': {"'graphlib' module": 1}},
    "import ast\nast.dump(None, indent=12)":
        {'2.6': {"'ast' module": 1}, '3.9': {"'ast.dump(indent)'": 1}},
    "import ast\nast.unparse(None)":
        {'2.6': {"'ast' module": 1}, '3.9': {"'ast.unparse' member": 1}},

    # "from asyncio import get_event_loop\nAbstractEventLoop().shutdown_default_executor()":
    #     {'3.4': {"'asyncio' module": 1}, '3.9': {"'AbstractEventLoop.shutdown_default_executor' member": 1}},

    "from asyncio import PidfdChildWatcher":
        {'3.4': {"'asyncio' module": 1}, '3.9': {"'asyncio.PidfdChildWatcher' member": 1}},

    "from concurrent import futures\nfutures.Executor().shutdown(cancel_futures=True)":
        {'3.2': {"'concurrent.futures' module": 1},
         '3.9': {"'concurrent.futures.Executor.shutdown(cancel_futures)'": 1}}

}


class TestFeatures(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        setup_project(1)
        download_latest_python_source(PYTHON_2_VERSION)
        download_latest_python_source(PYTHON_3_VERSION)

    def test_version_3_9(self):
        for code, test_result in PYTHON_3_9.items():
            test_code(self, code, test_result)

    def test_from_changelog(self):
        # Clear previous run
        TEST_CASES_FILE_PY2.unlink(missing_ok=True)
        TEST_CASES_FILE_PY3.unlink(missing_ok=True)

        # We combine the results, since some features are both belonging to python 2.x and python 3.x
        # We need the whole Python source, since a sphinx-extension uses relative importing

        # Using Sphinx app twice in same Python process does cause some errors, so run them in a subprocess (parallel)
        sub2 = subprocess.Popen([
            sys.executable, "generate_test_cases.py", PYTHON_2_VERSION, TEST_CASES_FILE_PY2.absolute()
        ])
        sub3 = subprocess.Popen([
            sys.executable, "generate_test_cases.py", PYTHON_3_VERSION, TEST_CASES_FILE_PY3.absolute()
        ])
        self.assertEqual(sub2.wait(), 0)
        self.assertEqual(sub3.wait(), 0)

        # Now test the test-cases, in alphabetic order
        # TODO Run subTest for each module
        for code, expected in sorted(get_test_cases().items()):
            # TODO Normalize expected first: remove python 1.x.x and 2.0, and generalize x.y.z to x.y
            test_code(self, code, expected)

        # TODO Make test to ensure all modules are covered (all non-submodules: sys.stdlib_module_names)


if __name__ == '__main__':
    unittest.main()
