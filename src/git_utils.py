"""Git repository utilities for AutoDocker."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

VALID_SCHEMES = ("https://", "http://", "git@", "git://")


def validate_github_url(url: str) -> None:
    """Validate that the given URL looks like a GitHub repository URL.

    Args:
        url: The URL string to validate.

    Raises:
        SystemExit: If the URL is not a valid GitHub repository URL.
    """
    if not any(url.startswith(scheme) for scheme in VALID_SCHEMES):
        logger.error(
            "Invalid URL '%s'. Must start with https://, http://, git@, or git://",
            url,
        )
        raise SystemExit(1)

    lowered = url.lower()
    if "github.com" not in lowered and "gitlab.com" not in lowered and "bitbucket" not in lowered:
        logger.warning(
            "URL '%s' does not appear to be a GitHub/GitLab/Bitbucket URL. Proceeding anyway.",
            url,
        )


def clone_repository(url: str, dest: Path) -> None:
    """Clone a git repository into the destination directory.

    Args:
        url: Git repository URL to clone.
        dest: Local path to clone into.

    Raises:
        SystemExit: If cloning fails.
    """
    result = subprocess.run(
        ["git", "clone", "--depth", "1", url, str(dest)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("Failed to clone repository '%s':\n%s", url, result.stderr)
        raise SystemExit(1)

    logger.info("✓ Repository cloned")


def repo_name_from_url(url: str) -> str:
    """Extract the repository name from a git URL.

    Args:
        url: Git repository URL.

    Returns:
        Repository name without .git suffix.
    """
    # Strip trailing slashes and .git suffix
    stripped = url.rstrip("/")
    if stripped.endswith(".git"):
        stripped = stripped[:-4]
    return stripped.split("/")[-1]
