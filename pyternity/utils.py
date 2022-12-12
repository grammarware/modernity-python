import logging
import sys
from pathlib import Path
from typing import TypeAlias

import vermin

ModernitySignature: TypeAlias = dict[tuple[int, int], float]

ROOT_DIR = Path(__file__).parent.parent
TMP_DIR = ROOT_DIR / "tmp"
EXAMPLES_DIR = ROOT_DIR / "examples"

CLEAN_DOWNLOADS = False

logger = logging.getLogger('pyternity_logger')

VERMIN_CONFIG = vermin.Config.parse_file(vermin.Config.detect_config_file())


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

    # Setup logger
    logger.setLevel(logging.DEBUG)

    normal_handler = logging.StreamHandler(sys.stdout)
    normal_handler.setLevel(logging.DEBUG)
    normal_handler.addFilter(NonErrorsFilter())
    logger.addHandler(normal_handler)

    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setLevel(logging.ERROR)
    logger.addHandler(error_handler)

    logger.debug(f"{VERMIN_CONFIG=}")
