import re
import unittest
from pathlib import Path

from sphinx.builders.changes import ChangesBuilder

from pyternity import features
from pyternity.utils import Features, TMP_DIR, setup_project, Config


def msg_features(d: Features):
    return {k: dict(sorted(v.items())) for k, v in sorted(d.items())}


# Idea; read all doc files, and look for  .. versionchanged / .. versionadded
# https://github.com/python/cpython/tree/main/Doc/library


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


# from concurrent import futures
# futures.Executor().shutdown(cancel_futures=True)

class TestFeatures(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        setup_project()
        Config.vermin.set_processes(1)

    def test_version_3_9(self):
        for test_code, test_result in PYTHON_3_9.items():
            # Note: tempfile library cannot be used here, since Vermin reopens the file
            tmp_file = TMP_DIR / "python39.py"

            if not tmp_file.exists():
                with tmp_file.open('w') as f:
                    f.write(test_code)

            f = features.get_features(tmp_file)
            tmp_file.unlink()

            with self.subTest(test_code):
                self.assertDictEqual(f, test_result, msg_features(f))


from html.parser import HTMLParser


class MyHTMLParser(HTMLParser):

    CLEAN_DATA = re.compile(r" +")
    ADDED_PARAMETER = re.compile(r"Added the (.*) parameter")
    NEW_IN_VERSION = re.compile(r"New in version \d+\.\d+\.")

    def __init__(self, *, convert_charrefs: bool = ...):
        super().__init__()
        self.new_thing = ""
        self.current_module = ""

    def handle_starttag(self, tag, attrs):
        pass
        # print("Encountered a start tag:", tag)

    def handle_endtag(self, tag):
        pass
        # print("Encountered an end tag :", tag)

    def handle_data(self, data):
        data = data.strip().replace('\n', '')
        data = self.CLEAN_DATA.sub(' ', data)
        if data in ("", ":"):
            return

        # print(f"{self.lasttag=}; {data=}")

        if self.lasttag == 'h4':
            self.current_module = data.lower()

        elif self.lasttag == 'b':
            self.new_thing = data

        elif self.lasttag == 'h2' and data != 'Library changes':
            raise StopIteration

        elif self.lasttag == 'i':
            if self.NEW_IN_VERSION.fullmatch(data):

                if self.new_thing.startswith('-'):
                    # We do not test for newly added CLI parameters
                    return

                # print('new function/class etc..', self.current_module, self.new_thing)
                print(f"import {self.current_module}\n{self.current_module}.{self.new_thing}")

            #



            # if self.ADDED_PARAMETER.match(data):
            #     print("New parameter: ...", data)

        pass
        # print("Encountered some data  :", data)


def build_tests_from_changes(changes_html_file: Path):
    parser = MyHTMLParser()

    with changes_html_file.open() as f:
        try:
            parser.feed(f.read())
        except StopIteration:
            pass


class TestFromDocs(unittest.TestCase):
    def test_docs(self):
        html_file = TMP_DIR / 'cpython-main' / 'Doc' / 'build' / 'changes311' / 'changes.html'

        build_tests_from_changes(html_file)

    # Steps:
    # Download the latest python source
    # See conf.py for all settings (https://github.com/python/cpython/blob/main/Doc/conf.py)
    # Run .\sphinx-build.exe -bchanges -D version=3.11 -D release=3.11.0 C:\Users\cpAdm\PycharmProjects\Pyternity\tmp\cpython-main\Doc C:\Users\cpAdm\PycharmProjects\Pyternity\tmp\cpython-main\Doc\build\changes311


if __name__ == '__main__':
    unittest.main()
