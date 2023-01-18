from collections import defaultdict
from datetime import date

from vermin import MOD_REQS, MOD_MEM_REQS, KWARGS_REQS, STRFTIME_REQS, BYTES_REQS, ARRAY_TYPECODE_REQS, \
    CODECS_ERROR_HANDLERS, CODECS_ENCODINGS, BUILTIN_GENERIC_ANNOTATION_TYPES, DICT_UNION_SUPPORTED_TYPES, \
    DICT_UNION_MERGE_SUPPORTED_TYPES, DECORATOR_USER_FUNCTIONS

from pyternity.utils import Config

PYTHON_RELEASES = {version: date.fromisoformat(d) for version, d in {
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


def possible_versions(commit_date: date) -> set[tuple[int, int]]:
    return {version for version, v_date in PYTHON_RELEASES.items() if v_date <= commit_date}
