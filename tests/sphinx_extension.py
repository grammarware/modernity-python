from pathlib import Path

import sphinx.application
import sphinx.addnodes

from tests.test_utils import get_features_from_test_code, save_test_case


def generate_test_cases(app: sphinx.application.Sphinx, doctree: sphinx.addnodes.document):
    # We are only interested in changes in the library
    source = doctree.attributes['source']
    if Path(source).parent.name != "library":
        return

    print(source)

    # TODO This does not test features that are completely removed in the Python docs
    for node in doctree.findall():
        if node.tagname != "versionmodified":
            continue

        version = node.attributes['version']
        # TODO handle version if it is a tuple
        if isinstance(version, str):
            try:
                test_case = handle_versionmodified(version, node)
            except:
                # TODO fix all errors
                continue
            if test_case:
                save_test_case(*test_case)
            else:
                pass
                # TODO handle other

    print("\n\n")


def handle_versionmodified(version: str, node: sphinx.addnodes.versionmodified) -> tuple[str, str] | None:
    desc = node.parent.parent
    desc_signature: sphinx.addnodes.desc_signature = desc[0]

    if node.attributes['type'] == "versionadded":
        # New method for some class, or a new class, or a new function
        if desc.attributes.get('objtype') in ("method", "class", "function"):
            module = desc_signature.attributes['module']
            ids: str = desc_signature.attributes['ids'][0]
            prev_ids = ids.rsplit('.', maxsplit=1)[0]

            import_stmt = f"import {module}\n" if module else ""
            prev_features = get_features_from_test_code(f"{import_stmt}{prev_ids}")

            return save_test_case(f"{import_stmt}{ids}", prev_features | {version: {f"'{ids}' member": 1}})

        # New module
        if desc.tagname == "document" and desc_signature[2] == node:
            module = desc_signature.attributes['ids'][0].lstrip('module-')
            return save_test_case(f"import {module}", {version: {f"'{module}' module": 1}})

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


def setup(app: sphinx.application.Sphinx):
    app.connect('doctree-read', generate_test_cases)
    return {'version': '1.0', 'parallel_read_safe': True}
