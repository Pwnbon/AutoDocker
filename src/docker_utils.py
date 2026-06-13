"""Docker interaction utilities for AutoDocker."""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def check_docker_available() -> None:
    """Verify Docker is installed and the daemon is running."""
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


def generate_dockerfile(repo_dir: Path, language: str = "python") -> str:
    """Generate a Dockerfile string based on language and repository contents.

    Args:
        repo_dir: Path to the cloned repository directory.
        language: "python" or "go".

    Returns:
        Dockerfile content as a string.
    """
    if language == "go":
        return _generate_go_dockerfile(repo_dir)
    return _generate_python_dockerfile(repo_dir)


def _generate_python_dockerfile(repo_dir: Path) -> str:
    """Generate a Python Dockerfile.

    Always includes requirements.txt handling. If the repo does not have one,
    an empty file is created so the Dockerfile layer is consistent and the
    file can be populated later without code changes.
    """
    req_file = repo_dir / "requirements.txt"
    if not req_file.exists():
        default_reqs = Path.home() / ".autodocker" / "default_requirements.txt"
        content = default_reqs.read_text(encoding="utf-8") if default_reqs.exists() else ""
        req_file.write_text(content, encoding="utf-8")
        if content.strip():
            logger.info("✓ Applied default requirements")
        else:
            logger.info("✓ Created empty requirements.txt")

    return (
        "FROM python:3.12-slim\n\n"
        "WORKDIR /app\n\n"
        "COPY requirements.txt .\n\n"
        "RUN pip install --no-cache-dir -r requirements.txt\n\n"
        "COPY . .\n\n"
        'ENTRYPOINT ["python"]\n'
    )


def _generate_go_dockerfile(repo_dir: Path) -> str:
    """Generate a two-stage Go Dockerfile.

    Compiles in golang:1.22, produces a minimal alpine final image.
    """
    has_gosum = (repo_dir / "go.sum").exists()
    copy_deps = "COPY go.mod go.sum ./\n" if has_gosum else "COPY go.mod ./\n"

    return (
        "FROM golang:1.22 AS builder\n\n"
        "WORKDIR /app\n\n"
        + copy_deps
        + "\nRUN go mod download\n\n"
        "COPY . .\n\n"
        "RUN CGO_ENABLED=0 go build -o app .\n\n"
        "FROM alpine:latest\n\n"
        "WORKDIR /root/\n\n"
        "COPY --from=builder /app/app .\n\n"
        'ENTRYPOINT ["./app"]\n'
    )


def build_docker_image(repo_dir: Path, image_name: str, language: str = "python") -> None:
    """Build a Docker image from the given directory.

    Args:
        repo_dir: Path to directory containing source code.
        image_name: Tag to apply to the built image.
        language: "python" or "go" — controls Dockerfile generation.
    """
    dockerfile_path = repo_dir / "Dockerfile"
    dockerfile_content = generate_dockerfile(repo_dir, language)
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
    """Remove a Docker image by name."""
    result = subprocess.run(
        ["docker", "rmi", image_name],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        logger.error("Failed to remove image '%s':\n%s", image_name, result.stderr)
        raise SystemExit(1)