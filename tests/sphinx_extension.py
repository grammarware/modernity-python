from collections import defaultdict
from pathlib import Path
from typing import TypeVar

import sphinx.application
import sphinx.addnodes
import docutils.nodes

from pyternity.utils import Features
from tests.test_utils import get_features_from_test_code, combine_features, save_test_cases

T = TypeVar('T')

test_cases: defaultdict[str, Features]


def generate_test_cases(app: sphinx.application.Sphinx, doctree: sphinx.addnodes.document):
    global test_cases

    # We are only interested in changes in the library
    source = Path(doctree.get('source'))
    if source.parent.name != "library":
        return

    print(source)

    # TODO This does not test features that are completely removed in the Python docs
    for node in doctree.findall(sphinx.addnodes.versionmodified):
        version = node.get('version')
        # TODO handle version if it is a tuple
        if isinstance(version, str):
            try:
                code, expected = handle_versionmodified(version, node)
                test_cases[code] |= expected

            except Exception as e:
                # TODO fix all errors; and code that did not result in a testcase
                print("VERSIONMODIFIED ERROR:")
                print(e)
                continue

    print("\n\n")


def handle_versionmodified(version: str, node: sphinx.addnodes.versionmodified) -> tuple[str, Features]:
    description = node.next_node(docutils.nodes.paragraph)
    feature_added = node.get('type') == "versionadded"

    if isinstance(desc := node.parent.parent, sphinx.addnodes.desc):
        desc_signature = desc.next_node(sphinx.addnodes.desc_signature)

        if feature_added:
            # New method for some class, or a new class, or a new function
            # These nodes have only 1 (inline) element in their paragraph
            if desc.get('objtype') in ("method", "class", "function") and len(description.children) == 1:
                module = desc_signature.get('module')
                ids = desc_signature.get('ids')[0]
                prev_ids = ids.rsplit('.', maxsplit=1)[0]

                # If there is no import statement (i.e. it is a builtin), call the thing
                # TODO Maybe there are also constants?
                import_stmt = f"import {module}\n" if module else ""
                prev_features = get_features_from_test_code(f"{import_stmt}{prev_ids}{'()' if not import_stmt else ''}")

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
    global test_cases
    save_test_cases(app.config.overrides.get('pyternity_test_cases_file'), test_cases)


def setup(app: sphinx.application.Sphinx):
    global test_cases
    test_cases = defaultdict(lambda: defaultdict(Features))

    app.connect('doctree-read', generate_test_cases)
    app.connect('build-finished', build_finished)
    return {'version': '1.0', 'parallel_read_safe': True}
