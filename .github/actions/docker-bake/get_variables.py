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
    --ghcr-username <user> \
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
from typing import Optional, Tuple

from actions_toolkit import core
from ruamel import yaml


def parse_platform(p: str) -> Tuple[str, str, Optional[str]]:
    """Parses a Docker platform string into components.

    Args:
      p: Platform string in the form "os/arch[/variant]". "-" is accepted
        as a separator for convenience (e.g., "linux-arm-v7").

    Returns:
      A tuple (os, arch, variant_or_none). If only an arch is provided,
      defaults os to "linux".
    """
    p = (p or "").strip().lower().replace("-", "/")
    parts = [x for x in p.split("/") if x]
    if len(parts) == 1:
        return "linux", parts[0], None
    if len(parts) == 2:
        return parts[0], parts[1], None
    return parts[0], parts[1], "/".join(parts[2:])


def canonical_platform(p: str) -> str:
    """Normalizes a platform string to slash form.

    Args:
      p: Platform string (any of "amd64", "linux/amd64", "linux-arm-v7", etc.).

    Returns:
      Canonical platform in slash form "os/arch[/variant]".
    """
    os_, arch, var = parse_platform(p)
    return f"{os_}/{arch}" + (f"/{var}" if var else "")


def norm_platform(p: str) -> str:
    """Converts a platform string to a dashed key safe for tags/scopes.

    Args:
      p: Platform string.

    Returns:
      Dashed form, e.g., "linux-arm-v7".
    """
    os_, arch, var = parse_platform(p)
    return f"{os_}-{arch}" + (f"-{var}" if var else "")


def load_templates() -> dict:
    """Loads templates.yml from repo root.

    Returns:
      Parsed YAML as a dict. Empty dict if file is empty.
    """
    y = yaml.YAML()
    with open("templates.yml", "r", encoding="utf-8") as f:
        return y.load(f) or {}


def platforms_support(allowed_csv: str, want: str) -> bool:
    """Checks if a wanted platform matches an allowed platforms list.

    Matching rule:
      - os and arch must match exactly;
      - if the allowed entry has no variant,
            it matches any variant of that os/arch;
      - if the allowed entry has a variant, it must match exactly.

    Args:
      allowed_csv: Comma-delimited list of platforms from templates.yml.
      want: Canonical wanted platform (slash form), possibly with variant.

    Returns:
      True if any allowed entry matches the wanted platform.
    """
    want_os, want_arch, want_var = parse_platform(want)
    for raw in (allowed_csv or "").split(","):
        a_os, a_arch, a_var = parse_platform(raw.strip())
        if (a_os, a_arch) != (want_os, want_arch):
            continue
        if a_var is None:
            return True  # wildcard variant
        if want_var == a_var:
            return True
    return False


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
        "--ghcr-username", default="", help="GHCR owner/org for final tags."
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

    data = load_templates()
    entries = data.get(args.family, [])
    entry = next(
        (
            e
            for e in entries
            if e.get("name") == args.distro and not e.get("eol", False)
        ),
        None,
    )
    if entry is None:
        core.set_failed(
            f"No entry '{args.distro}' under '{args.family}'"
            f" in templates.yml (or it's EOL)"
        )
        return 1

    stages: list[str] = []
    stage_targets: list[str] = []
    set_lines: list[str] = []
    for tgt in entry.get("targets", []):
        if not platforms_support(tgt.get("platforms", ""), platform):
            continue
        stage = tgt.get("target")
        stages.append(stage)
        tname = f"{release}-{stage}"
        stage_targets.append(tname)

        destinations: list[str] = []
        if args.ghcr_username:
            destinations.append(f"ghcr.io/{args.ghcr_username}/{args.family}")
        if args.docker_username:
            destinations.append(f"docker.io/{args.docker_username}/{args.family}")

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
