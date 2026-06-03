"""Metadata storage for AutoDocker-managed images."""

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

METADATA_DIR = Path.home() / ".autodocker"
METADATA_FILE = METADATA_DIR / "images.json"


def _load_metadata() -> dict[str, Any]:
    """Load metadata from disk.

    Returns:
        Dictionary of image metadata, keyed by image name.
    """
    if not METADATA_FILE.exists():
        return {}
    try:
        return json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not read metadata file: %s", exc)
        return {}


def _save_metadata(data: dict[str, Any]) -> None:
    """Persist metadata to disk.

    Args:
        data: Metadata dictionary to save.
    """
    METADATA_DIR.mkdir(parents=True, exist_ok=True)
    METADATA_FILE.write_text(
        json.dumps(data, indent=2), encoding="utf-8"
    )


def save_image_metadata(image_name: str, url: str) -> None:
    """Store metadata for a newly built image.

    Args:
        image_name: Name/tag of the Docker image.
        url: Source repository URL.
    """
    data = _load_metadata()
    data[image_name] = {
        "url": url,
        "build_date": date.today().isoformat(),
    }
    _save_metadata(data)


def delete_image_metadata(image_name: str) -> None:
    """Remove metadata entry for an image.

    Args:
        image_name: Name/tag of the Docker image to remove.
    """
    data = _load_metadata()
    if image_name in data:
        del data[image_name]
        _save_metadata(data)


def get_all_images() -> dict[str, Any]:
    """Return all tracked image metadata.

    Returns:
        Dictionary of all image metadata.
    """
    return _load_metadata()


def get_image_info(image_name: str) -> dict[str, Any] | None:
    """Return metadata for a specific image.

    Args:
        image_name: Name/tag of the Docker image.

    Returns:
        Metadata dict or None if not found.
    """
    return _load_metadata().get(image_name)


def is_managed_image(image_name: str) -> bool:
    """Check whether an image is tracked by AutoDocker.

    Args:
        image_name: Name/tag of the Docker image.

    Returns:
        True if the image exists in metadata, False otherwise.
    """
    return image_name in _load_metadata()
