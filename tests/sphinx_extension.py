import multiprocessing
import pickle
import re
from functools import reduce
from pathlib import Path
from traceback import TracebackException

from sphinx.application import Sphinx
import sphinx.addnodes
import docutils.nodes

from pyternity.utils import Features, logger
from tests.test_utils import get_features_from_test_code, combine_features, save_test_cases, normalize_expected

# Python documentation is not consistent in when a new parameter has been added...
HAS_NEW_PARAMETER = re.compile(
    r"((the )?((optional|keyword-only|keyword) )?((parameter|flag|argument)s?) ((was|were) )?added)|"
    r"((added|introduced) (support for )?(the )?((optional|keyword-only|keyword) )?((parameter|flag|argument)s?))|"
    r"(^(was|were|attributes) added$)|"
    r"(^added support for$)|"
    r"(^the parameter is new$)",
    re.IGNORECASE
)


def generate_test_cases(outdir: str, doctree_file: Path) -> dict[str, Features]:
    with doctree_file.open('rb') as f:
        doctree: sphinx.addnodes.document = pickle.load(f)

    test_cases = {}
    source = Path(doctree.get('source'))
    logger.info(f"Processing {source}...")

    # TODO This does not test features that are completely removed in the Python docs
    for node in doctree.findall(sphinx.addnodes.versionmodified):
        version = node.get('version')
        # TODO handle version if it is a tuple
        if isinstance(version, str):
            try:
                new_test_cases = handle_versionmodified(version, node)
                if not new_test_cases:
                    # TODO Handle cases it does not find anything
                    continue

                for new_test_case in new_test_cases:
                    code, expected = new_test_case
                    normalize_expected(expected)
                    # Only update, if test_code was not a test_case yet
                    test_cases.setdefault(code, dict(expected))

            except Exception as e:
                # TODO fix all errors; and code that did not result in a testcase
                doc_tree_file = Path(outdir) / source.parent.name / (source.stem + '.xml')
                logger.error(
                    f":: VERSIONMODIFIED ERROR ::\n"
                    f'File "{source}", line {node.line}\n'
                    f'File "{doc_tree_file}", line {node.line}\n'
                    ''.join(TracebackException.from_exception(e).format())
                )

    return test_cases


def new_parameters_from_node(node: sphinx.addnodes.versionmodified):
    # Parameter names are stored in emphasis nodes
    emphasises = [param.astext() for param in node.traverse(docutils.nodes.emphasis)]
    if not emphasises:
        return

    nodes = node.next_node(docutils.nodes.paragraph)[0].traverse(docutils.nodes.Text, descend=False, siblings=True)
    text = ' '.join(str(n).strip() for n in nodes).replace('and ', '').replace(' ,', '').rstrip(' .')

    if HAS_NEW_PARAMETER.match(text):
        return emphasises
    else:
        print(repr(''.join(n.astext() for n in node[0][1:]).replace('\n', ' ')))
        print(repr(text))
        print()


def handle_versionmodified(version: str, node: sphinx.addnodes.versionmodified) -> list[tuple[str, Features]] | None:
    # Vermin does not detect deprecation, so skip these nodes
    if node.get('type') == 'deprecated':
        return

    description = node.next_node(docutils.nodes.paragraph)
    feature_added = node.get('type') == 'versionadded'

    if isinstance(desc := node.parent.parent, sphinx.addnodes.desc):
        desc_signature = desc.next_node(sphinx.addnodes.desc_signature)

        if desc.get('objtype') in ('opcode', 'cmdoption', 'pdbcommand'):
            return

        if feature_added:
            # New method/class/function/exception/attribute/constants(data)
            # https://devguide.python.org/documentation/markup/#information-units
            assert desc.get('objtype') in ('method', 'class', 'function', 'exception', 'attribute', 'data'), \
                f"Other objtype={desc.get('objtype')} found"

            # These nodes should have only 1 (inline) element in their paragraph?
            if len(description.children) == 1:
                module = desc_signature.get('module')
                ids = desc_signature.get('ids')[0]
                prev_ids = ids.rsplit('.', maxsplit=1)[0]

                # TODO Maybe there are also constants?
                import_stmt = f"import {module}\n" if module else ''
                prev_features = get_features_from_test_code(f"{import_stmt}{prev_ids}")

                return [(
                    f"{import_stmt}{ids}()", combine_features(prev_features, {version: {f"'{ids}' member": 1}})
                )]

        else:
            # Thing changed, check if new parameters were added

            # Only callables can have parameters added
            if desc.get('objtype') not in ('method', 'class', 'function', 'exception'):
                return

            new_parameters = new_parameters_from_node(node)
            if not new_parameters:
                return

            module = desc_signature.get('module')
            ids = desc_signature.get('ids')[0]
            import_stmt = f"import {module}\n" if module else ''
            prev_features = get_features_from_test_code(f"{import_stmt}{ids}()")

            # The value assigned to the named parameter does not matter
            # (technically you good also grab the default parameter value from desc_signature)
            # Generate separate test cases for each parameter, else combine 2 and 3 test cases may clash
            return [(
                f"{import_stmt}{ids}({new_parameter}=None)",
                combine_features(prev_features, {version: {f"'{ids}({new_parameter})'": 1}})
            ) for new_parameter in new_parameters]

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

                return [(
                    f"import {module_name}", Features(Features, {version: {f"'{module_name}' module": 1}})
                )]


def build_finished(app: Sphinx, _):
    # Build finished event will always be triggered. Using this event we can also generate our test cases even when
    # then input files have not changed, so we used the cached doctrees. We can do this, since our extension does not
    # modify this doctree.
    # Load doctree files here with pickle

    # We are only interested in changes in the library
    library_doctrees_dir = Path(app.doctreedir) / 'library'

    with multiprocessing.Pool(processes=app.parallel) as pool:
        new_test_cases = pool.starmap(generate_test_cases, ((app.outdir, p) for p in library_doctrees_dir.iterdir()))
        test_cases = reduce(dict.__ior__, new_test_cases)
        save_test_cases(app.config['pyternity_test_cases_file'], test_cases)


def setup(app: Sphinx):
    app.connect('build-finished', build_finished)
    return {'version': '1.0'}
