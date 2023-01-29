import ast
import os
import sys
from pathlib import Path

import sphinx.application
import sphinx.domains.python


def get_variable_from_file(file: Path, variable_name: str):
    with file.open() as f:
        for e in ast.parse(f.read()).body:
            if isinstance(e, ast.Assign):
                name = e.targets[0]
                if isinstance(name, ast.Name) and name.id == variable_name:
                    return [c.value for c in e.value.elts]


def generate_test_cases(doc_dir: Path, output_file: Path):
    # Monkey patch the following two classes, which are replacements in newer version of Sphinx
    # Only needed for Python-2.7.18\Doc\tools\extensions\pyspecific.py
    sphinx.domains.python.PyModulelevel = sphinx.domains.python.PyFunction
    sphinx.domains.python.PyClassmember = sphinx.domains.python.PyMethod

    # Load 'extensions' dynamically from the conf.py file (https://github.com/python/cpython/blob/main/Doc/conf.py)
    # and add our extension to it
    extensions = get_variable_from_file(doc_dir / 'conf.py', "extensions") + ['sphinx_extension']

    # Options can be found here:
    # https://www.sphinx-doc.org/en/master/usage/configuration.html
    # https://www.sphinx-doc.org/en/master/man/sphinx-build.html
    app = sphinx.application.Sphinx(
        srcdir=doc_dir,
        confdir=doc_dir,
        outdir=doc_dir / 'build',
        doctreedir=doc_dir / 'build' / '.doctrees',
        buildername="xml",  # Can also be "dummy"; trees are now only saved for debugging purposes
        keep_going=True,
        parallel=os.cpu_count() // 2,
        confoverrides={'extensions': extensions}
    )

    # Add this custom config value so extension knows where to save the test cases (different for each Python version)
    # Note: Doing this in 'confoverrides' above will give a warning
    app.add_config_value('pyternity_test_cases_file', output_file, False, Path)

    # Generate test cases
    app.build()

    return app.statuscode


if __name__ == '__main__':
    _, python_doc_dir, test_cases_file = sys.argv
    status_code = generate_test_cases(Path(python_doc_dir), Path(test_cases_file))
    exit(status_code)
