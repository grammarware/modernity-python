import subprocess
import unittest

from pyternity.plotting import plot_vermin_vs_test_features
from pyternity.utils import *
from tests.test_utils import test_code, get_test_cases, TEST_CASES_FILE_PY2, TEST_CASES_FILE_PY3, \
    download_latest_python_source, PYTHON_2_VERSION, PYTHON_3_VERSION, tested_features_per_python_version, TESTS_DIR

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
        setup_project()
        download_latest_python_source(PYTHON_2_VERSION)
        download_latest_python_source(PYTHON_3_VERSION)

    def test_version_3_9(self):
        for code, test_result in PYTHON_3_9.items():
            with self.subTest(code):
                test_code(self, code, test_result)

    def test_from_changelog(self):
        """
        Generate test cases by looking through the Python 2 & 3 documentation for versionchanged/versionadded nodes.
        Then based on the node's context, generate a test case.
        Python library documentation: https://github.com/python/cpython/tree/main/Doc/library
        Note: As it turns out, the changelog pages itself don't always include all changes from the whole documentation
        """

        # Clear previous run
        TEST_CASES_FILE_PY2.unlink(missing_ok=True)
        TEST_CASES_FILE_PY3.unlink(missing_ok=True)

        # We combine the results, since some features are both belonging to python 2.x and python 3.x
        # We need the whole Python source, since a sphinx-extension uses relative importing

        # Using Sphinx app twice in same Python process does cause some errors, so run them in a subprocess (parallel)
        sub2 = subprocess.Popen([
            sys.executable, TESTS_DIR / "generate_test_cases.py", PYTHON_2_VERSION, TEST_CASES_FILE_PY2.absolute()
        ])
        sub3 = subprocess.Popen([
            sys.executable, TESTS_DIR / "generate_test_cases.py", PYTHON_3_VERSION, TEST_CASES_FILE_PY3.absolute()
        ])
        self.assertEqual(sub2.wait(), 0)
        self.assertEqual(sub3.wait(), 0)

        test_cases = get_test_cases()

        failed_per_version = defaultdict(int)

        # Now test the generated test cases (in alphabetic order)
        for code, expected in sorted(test_cases.items()):
            with self.subTest(code):
                try:
                    test_code(self, code, expected)
                except AssertionError:
                    version = max(expected.keys(), key=lambda versions: tuple(map(int, versions.split('.'))))
                    failed_per_version[version] += 1
                    raise

        logger.info("Plotting Vermin vs Test graph ...")
        plot_vermin_vs_test_features(vermin_rules_per_python_version(),
                                     tested_features_per_python_version(test_cases), failed_per_version)


class TestGenerator(unittest.TestCase):
    # See: https://github.com/python/typeshed/blob/main/stdlib/VERSIONS and
    # https://docs.python.org/3/whatsnew/index.html
    PYTHON_3_MODULES = {
        3.0: {'reprlib', 'winreg', 'html', 'http', '_socket', 'queue', 'configparser', 'tkinter', 'socketserver',
              'builtins', '_imp', 'xmlrpc'},
        3.1: {'_compat_pickle', 'tkinter.ttk', 'importlib'},
        3.2: {'_posixsubprocess', 'concurrent', 'concurrent.futures' 'sysconfig'},
        3.3: {'ipaddress', 'collections.abc', '_winapi', '_decimal', 'venv', 'faulthandler', 'lzma'},
        3.4: {'selectors', 'pathlib', 'statistics', '_stat', 'asyncio', '_tracemalloc', 'enum', 'tracemalloc',
              '_sitebuiltins', '_operator',
              # 'ensurepip' Both in 2.7 and >3.4
              },
        3.5: {'_compression', 'typing', '_pydecimal', 'zipapp'},
        3.6: {'secrets'},
        3.7: {'asyncio.format_helpers', 'asyncio.runners', 'dataclasses', 'contextvars', '_py_abc',
              'importlib.resources'},
        3.8: {'asyncio.exceptions', 'asyncio.staggered', 'asyncio.trsock', 'importlib.metadata',
              'multiprocessing.resource_tracker', 'multiprocessing.shared_memory', 'unittest.async_case'},
        3.9: {'asyncio.threads', 'graphlib', 'zoneinfo', 'unittest._log'},
        3.10: {'asyncio.mixins', 'importlib.metadata._meta'},
        3.11: {'tomllib', 'asyncio.taskgroups', 'wsgiref.types'}
    }

    def test_python3_modules(self):
        test_cases = get_test_cases()
        for version, modules in TestGenerator.PYTHON_3_MODULES.items():
            for module in modules:
                with self.subTest(version=version, module=module):
                    self.assertEqual(test_cases[f"import {module}"], {str(version): {f"'{module}' module": 1}})

        self.assertEqual(test_cases['import ensurepip'],
                         {'2.7': {"'ensurepip' module": 1}, '3.4': {"'ensurepip' module": 1}})


if __name__ == '__main__':
    unittest.main()
