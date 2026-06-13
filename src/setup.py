"""First-run setup for AutoDocker.

Creates ~/.autodocker/ and its default files if they do not exist.
Called automatically on every startup — safe to run repeatedly.
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

AUTODOCKER_DIR = Path.home() / ".autodocker"
IMAGES_FILE = AUTODOCKER_DIR / "images.json"
DEFAULT_REQS_FILE = AUTODOCKER_DIR / "default_requirements.txt"

_DEFAULT_REQS_CONTENT = """\
# AutoDocker default requirements
# These packages are pip-installed in every Python image that does not
# supply its own requirements.txt.
#
# Add one package per line, exactly as you would in a requirements.txt:
#   requests
#   httpx>=0.27
#   rich
"""


def ensure_autodocker_dir() -> None:
    """Create ~/.autodocker/ and its default files on first run.

    Safe to call on every startup — only writes files that are missing.
    """
    first_run = not AUTODOCKER_DIR.exists()

    AUTODOCKER_DIR.mkdir(parents=True, exist_ok=True)

    if not IMAGES_FILE.exists():
        IMAGES_FILE.write_text("{}\n", encoding="utf-8")

    if not DEFAULT_REQS_FILE.exists():
        DEFAULT_REQS_FILE.write_text(_DEFAULT_REQS_CONTENT, encoding="utf-8")

    if first_run:
        logger.info(
            "✓ Initialized AutoDocker at %s\n"
            "  Edit %s to set default pip packages.",
            AUTODOCKER_DIR,
            DEFAULT_REQS_FILE,
        )
