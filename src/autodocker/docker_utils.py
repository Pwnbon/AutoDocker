"""Docker interaction utilities for AutoDocker."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def check_docker_available() -> None:
    """Verify Docker is installed and the daemon is running.

    Raises:
        SystemExit: If Docker is not available or daemon is not running.
    """
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            raise FileNotFoundError
    except FileNotFoundError:
        logger.error("Docker is not installed or not found in PATH.")
        raise SystemExit(1)

    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode != 0:
            logger.error(
                "Docker daemon is not running. Please start Docker and try again."
            )
            raise SystemExit(1)
    except subprocess.TimeoutExpired:
        logger.error("Timed out waiting for Docker daemon response.")
        raise SystemExit(1)


def generate_dockerfile(repo_dir: Path) -> str:
    """Generate a Dockerfile string based on repository contents.

    Args:
        repo_dir: Path to the cloned repository directory.

    Returns:
        Dockerfile content as a string.
    """
    has_requirements = (repo_dir / "requirements.txt").exists()

    if has_requirements:
        return (
            "FROM python:3.12-slim\n\n"
            "WORKDIR /app\n\n"
            "COPY requirements.txt .\n\n"
            "RUN pip install --no-cache-dir -r requirements.txt\n\n"
            "COPY . .\n\n"
            'ENTRYPOINT ["python"]\n'
        )
    else:
        return (
            "FROM python:3.12-slim\n\n"
            "WORKDIR /app\n\n"
            "COPY . .\n\n"
            'ENTRYPOINT ["python"]\n'
        )


def build_docker_image(repo_dir: Path, image_name: str) -> None:
    """Build a Docker image from the given directory.

    Args:
        repo_dir: Path to directory containing Dockerfile and source.
        image_name: Tag to apply to the built image.

    Raises:
        SystemExit: If the Docker build fails.
    """
    dockerfile_path = repo_dir / "Dockerfile"
    dockerfile_content = generate_dockerfile(repo_dir)
    dockerfile_path.write_text(dockerfile_content, encoding="utf-8")
    logger.info("✓ Dockerfile generated")

    result = subprocess.run(
        ["docker", "build", "-t", image_name, str(repo_dir)],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("Docker build failed:\n%s", result.stderr)
        raise SystemExit(1)

    logger.info("✓ Docker image built")


def remove_docker_image(image_name: str) -> None:
    """Remove a Docker image by name.

    Args:
        image_name: Name/tag of the Docker image to remove.

    Raises:
        SystemExit: If the removal fails.
    """
    result = subprocess.run(
        ["docker", "rmi", image_name],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("Failed to remove image '%s':\n%s", image_name, result.stderr)
        raise SystemExit(1)
