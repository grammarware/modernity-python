import logging
import sys
from pathlib import Path
from typing import TypeAlias

ModernitySignature: TypeAlias = dict[tuple[int, int], float]

ROOT_DIR = Path(__file__).parent.parent
TMP_DIR = ROOT_DIR / "tmp"
TMP_DIR.mkdir(exist_ok=True)

EXAMPLES_DIR = ROOT_DIR / "examples"
EXAMPLES_DIR.mkdir(exist_ok=True)

# Setup logger
logger = logging.getLogger('pyternity_logger')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler(sys.stdout))
error_handler = logging.StreamHandler(sys.stderr)
error_handler.setLevel(logging.ERROR)
logger.addHandler(error_handler)
