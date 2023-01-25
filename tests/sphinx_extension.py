import multiprocessing
import pickle
import re
from functools import reduce
from itertools import chain

import docutils.nodes
import sphinx.addnodes
from sphinx.application import Sphinx

from pyternity.utils import *
from tests.test_utils import get_features_from_test_code, combine_features, save_test_cases, normalize_expected

# Python documentation is not consistent in when a new parameter has been added...
parameter = (r"(support for )?(the )?((optional|required|keyword(-only)?) )?"
             r"((parameter|flag|argument|option|attribute|keyword)s?)")
HAS_NEW_PARAMETER = re.compile(
    fr"({parameter} ((was|were|is|are|has been) )?added)|"
    fr"((add(ed)?|introduced) {parameter})|"
    fr"(^(new )?{parameter}$)|"
    r"(^(was|were) added$)|"
    r"(^added( the support| support for)?$)|"
    r"(^the keyword-only argument$)|"
    r"(^the parameter( is new)?$)",
    re.IGNORECASE
)


def generate_test_cases(out_dir: str, doctree_file: Path) -> dict[str, Features]:
    # Load the cached doctree (Sphinx caches this automatically after (the first) doctree build)
    with doctree_file.open('rb') as f:
        doctree: sphinx.addnodes.document = pickle.load(f)

    test_cases = {}
    source = Path(doctree.get('source'))
    # TODO Fix logging within this subprocess
    logger.info(f"Processing {source} ...")

    # TODO This does not test features that are completely removed in the Python docs
    for node in doctree.findall(sphinx.addnodes.versionmodified):
        version = node.get('version')
        # TODO handle version if it is a tuple
        if isinstance(version, str):
            new_test_cases = handle_versionmodified(version, node)

            if not new_test_cases:
                # TODO Handle cases it does not find anything
                doc_tree_file = Path(out_dir) / source.parent.name / (source.stem + '.xml')
                logger.debug(
                    f"Did not generate any test cases for this versionmodified node:\n"
                    f'File "{source}", line {node.line}\n'
                    f'File "{doc_tree_file}", line {node.line}'
                )
                continue

            for new_test_case in new_test_cases:
                code, expected = new_test_case
                normalize_expected(expected)
                # Only update, if test_code was not a test_case yet
                test_cases.setdefault(code, dict(expected))

    return test_cases


def new_parameters_from_node(node: sphinx.addnodes.versionmodified) -> list[str] | None:
    # Parameter names are stored in emphasis nodes
    emphasises = [param.astext() for param in node.traverse(docutils.nodes.emphasis)]
    if not emphasises:
        return

    # TODO 'Changed in version 2.7.9: cafile, capath, cadefault, and context were added.'
    #  'Changed in version 2.6: pwd was added, and name can now be a ZipInfo object.'
    #  'Changed in version 2.3: the encoding argument was introduced; see writexml().'
    #  'Changed in version 3.2: allow_no_value, delimiters, comment_prefixes, strict,\nempty_lines_in_values, default_section and interpolation were\nadded.'
    #  'Changed in version 3.5: SMTPNotSupportedError may be raised, and the\ninitial_response_ok parameter was added.'

    nodes = node.next_node(docutils.nodes.paragraph)[0].traverse(docutils.nodes.Text, descend=False, siblings=True)
    text = ' '.join(str(n).strip() for n in nodes).replace('and ', '').replace(' ,', '').rstrip(' .')

    if HAS_NEW_PARAMETER.match(text):
        return emphasises


