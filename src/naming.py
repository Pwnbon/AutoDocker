"""Image naming utilities for AutoDocker."""

import hashlib


def generate_image_name(repo_url: str, repo_name: str) -> str:
    """Generate an automatic image name from a repository URL.

    The name format is: ``<repo-name>-<6-character-hash>``

    Args:
        repo_url: Full repository URL used to derive the hash.
        repo_name: Short name of the repository.

    Returns:
        Generated image name string.
    """
    url_hash = hashlib.sha256(repo_url.encode()).hexdigest()[:6]
    safe_name = _sanitize_name(repo_name)
    return f"{safe_name}-{url_hash}"


def _sanitize_name(name: str) -> str:
    """Sanitize a string for use as a Docker image name.

    Converts to lowercase and replaces non-alphanumeric characters
    (except hyphens) with hyphens.

    Args:
        name: Raw name string.

    Returns:
        Sanitized name safe for Docker image tags.
    """
    sanitized = "".join(
        c if c.isalnum() or c == "-" else "-" for c in name.lower()
    )
    # Collapse multiple consecutive hyphens
    while "--" in sanitized:
        sanitized = sanitized.replace("--", "-")
    return sanitized.strip("-")
