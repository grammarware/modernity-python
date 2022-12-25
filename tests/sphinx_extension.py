from collections import defaultdict
from pathlib import Path

import sphinx.application
import sphinx.addnodes
import docutils.nodes
from docutils.nodes import paragraph, serial_escape

from pyternity.utils import Features
from tests.test_utils import get_features_from_test_code, save_doc_tree, combine_features, save_test_cases


# TODO Maybe use XML builder instead?
def _dom_node(self, domroot):
    element = domroot.createElement(self.tagname)
    for attribute, value in self.attlist():
        if isinstance(value, list) or isinstance(value, tuple):  # Added `isinstance(value, tuple)` to support tuples
            value = ' '.join(serial_escape('%s' % (v,)) for v in value)
        element.setAttribute(attribute, '%s' % value)
    for child in self.children:
        element.appendChild(child._dom_node(domroot))
    return element


# Monkey patch to support tuple values (used in Python3\Doc\library\2to3.rst)
docutils.nodes.Element._dom_node = _dom_node

test_cases: defaultdict[str, Features]


def generate_test_cases(app: sphinx.application.Sphinx, doctree: sphinx.addnodes.document):
    global test_cases

    # We are only interested in changes in the library
    source = Path(doctree.attributes['source'])
    if source.parent.name != "library":
        return

    print(source)

    # Save doctree for debugging purposes
    save_doc_tree(app.outdir, source.stem, doctree.asdom().toprettyxml())

    # TODO This does not test features that are completely removed in the Python docs
    for node in doctree.findall(sphinx.addnodes.versionmodified):
        version = node.attributes['version']
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
    desc = node.parent.parent
    desc_signature: sphinx.addnodes.desc_signature = desc[0]

    if node.attributes['type'] == "versionadded":
        # New method for some class, or a new class, or a new function
        if desc.attributes.get('objtype') in ("method", "class", "function"):
            module = desc_signature.attributes['module']
            ids: str = desc_signature.attributes['ids'][0]
            prev_ids = ids.rsplit('.', maxsplit=1)[0]

            # If there is no import statement (i.e. it is a builtin), call the thing
            # TODO Maybe there are also constants?
            import_stmt = f"import {module}\n" if module else ""
            prev_features = get_features_from_test_code(f"{import_stmt}{prev_ids}{'()' if not import_stmt else ''}")

            return (
                f"{import_stmt}{ids}{'()' if not import_stmt else ''}",
                combine_features(prev_features, {version: {f"'{ids}' member": 1}})
            )

        # New module
        # This node should be before a <paragraph>, then it tells something about the whole module
        if desc.tagname == "document" \
                and node.line < desc_signature[desc_signature.first_child_matching_class(paragraph)].line:
            module = desc_signature.attributes['names'][0].split(' ')[0]

            # TODO Currently only AST module has two versionmodified nodes, take first one
            # p: paragraph = node[0]
            # if len(p.children) != 1:
            #     # AST (2/3),
            #     print(module)
            #     # breakpoint()

            return f"import {module}", {version: {f"'{module}' module": 1}}

    elif node.attributes['type'] == "versionchanged":
        # New parameter has been added to a method
        if desc.attributes.get('objtype') in ("method",):
            try:
                param_name = node[0][1][1][0]
            except IndexError:
                # Case when argument already existed, but was now given default value
                return

            # The value assigned to the named parameter does not matter
            # (technically you good also grab the default parameter value from desc_signature)

            # TODO return desc_signature.attributes['module'], f"{desc_signature.attributes['ids'][0]}({param_name}=None)"


def build_finished(app: sphinx.application.Sphinx, _):
    global test_cases
    save_test_cases(app.config.overrides.get('pyternity_test_cases_file'), test_cases)


def setup(app: sphinx.application.Sphinx):
    global test_cases
    test_cases = defaultdict(lambda: defaultdict(Features))

    app.connect('doctree-read', generate_test_cases)
    app.connect('build-finished', build_finished)
    return {'version': '1.0', 'parallel_read_safe': True}
