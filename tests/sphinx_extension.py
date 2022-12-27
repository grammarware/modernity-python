import pickle
from collections import defaultdict
from pathlib import Path
from traceback import TracebackException

import sphinx.application
import sphinx.addnodes
import docutils.nodes

from pyternity.utils import Features
from tests.test_utils import get_features_from_test_code, combine_features, save_test_cases, normalize_expected


def generate_test_cases(
        app: sphinx.application.Sphinx, doctree: sphinx.addnodes.document, test_cases: defaultdict[str, Features]
):
    source = Path(doctree.get('source'))

    # TODO This does not test features that are completely removed in the Python docs
    for node in doctree.findall(sphinx.addnodes.versionmodified):
        version = node.get('version')
        # TODO handle version if it is a tuple
        if isinstance(version, str):
            try:
                new_test_case = handle_versionmodified(version, node)
                if not new_test_case:
                    # TODO Handle cases it does not find anything
                    continue

                code, expected = new_test_case
                normalize_expected(expected)
                # Only update, if test_code was not a test_case yet
                test_cases.setdefault(code, expected)

            except Exception as e:
                # TODO fix all errors; and code that did not result in a testcase
                doc_tree_file = Path(app.outdir) / source.parent.name / (source.stem + '.xml')
                print(f':: VERSIONMODIFIED ERROR ::')
                print(f"File {source}, line {node.line}")
                print(f"File {doc_tree_file}, line {node.line}")
                print(''.join(TracebackException.from_exception(e).format()))
                continue

    print("\n\n")


def handle_versionmodified(version: str, node: sphinx.addnodes.versionmodified) -> tuple[str, Features]:
    description = node.next_node(docutils.nodes.paragraph)
    feature_added = node.get('type') == "versionadded"

    if isinstance(desc := node.parent.parent, sphinx.addnodes.desc):
        desc_signature = desc.next_node(sphinx.addnodes.desc_signature)

        if feature_added:
            # New method/class/function/exception/attribute/constants(data)
            # https://devguide.python.org/documentation/markup/#information-units
            # These nodes should have only 1 (inline) element in their paragraph?
            if desc.get('objtype') in ("method", "class", "function", "exception", "attribute", "data"):
                if len(description.children) == 1:
                    module = desc_signature.get('module')
                    ids = desc_signature.get('ids')[0]
                    prev_ids = ids.rsplit('.', maxsplit=1)[0]

                    # If there is no import statement (i.e. it is a builtin), call the thing
                    # TODO Maybe there are also constants?
                    import_stmt = f"import {module}\n" if module else ""
                    prev_features = get_features_from_test_code(
                        f"{import_stmt}{prev_ids}{'()' if not import_stmt else ''}")

                    return (
                        f"{import_stmt}{ids}{'()' if not import_stmt else ''}",
                        combine_features(prev_features, {version: {f"'{ids}' member": 1}})
                    )

    if isinstance(document := node.parent.parent, sphinx.addnodes.document):
        section = document.next_node(docutils.nodes.section)

        if feature_added:
            # New module
            # This node should be before a <paragraph>, then it tells something about the whole module
            # "When this applies to an entire module,
            # it should be placed at the top of the module section before any prose."
            if node.line < section.next_node(docutils.nodes.paragraph).line:
                module_name = section.get('names')[0].split(' ')[0]

                # TODO Currently only AST module has two versionmodified nodes, take first one

                return f"import {module_name}", {version: {f"'{module_name}' module": 1}}

    # elif node.attributes['type'] == "versionchanged":
    #     # New parameter has been added to a method
    #     if parent_parent.attributes.get('objtype') in ("method",):
    #         try:
    #             param_name = node[0][1][1][0]
    #         except IndexError:
    #             # Case when argument already existed, but was now given default value
    #             return
    #
    #         # The value assigned to the named parameter does not matter
    #         # (technically you good also grab the default parameter value from desc_signature)
    #
    #         # TODO return desc_signature.attributes['module'], f"{desc_signature.attributes['ids'][0]}({param_name}=None)"


def build_finished(app: sphinx.application.Sphinx, _):
    test_cases = defaultdict(lambda: defaultdict(Features))

    # Build finished event will always be triggered. Using this event we can also generate our test cases even when
    # then input files have not changed, so we used the cached doctrees. We can do this, since our extension does not
    # modify this doctree.
    # Load doctree files here with pickle
    # TODO This can also be run in parallel

    # We are only interested in changes in the library
    library_doctrees_dir = Path(app.doctreedir) / 'library'
    for doctree_file in library_doctrees_dir.iterdir():
        print(doctree_file.absolute())
        with doctree_file.open('rb') as f:
            doctree = pickle.load(f)
            generate_test_cases(app, doctree, test_cases)

    save_test_cases(app.config['pyternity_test_cases_file'], test_cases)


def setup(app: sphinx.application.Sphinx):
    app.connect('build-finished', build_finished)
    return {'version': '1.0'}