def handle_versionmodified(version: str, node: sphinx.addnodes.versionmodified) -> list[tuple[str, Features]] | None:
    # Vermin does not detect deprecation, so skip these nodes
    if node.get('type') == 'deprecated':
        return

    description = node.next_node(docutils.nodes.paragraph)
    feature_added = node.get('type') == 'versionadded'

    if isinstance(desc := node.parent.parent, sphinx.addnodes.desc):
        # We don't care about newly added or changed opcodes/commands
        if desc.get('objtype') in ('opcode', 'cmdoption', 'pdbcommand'):
            return

        desc_signatures = desc[0].traverse(sphinx.addnodes.desc_signature, siblings=True, descend=False)

        def handle_desc_signature(desc_signature: sphinx.addnodes.desc_signature) -> list[tuple[str, Features]] | None:
            module = desc_signature.get('module')
            import_stmt = f"import {module}\n" if module else ''

            # When same function is listed twice (with different signature), only the first one has 'ids'
            if not desc_signature.get('ids'):
                return
            ids = desc_signature.get('ids')[-1]

            if feature_added:
                # New method/class/function/exception/attribute/constants(data)
                # https://devguide.python.org/documentation/markup/#information-units
                assert desc.get('objtype') in ('method', 'class', 'function', 'exception', 'attribute', 'data'), \
                    f"Other objtype={desc.get('objtype')} found"

                # These nodes should have only 1 (inline) element in their paragraph?
                if len(description.children) == 1:
                    prev_ids = ids.rsplit('.', maxsplit=1)[0]
                    prev_features = get_features_from_test_code(f"{import_stmt}{prev_ids}")

                    # It does not matter for detection if we call something that cannot be called
                    return [(
                        f"{import_stmt}{ids}()", combine_features(prev_features, {version: {f"'{ids}' member": 1}})
                    )]

            else:
                # Thing changed, check if new parameters were added

                # Only callables can have parameters added
                if desc.get('objtype') not in ('method', 'class', 'function', 'exception'):
                    return

                if not (new_parameters := new_parameters_from_node(node)):
                    return

                prev_features = get_features_from_test_code(f"{import_stmt}{ids}()")

                # The value assigned to the named parameter does not matter
                # (technically you good also grab the default parameter value from desc_signature)
                # Generate separate test cases for each parameter, else combine 2 and 3 test cases may clash
                return [(
                    f"{import_stmt}{ids}({new_parameter}=None)",
                    combine_features(prev_features, {version: {f"'{ids}({new_parameter})'": 1}})
                ) for new_parameter in new_parameters]

        return list(chain.from_iterable(filter(None, map(handle_desc_signature, desc_signatures))))

    elif isinstance(document := node.parent.parent, sphinx.addnodes.document):
        section = document.next_node(docutils.nodes.section)

        if feature_added:
            # New module if: "When this applies to an entire module,
            # it should be placed at the top of the module section before any prose."
            # So, this node should be before any new <section> (if any), then it tells something about the whole module
            next_section = section.next_node(docutils.nodes.section)
            if not next_section or node.line < next_section.line:
                # FIXME Names attribute is always lowercase; so is wrong for e.g. 'DocXMLRPCServer'
                module_name = section.get('names')[0].split(' ')[0]

                # TODO Currently only AST module has two versionmodified nodes, take first one

                return [(
                    f"import {module_name}", Features(Features, {version: {f"'{module_name}' module": 1}})
                )]


def build_finished(app: Sphinx, _):
    """
    `build-finished` event will always be triggered (even when there are no changed in the rst files).
    So we use this event to generate our test cases, which also allows us to use the cached doctrees.
    :param app:
    :param _:
    """
    # We are only interested in the library documentation
    library_doctrees_dir = Path(app.doctreedir) / 'library'

    with multiprocessing.Pool(processes=app.parallel) as pool:
        new_test_cases = pool.starmap(generate_test_cases, ((app.outdir, p) for p in library_doctrees_dir.iterdir()))
        test_cases = reduce(dict.__ior__, new_test_cases)
        save_test_cases(app.config['pyternity_test_cases_file'], test_cases)


def setup(app: Sphinx) -> dict:
    """
    This method is called when Sphinx is setting up all the extensions.\n
    See: https://www.sphinx-doc.org/en/master/extdev/index.html
    :param app: The Sphinx app
    :return: Extension metadata
    """
    app.connect('build-finished', build_finished)
    return {'version': '1.0'}
