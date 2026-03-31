#!/usr/bin/env python3
"""Local script for building templates via docker buildx bake."""

from __future__ import annotations

import logging
import os
import subprocess
import json
import re
from datetime import date
from pathlib import Path
from typing import Iterable

import click

""" md
# Build (`build.py`)

`build.py` wraps `docker buildx bake` to build
(or push) the generated targets from your workstation.

## Usage
```bash
# Build all active targets (bake default group)
python build.py all

# Build a single bake target
python build.py ros2-rolling-base

# Build a bake group (for example, one distro group)
python build.py ros2-jazzy
```

### Options
- `--push`: Push results to `${DOCKER_REGISTRY:-althack}` (or set `DOCKER_PUSH=true`).
- `--no-clean`: Skip the final `docker system prune -f` (or set `DOCKER_CLEAN=false`).

The script always reads from the generated `docker-bake.hcl`, updating tags like
`registry/repo:image-stage` and `registry/repo:image-stage-YYYY-MM-DD` when pushing.

"""

TODAY = date.today()
DEFAULT_REGISTRY = "althack"
DOCKER_BAKE_FILE = Path(__file__).resolve().parent / "docker-bake.hcl"

log = logging.getLogger(__name__)


def _bake_selector_completion(
    ctx: click.Context, param: click.Parameter, incomplete: str
) -> list[click.shell_completion.CompletionItem]:
    """Return shell completion candidates for bake selectors."""
    del ctx, param
    values = {"all"}
    if DOCKER_BAKE_FILE.exists():
        text = DOCKER_BAKE_FILE.read_text(encoding="utf-8")
        for match in re.findall(r'^(?:target|group)\s+"([^"]+)"', text, re.M):
            values.add(match)
    return [
        click.shell_completion.CompletionItem(value)
        for value in sorted(values)
        if value.startswith(incomplete)
    ]


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
        subprocess.run(cmd, check=True)

    def resolve_targets(self, ref: str) -> list[str]:
        """Resolve a bake target/group selector to concrete targets."""
        cmd = [
            "docker",
            "buildx",
            "bake",
            "--file",
            self.bake_file,
            "--print",
            ref,
        ]
        log.debug("Resolving targets with: %s", " ".join(cmd))
        output = subprocess.check_output(cmd, text=True)
        payload = json.loads(output)
        targets = list((payload.get("target") or {}).keys())
        targets.sort()
        return targets

    def has_target(self, target: str) -> bool:
        """Return True when the target exists in docker-bake.hcl."""
        with open(self.bake_file, "r", encoding="utf-8") as file:
            content = file.read()
        return f'target "{target}"' in content

    def has_group(self, group: str) -> bool:
        """Return True when the group exists in docker-bake.hcl."""
        with open(self.bake_file, "r", encoding="utf-8") as file:
            content = file.read()
        return f'group "{group}"' in content

    def has_ref(self, ref: str) -> bool:
        """Return True when a bake ref exists as either target or group."""
        return self.has_target(ref) or self.has_group(ref)

    @staticmethod
    def prune() -> None:
        """Prune dangling Docker resources."""
        subprocess.run(["docker", "system", "prune", "-f"], check=True)


def parse_bake_target(target: str) -> tuple[str, str, str]:
    """Parse ``family-name-stage`` bake target into parts."""
    family, separator, rest = target.partition("-")
    name, separator2, stage = rest.rpartition("-")
    if not separator or not separator2 or not family or not name or not stage:
        raise ValueError(f"Invalid bake target '{target}'")
    return family, name, stage


def build(selection: str, push: bool, clean: bool) -> None:
    """Build a bake target/group, or ``all`` (mapped to ``default`` group)."""
    baker = DockerBake()
    bake_ref = "default" if selection == "all" else selection
    if not baker.has_ref(bake_ref):
        raise Exception(
            f"Bake target/group '{bake_ref}' was not found in docker-bake.hcl. "
            "Run './generate.py' to refresh bake targets."
        )

    push_requested = push or should_push()
    if push_requested:
        targets = baker.resolve_targets(bake_ref)
        if not targets:
            raise Exception(f"No concrete bake targets resolved for '{bake_ref}'.")
        for target in targets:
            family, name, stage = parse_bake_target(target)
            base_tag = f"{baker.registry}/{family}:{name}-{stage}"
            extra_tags = [base_tag, f"{base_tag}-{TODAY}"]
            log.info(
                "Building %s (target=%s push=%s)",
                base_tag,
                target,
                push_requested,
            )
            baker.bake(target, push=True, tags=extra_tags)
    else:
        log.info("Building %s (push=%s)", bake_ref, push_requested)
        baker.bake(bake_ref, push=False)

    if clean or should_clean():
        baker.prune()


@click.command()
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
@click.argument("selector", shell_complete=_bake_selector_completion)
def main(
    push: bool,
    clean: bool,
    selector: str,
) -> None:
    """CLI entry point dispatching generate + build routines."""
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    handler.setLevel(logging.DEBUG)
    log.addHandler(handler)

    build(selector, push, clean)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
