#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Emit Bake variables and tag overrides from templates.yml.

This  accepts any Docker platform triple ``os/arch[/variant]``
(e.g., ``linux/amd64``), passes it through to Bake, and generates per-stage
tag override lines.

Example:
  get_variables.py \
    --family ros2 \
    --distro rolling \
    --platform linux/amd64 \
    --ghcr-owner <owner> \
    --docker-username <user> \
    --digest

GitHub Actions outputs (via actions_toolkit.core.set_output):
  platform:       Canonical slash form for Bake (e.g., "linux/arm/v7").
  platform_key:   Dashed form for names/scopes (e.g., "linux-arm-v7").
  platform_group: Platform-only key (e.g., "linux-amd64").
  group:          Release-platform group name (e.g., "ros2-rolling-linux-amd64").
  release:        Parent name (e.g. "ros2-rolling").
  stages:         JSON array of stage ids (["base", "dev", ...]).
  stage_targets:  JSON array of full target names (["ros2-rolling-base", ...]).
  set_lines:      Newline-joined Bake `--set` directives for outputs.
"""  # noqa:E501

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from actions_toolkit import core

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dockerfiles_templates import (  # noqa: E402
    Templates,
    canonical_platform,
    parse_platform,
)


def norm_platform(p: str) -> str:
    """Converts a platform string to a dashed key safe for tags/scopes.

    Args:
      p: Platform string.

    Returns:
      Dashed form, e.g., "linux-arm-v7".
    """
    os_, arch, var = parse_platform(p)
    return f"{os_}-{arch}" + (f"-{var}" if var else "")


def main() -> int:
    """Entry point."""
    parser = argparse.ArgumentParser(
        description="Generate Bake variables and set-lines from templates.yml"
    )
    parser.add_argument(
        "--family",
        required=True,
        help="Program/family (e.g., ros2).",
    )
    parser.add_argument(
        "--distro",
        required=True,
        help="Distro/release (e.g., rolling).",
    )
    parser.add_argument(
        "--platform",
        required=True,
        help="Docker platform os/arch[/variant] (e.g., linux/amd64).",
    )
    parser.add_argument(
        "--ghcr-owner",
        dest="ghcr_owner",
        default="",
        help="GHCR owner/org for final tags.",
    )
    parser.add_argument(
        "--ghcr-username",
        dest="ghcr_owner",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--docker-username",
        default="",
        help="Docker Hub user/org for final tags.",
    )
    parser.add_argument(
        "--digest",
        action="store_true",
        help="Emit Bake --set lines that push-by-digest for each stage.",
    )
    args = parser.parse_args()

    platform = canonical_platform(args.platform)  # e.g., "linux/arm/v7"
    pkey = norm_platform(args.platform)  # e.g., "linux-arm-v7"

    # Group by parent platform (os/arch) so one group covers all variants.
    os_, arch, _ = parse_platform(args.platform)
    # e.g., "linux-arm", "linux-amd64", "windows-amd64"
    release = f"{args.family}-{args.distro}"
    platform_group = f"{os_}-{arch}"
    release_group = f"{release}-{platform_group}"

    try:
        templates = Templates(templates_path="templates.yml")
    except ValueError as exc:
        core.set_failed(str(exc))
        return 1
    entry = templates.get_entry(args.family, args.distro, eol=False)
    if entry is None:
        core.set_failed(
            f"No entry '{args.distro}' under '{args.family}'"
            f" in templates.yml (or it's EOL)"
        )
        return 1

    stages: list[str] = []
    stage_targets: list[str] = []
    set_lines: list[str] = []
    normalized_family = args.family.strip().lower()
    normalized_ghcr_owner = args.ghcr_owner.strip().lower()
    normalized_docker_user = args.docker_username.strip().lower()
    for tgt in templates.targets_for_platform(entry, platform):
        stage = tgt.get("target")
        stages.append(stage)
        tname = f"{release}-{stage}"
        stage_targets.append(tname)

        destinations: list[str] = []
        if normalized_ghcr_owner:
            destinations.append(
                f"ghcr.io/{normalized_ghcr_owner}/{normalized_family}"
            )
        if normalized_docker_user:
            destinations.append(
                f"docker.io/{normalized_docker_user}/{normalized_family}"
            )

        if args.digest:
            set_lines.append(f"{tname}.tags=")
            for destination in destinations:
                set_lines.append(
                    f"{tname}.output=type=registry,name={destination},push-by-digest=true"  # noqa:
                )

    if not stages:
        core.warning(
            f"No build targets in templates.yml for {release} on platform {platform}"
        )
        core.set_output("exists", False)
        return 0

    # Emit GitHub Action outputs.
    core.set_output("platform", platform)  # exact value to give Bake
    core.set_output("platform_key", pkey)  # dashed for scopes/tags
    core.set_output("platform_group", platform_group)
    core.set_output("release", release)  # release name
    core.set_output("group", release_group)  # release-platform group name
    core.set_output("stages", json.dumps(stages))
    core.set_output("stage_targets", json.dumps(stage_targets))
    core.set_output("set_lines", "\n".join(set_lines))

    core.info(
        f"Release: {release} | Group: {release_group} | Platform: {platform} "
        f"| Stages: {','.join(stages)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
