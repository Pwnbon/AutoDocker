"""CLI command implementations for AutoDocker."""

import logging
import shutil
import tempfile
from pathlib import Path

from .docker_utils import (
    build_docker_image,
    check_docker_available,
    remove_docker_image,
)
from .git_utils import (
    clone_repository,
    detect_language,
    repo_name_from_url,
    validate_github_url,
)
from .metadata import (
    delete_image_metadata,
    get_all_images,
    get_image_info,
    is_managed_image,
    save_image_metadata,
)
from .naming import generate_image_name

logger = logging.getLogger(__name__)


def cmd_build(url: str, custom_name: str | None = None) -> None:
    """Build a Docker image from a GitHub repository.

    Args:
        url: GitHub repository URL to clone and build.
        custom_name: Optional custom image name. Auto-generated if not provided.
    """
    validate_github_url(url)
    check_docker_available()

    repo_name = repo_name_from_url(url)
    image_name = custom_name if custom_name else generate_image_name(url, repo_name)

    tmp_dir = Path(tempfile.mkdtemp(prefix="autodocker_"))
    clone_dest = tmp_dir / repo_name

    try:
        clone_repository(url, clone_dest)

        language = detect_language(clone_dest)
        logger.info("✓ Language detected: %s", language)

        build_docker_image(clone_dest, image_name, language)
        logger.info("✓ Temporary files removed")
    except SystemExit:
        raise
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    save_image_metadata(image_name, url, language)

    print(f"\nBuild successful\n")
    print(f"Image Name : {image_name}")
    print(f"Language   : {language}\n")
    print("Run examples:\n")

    if language == "go":
        print(f"  docker run --rm {image_name} --help")
        print(f"  docker run --rm {image_name} subcommand --flag value\n")
    else:
        print(f"  docker run --rm {image_name} script.py --help")
        print(f"  docker run --rm {image_name} script.py -arg1 value1\n")


def cmd_list() -> None:
    """List all AutoDocker-managed images."""
    images = get_all_images()

    if not images:
        print("No AutoDocker-managed images found.")
        return

    print(f"{'IMAGE NAME':<35} {'LANG':<8} {'BUILD DATE':<12}  URL")
    print("-" * 95)
    for name, meta in images.items():
        build_date = meta.get("build_date", "unknown")
        repo_url = meta.get("url", "unknown")
        lang = meta.get("language", "unknown")
        print(f"{name:<35} {lang:<8} {build_date:<12}  {repo_url}")


def cmd_remove(image_name: str) -> None:
    """Remove an AutoDocker-managed Docker image."""
    if not is_managed_image(image_name):
        logger.warning(
            "Image '%s' is not tracked by AutoDocker. Attempting removal anyway.",
            image_name,
        )

    check_docker_available()
    remove_docker_image(image_name)
    delete_image_metadata(image_name)
    print(f"✓ Image '{image_name}' removed successfully.")


def cmd_info(image_name: str) -> None:
    """Display metadata for an AutoDocker-managed image."""
    info = get_image_info(image_name)

    if info is None:
        logger.error("No AutoDocker metadata found for image '%s'.", image_name)
        raise SystemExit(1)

    print(f"\nImage Name : {image_name}")
    print(f"Language   : {info.get('language', 'unknown')}")
    print(f"Repository : {info.get('url', 'unknown')}")
    print(f"Build Date : {info.get('build_date', 'unknown')}\n")


def cmd_run(image_name: str, script_args: list[str]) -> None:
    """Run a script or command inside an AutoDocker-managed image.

    For Python images: docker run --rm <image> <script.py> [args...]
    For Go images:     docker run --rm <image> [args...]
    """
    import subprocess

    if not script_args:
        logger.error(
            "No script or arguments specified.\n"
            "  Python: autodocker run <image> <script.py> [args...]\n"
            "  Go:     autodocker run <image> [args...]"
        )
        raise SystemExit(1)

    check_docker_available()
    cmd = ["docker", "run", "--rm", image_name] + script_args
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)