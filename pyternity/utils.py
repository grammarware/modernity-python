import logging
import sys
import time
from pathlib import Path
from typing import TypeAlias

import vermin

Features: TypeAlias = dict[tuple[int, int], dict[str, int]]

ROOT_DIR = Path(__file__).parent.parent
TMP_DIR = ROOT_DIR / "tmp"
EXAMPLES_DIR = ROOT_DIR / "examples"
RESULTS_DIR = ROOT_DIR / "results"

CLEAN_DOWNLOADS = False

logger = logging.getLogger('pyternity_logger')

VERMIN_CONFIG = vermin.Config.parse_file(vermin.Config.detect_config_file())


def measure_time(func):
    def func_timer(*args, **kwargs):
        start = time.perf_counter()
        res = func(*args, **kwargs)
        end = time.perf_counter()
        logger.info(f"TIMER {func.__name__} took {end - start:.3f}s")
        return res

    return func_timer


def parse_vermin_version(version: str) -> tuple[int, int] | None:
    if target := vermin.utility.parse_target(version):
        return target[1]


class NonErrorsFilter(logging.Filter):
    def filter(self, logRecord: logging.LogRecord):
        return logRecord.levelno < logging.ERROR


def setup_project():
    # Create missing directories
    TMP_DIR.mkdir(exist_ok=True)
    EXAMPLES_DIR.mkdir(exist_ok=True)
    RESULTS_DIR.mkdir(exist_ok=True)

    # Setup logger, log normal logs and errors separately
    logger.setLevel(logging.DEBUG)

    normal_handler = logging.StreamHandler(sys.stdout)
    normal_handler.setLevel(logging.DEBUG)
    normal_handler.addFilter(NonErrorsFilter())
    logger.addHandler(normal_handler)

    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

    logger.debug(f"{VERMIN_CONFIG=}")
