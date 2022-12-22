import shutil
import unittest
import warnings

from sphinx.application import Sphinx

from pyternity.utils import TMP_DIR, setup_project, Config, ROOT_DIR
from tests.test_utils import test_code

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

sphinx_test_case: unittest.TestCase


def get_sphinx_test_case():
    global sphinx_test_case
    return sphinx_test_case


class TestFeatures(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        setup_project()
        Config.vermin.set_processes(1)

    def test_version_3_9(self):
        for code, test_result in PYTHON_3_9.items():
            test_code(self, code, test_result)

    def test_from_changelog(self):
        # Copy the custom sphinx extension to the right place
        doc_dir = TMP_DIR / 'Python' / 'Doc'
        sphinx_file = ROOT_DIR / 'tests' / 'sphinx_extension.py'
        shutil.copyfile(sphinx_file, doc_dir / 'tools' / 'extensions' / 'sphinx_extension.py')

        # TODO Download (the latest) python source

        # We need the whole Python source, since a sphinx-extension uses relative importing

        # TODO load extensions dynamically from the conf.py file
        # spec = importlib.util.spec_from_file_location('sphinx.conf', doc_dir / 'conf.py')
        # module = importlib.util.module_from_spec(spec)
        # sys.modules['sphinx.conf'] = module
        # spec.loader.exec_module(module)
        # See conf.py for all settings (https://github.com/python/cpython/blob/main/Doc/conf.py)
        extensions = ['sphinx.ext.coverage', 'sphinx.ext.doctest', 'pyspecific', 'c_annotations', 'escape4chm',
                      'asdl_highlight', 'peg_highlight', 'glossary_search', 'sphinx_extension']

        # TODO do something with the warnings (not from my code, but from python source)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            srcdir = str(doc_dir.absolute())
            exclude_patterns = {f"{f.name}/*" if f.is_dir() else f.name for f in doc_dir.iterdir()} - {"library/*"}

            # Options can be found here:
            # https://www.sphinx-doc.org/en/master/usage/configuration.html
            # https://www.sphinx-doc.org/en/master/man/sphinx-build.html
            app = Sphinx(
                srcdir=srcdir,
                confdir=srcdir,
                outdir=str((doc_dir / 'build').absolute()),
                doctreedir=str(((doc_dir / 'build' / '.doctrees').absolute())),
                buildername="dummy",
                freshenv=True,
                keep_going=True,
                confoverrides={
                    'extensions': ','.join(extensions),
                    'exclude_patterns': ','.join(exclude_patterns)  # We are only interested in library changes
                }
            )

            app.build()
            self.assertEquals(app.statuscode, 0)


if __name__ == '__main__':
    unittest.main()
