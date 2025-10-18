#!/usr/bin/env python3
"""Local script for building templates via docker buildx bake."""

from __future__ import annotations

import logging
import os
import subprocess
from datetime import date
from pathlib import Path
from typing import Iterable

import click

from generate import generate_dockerfiles as gen
from generate import templates

""" md
# Build (`build.py`)

`build.py` wraps `docker buildx bake` so you can regenerate Dockerfiles and build
(or push) the generated targets from your workstation.

## Usage
```bash
# Regenerate Dockerfiles, build all targets locally
python build.py all

# Build a single image + target stage and push to the registry
python build.py --push rolling --target base
```

### Options
- `--no-generate`: Skip the file generation step.
- `--push`: Push results to `${DOCKER_REGISTRY:-althack}` (or set `DOCKER_PUSH=true`).
- `--target <stage>`: Limit to a single Dockerfile stage.
- `--no-clean`: Skip the final `docker system prune -f` (or set `DOCKER_CLEAN=false`).

The script always reads from the generated `docker-bake.hcl`, updating tags like
`registry/repo:image-stage` and `registry/repo:image-stage-YYYY-MM-DD` when pushing.

"""

TODAY = date.today()
DEFAULT_REGISTRY = "althack"
DOCKER_BAKE_FILE = Path(__file__).resolve().parent / "docker-bake.hcl"

log = logging.getLogger(__name__)


def _get_bool(value: str | None) -> bool:
    """Return True when an environment value should be considered enabled."""
    if value is None:
        return False
    return value.lower() not in {"0", "false", "no", "off", ""}


def should_push() -> bool:
    """Return True when pushes should occur based on env/config."""
    return _get_bool(os.getenv("DOCKER_PUSH"))


def should_clean() -> bool:
    """Return True when a post-build prune is requested."""
    return _get_bool(os.getenv("DOCKER_CLEAN"))


class DockerBake:
    """Thin wrapper around ``docker buildx bake`` invocations."""

    def __init__(self, registry: str | None = None) -> None:
        """Initialize the wrapper with a registry override.

        Args:
            registry: Optional registry root; falls back to env/constant.
        """
        self.registry = registry or os.getenv(
            "DOCKER_REGISTRY", DEFAULT_REGISTRY
        )
        self.bake_file = str(DOCKER_BAKE_FILE)

    def bake(
        self,
        target: str,
        *,
        push: bool,
        tags: Iterable[str] | None = None,
    ) -> None:
        """Execute a bake target with optional push settings.

        Args:
            target: Bake target name (e.g. ``ros2-rolling-base``).
            push: Whether to push instead of loading locally.
            tags: Additional tags to apply when pushing.
        """
        cmd: list[str] = [
            "docker",
            "buildx",
            "bake",
            "--file",
            self.bake_file,
            "--debug",
        ]

        cmd.append("--push" if push else "--load")

        if push and tags:
            tag_list = ",".join(tags)
            cmd.extend(["--set", f"{target}.tags={tag_list}"])

        cmd.append(target)
        log.debug("Running: %s", " ".join(cmd))
        ret = os.system(" ".join(cmd))
        if ret != 0:
            raise Exception("Error in docker bake")

    @staticmethod
    def prune() -> None:
        """Prune dangling Docker resources."""
        subprocess.run(["docker", "system", "prune", "-f"], check=True)


def build(image: str, target: str, push: bool, clean: bool) -> None:
    """Build selected templates with docker bake.

    Args:
        image: Template key or ``all`` for every template.
        target: Optional specific stage to build.
        push: Whether to push artifacts to the registry.
        clean: Whether to prune Docker after completion.
    """
    builds = templates.images(eol=True)
    if image != "all":
        builds = {image: templates.images()[image]}

    baker = DockerBake()
    push_requested = push or should_push()

    for name, definition in builds.items():
        repo = definition["repository"]
        stages = definition["targets"] if not target else [target]
        print(f"***Found Stages: {stages}")
        for current_stage in stages:
            bake_target = f"{repo}-{name}-{current_stage}"
            base_tag = f"{baker.registry}/{repo}:{name}-{current_stage}"
            log.info(
                "Building %s (target=%s push=%s)",
                base_tag,
                bake_target,
                push_requested,
            )
            extra_tags = None
            if push_requested:
                extra_tags = [base_tag, f"{base_tag}-{TODAY}"]
            baker.bake(bake_target, push=push_requested, tags=extra_tags)

    if not builds:
        raise Exception(f"No builds found for {image}")

    if clean or should_clean():
        baker.prune()


@click.command()
@click.option(
    "--generate/--no-generate",
    default=True,
    help="Generate docker files first.",
)
@click.option(
    "--push/--no-push",
    default=False,
    help="Push generated images to the configured registry.",
)
@click.option(
    "--clean/--no-clean",
    default=True,
    help="Run `docker system prune -f` after the build.",
)
@click.option(
    "--target", default="", help="Limit to a specific Dockerfile target."
)
@click.argument("image", type=click.Choice(list(templates.images()) + ["all"]))
def main(
    generate: bool, push: bool, clean: bool, image: str, target: str
) -> None:
    """CLI entry point dispatching generate + build routines."""
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setLevel(logging.DEBUG)
    log.addHandler(handler)

    if generate:
        gen(log)

    build(image, target, push, clean)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
