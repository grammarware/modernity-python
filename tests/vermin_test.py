import ast
import unittest
from pathlib import Path

import sphinx.domains.python
import sphinx.application

from pyternity.utils import TMP_DIR, setup_project, Config
from tests.test_utils import test_code, get_test_cases, TEST_CASES_FILE

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
        setup_project()
        Config.vermin.set_processes(1)

    def test_version_3_9(self):
        for code, test_result in PYTHON_3_9.items():
            test_code(self, code, test_result)

    def test_from_changelog(self):
        # Clear previous run
        TEST_CASES_FILE.unlink(missing_ok=True)

        # TODO Download (the latest?) python sources:
        #  2.7 will not change: https://www.python.org/downloads/release/python-2718/
        #  3.x
        # We combine the results, since some features are both belonging to python 2.x and python 3.x
        # We need the whole Python source, since a sphinx-extension uses relative importing

        # Monkey patch the following two classes, which are replacements in newer version of sphinx
        # Used in extensions/pyspecific.py (only for Python 2.7)
        sphinx.domains.python.PyModulelevel = sphinx.domains.python.PyFunction
        sphinx.domains.python.PyClassmember = sphinx.domains.python.PyMethod
        self.assertEqual(generate_test_cases(TMP_DIR / 'Python-2.7.18' / 'Doc'), 0)

        # Using Sphinx app twice, does cause some errors, which don't appear when running this version solely
        # But these errors don't seem to hinder our results
        self.assertEqual(generate_test_cases(TMP_DIR / 'Python3' / 'Doc'), 0)

        for code, expected in get_test_cases().items():
            test_code(self, code, expected)


def generate_test_cases(doc_dir: Path):
    # Load 'extensions' dynamically from the conf.py file (https://github.com/python/cpython/blob/main/Doc/conf.py)
    # And add our extension to it
    extensions = get_variable_from_file(doc_dir / 'conf.py', "extensions") + ['sphinx_extension']

    # Options can be found here:
    # https://www.sphinx-doc.org/en/master/usage/configuration.html
    # https://www.sphinx-doc.org/en/master/man/sphinx-build.html
    app = sphinx.application.Sphinx(
        srcdir=doc_dir,
        confdir=doc_dir,
        outdir=doc_dir / 'build',
        doctreedir=doc_dir / 'build' / '.doctrees',
        buildername="dummy",
        freshenv=True,
        keep_going=True,
        confoverrides={'extensions': ','.join(extensions)}
    )

    # Generate test cases
    app.build()

    return app.statuscode


def get_variable_from_file(file: Path, variable_name: str):
    with file.open() as f:
        for e in ast.parse(f.read()).body:
            if isinstance(e, ast.Assign):
                name = e.targets[0]
                if isinstance(name, ast.Name) and name.id == variable_name:
                    return [c.value for c in e.value.elts]


if __name__ == '__main__':
    unittest.main()
