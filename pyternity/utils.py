import logging
import sys
import warnings
from collections import defaultdict
from datetime import datetime
from operator import itemgetter
from pathlib import Path
from typing import TypeAlias

import vermin
from vermin import MOD_REQS, MOD_MEM_REQS, KWARGS_REQS, STRFTIME_REQS, BYTES_REQS, ARRAY_TYPECODE_REQS, \
    CODECS_ERROR_HANDLERS, CODECS_ENCODINGS, BUILTIN_GENERIC_ANNOTATION_TYPES, DICT_UNION_SUPPORTED_TYPES, \
    DICT_UNION_MERGE_SUPPORTED_TYPES, DECORATOR_USER_FUNCTIONS

Features: TypeAlias = defaultdict[str, defaultdict[str, int]]
Signature: TypeAlias = dict[str, int]

ROOT_DIR = Path(__file__).parent.parent
LOG_FILE = ROOT_DIR / 'pyternity-log.txt'
TMP_DIR = ROOT_DIR / 'tmp'
EXAMPLES_DIR = ROOT_DIR / 'examples'
RESULTS_DIR = ROOT_DIR / 'results'
PLOTS_DIR = ROOT_DIR / 'plots'

PYTHON_RELEASES = {version: datetime.fromisoformat(d) for version, d in {
    "2.0": "2000-10-16",
    "2.1": "2001-04-15",
    "2.2": "2001-12-21",
    "2.3": "2003-06-29",
    "2.4": "2004-11-30",
    "2.5": "2006-09-19",
    "2.6": "2008-10-01",
    "2.7": "2010-07-03",
    "3.0": "2008-12-03",
    "3.1": "2009-06-27",
    "3.2": "2011-02-20",
    "3.3": "2012-09-29",
    "3.4": "2014-03-16",
    "3.5": "2015-09-13",
    "3.6": "2016-12-23",
    "3.7": "2018-06-27",
    "3.8": "2019-10-14",
    "3.9": "2020-10-05",
    "3.10": "2021-10-04",
    "3.11": "2022-10-24"
}.items()}

logger = logging.getLogger('pyternity_logger')


class Config:
    redownload_examples = False
    recalculate_examples = False
    vermin = vermin.Config.parse_file(vermin.Config.detect_config_file())


def sort_features(features: Features) -> dict[str, dict[str, int]]:
    """
    :param features: Features to sort
    :return: Return a new dict where features are sorted on version,
    and within each version it is sorted on how often it occurs (descending)
    """
    return {py_v: dict(sorted(features[py_v].items(), key=itemgetter(1), reverse=True)) for py_v in PYTHON_RELEASES}


def parse_vermin_version(version: str) -> str | None:
    if target := vermin.utility.parse_target(version):
        return f"{target[1][0]}.{target[1][1]}"


class NonErrorsFilter(logging.Filter):
    def filter(self, logRecord: logging.LogRecord):
        return logRecord.levelno < logging.ERROR


def setup_project():
    # Check if PYTHON_RELEASES is outdated
    if f"{sys.version_info.major}.{sys.version_info.minor}" not in PYTHON_RELEASES:
        warnings.warn("You are using a Python version that the tool currently may not support")

    # Create missing directories
    TMP_DIR.mkdir(exist_ok=True)
    EXAMPLES_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)
    PLOTS_DIR.mkdir(exist_ok=True)

    # Setup logger, log normal logs and errors separately
    logger.setLevel(logging.INFO)

    normal_handler = logging.StreamHandler(sys.stdout)
    normal_handler.setLevel(logging.DEBUG)
    normal_handler.addFilter(NonErrorsFilter())
    logger.addHandler(normal_handler)

    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

    file_handler = logging.FileHandler(LOG_FILE)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def vermin_rules_per_python_version() -> dict[str, list[str]]:
    config = Config.vermin
    features_per_version = defaultdict(list)

    detections = (
        MOD_REQS(config), MOD_MEM_REQS(config), KWARGS_REQS(config),
        STRFTIME_REQS, BYTES_REQS, ARRAY_TYPECODE_REQS, CODECS_ERROR_HANDLERS, CODECS_ENCODINGS,
        {annotation: (None, (3, 9)) for annotation in
         (*BUILTIN_GENERIC_ANNOTATION_TYPES, *DICT_UNION_SUPPORTED_TYPES, *DICT_UNION_MERGE_SUPPORTED_TYPES)},
        DECORATOR_USER_FUNCTIONS
    )

    for detection_type in detections:
        for feature, (py2, py3) in detection_type.items():
            if py2:
                features_per_version['.'.join(map(str, py2))].append(feature)
            if py3:
                features_per_version['.'.join(map(str, py3))].append(feature)

    return features_per_version


def possible_versions(commit_date: datetime) -> set[tuple[int, int]]:
    return {version for version, v_date in PYTHON_RELEASES.items() if v_date <= commit_date}


def is_python_file(path: str) -> bool:
    return Path(path).suffix in {".py", ".py3", ".pyw", ".pyj", ".pyi"}
