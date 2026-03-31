#!/usr/bin/env python3
"""Emit a matrix of non-EOL docker targets from templates.yml."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from actions_toolkit import core

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dockerfiles_templates import (  # noqa: E402
    Templates,
    canonical_platform,
)


def collect_non_eol(
    templates: Templates, platform: str | None = None
) -> list[dict]:
    platform = platform or ""
    include: list[dict] = []
    for entry in templates.entries(eol=False, platform=platform or None):
        name = entry.get("name")
        family = entry.get("family")
        if not name or not family:
            continue
        include.append({"family": family, "distro": name})
    return include


def parse_changed(raw: str) -> set[tuple[str, str]]:
    changed: set[tuple[str, str]] = set()
    tokens = [
        token.strip()
        for part in raw.splitlines()
        for token in part.split(",")
        if token.strip()
    ]
    for token in tokens:
        path = Path(token)
        if path.suffix != ".Dockerfile":
            continue
        parts = path.parts
        if len(parts) < 2:
            continue
        family = parts[-2]
        distro = path.stem
        changed.add((family, distro))
    return changed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate matrix JSON for non-EOL templates."
    )
    parser.add_argument(
        "--templates",
        default="templates.yml",
        help="Path to the templates.yml file.",
    )
    parser.add_argument(
        "--platform",
        default="",
        help="Optional platform filter (e.g., linux/amd64).",
    )
    parser.add_argument(
        "--changed",
        default="",
        help="Comma/newline separated list of changed Dockerfile paths.",
    )
    parser.add_argument(
        "--all",
        default="false",
        help="return all values regardless of change status.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        templates = Templates(templates_path=Path(args.templates))
    except ValueError as exc:
        core.set_failed(str(exc))
        return 1
    changed = parse_changed(args.changed)
    all = args.all.lower() == "true"
    include: list[dict[str, str]] = []
    stage_details: list[dict[str, str]] = []
    want_platform = canonical_platform(args.platform) if args.platform else ""
    for item in collect_non_eol(templates, args.platform or None):
        if (not all and not changed) or (
            not all and (item["family"], item["distro"]) not in changed
        ):
            continue
        include.append(item)
        entry = templates.get_entry(item["family"], item["distro"], eol=False)
        if not entry:
            continue
        for target in templates.targets_for_platform(entry, want_platform):
            stage = target.get("target")
            if not stage:
                continue
            platforms = target.get("platforms", [])
            stage_details.append(
                {
                    "family": item["family"],
                    "distro": item["distro"],
                    "stage": stage,
                    "platforms": ",".join(platforms),
                }
            )
    families = sorted({item["family"] for item in include})
    core.set_output("distros", include)
    core.set_output("families", families)
    core.set_output("stages", stage_details)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
