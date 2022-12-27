import ast
import sys
from pathlib import Path

import sphinx.application
import sphinx.domains.python

from pyternity.utils import TMP_DIR, setup_project


def get_variable_from_file(file: Path, variable_name: str):
    with file.open() as f:
        for e in ast.parse(f.read()).body:
            if isinstance(e, ast.Assign):
                name = e.targets[0]
                if isinstance(name, ast.Name) and name.id == variable_name:
                    return [c.value for c in e.value.elts]


def generate_test_cases(doc_dir: Path, output_file: Path):
    # Monkey patch the following two classes, which are replacements in newer version of sphinx
    # Only need for Python-2.7.18\Doc\tools\extensions\pyspecific.py
    sphinx.domains.python.PyModulelevel = sphinx.domains.python.PyFunction
    sphinx.domains.python.PyClassmember = sphinx.domains.python.PyMethod

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
        buildername="xml",  # Can also be dummy; trees are now only generated for debugging purposes
        keep_going=True,
        # parallel=os.cpu_count() // 2,
        confoverrides={'extensions': ','.join(extensions)}
    )

    # Add this custom config value so extension knows where to save the test cases (different for version 2/3)
    # Doing this in 'confoverrides' will give a warning
    app.add_config_value('pyternity_test_cases_file', output_file, False, str)

    # Generate test cases
    app.build()

    return app.statuscode


if __name__ == '__main__':
    _, python_version, test_cases_file = sys.argv

    # Since this is a separate subprocess, also initiate config here
    setup_project(1)

    status_code = generate_test_cases(TMP_DIR / f"Python-{python_version}" / 'Doc', Path(test_cases_file))
    exit(status_code)
