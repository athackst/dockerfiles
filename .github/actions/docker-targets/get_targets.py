#!/usr/bin/env python3
"""Emit a matrix of non-EOL docker targets from templates.yml."""

from __future__ import annotations

import argparse
from pathlib import Path
from actions_toolkit import core
from ruamel import yaml


def load_templates(path: Path) -> dict:
    loader = yaml.YAML()
    with path.open("r", encoding="utf-8") as fh:
        return loader.load(fh) or {}


def parse_platform(raw: str) -> tuple[str, str, str | None]:
    raw = (raw or "").strip().lower().replace("-", "/")
    parts = [p for p in raw.split("/") if p]
    if len(parts) == 1:
        return "linux", parts[0], None
    if len(parts) == 2:
        return parts[0], parts[1], None
    return parts[0], parts[1], "/".join(parts[2:])


def canonical_platform(raw: str) -> str:
    os_name, arch, variant = parse_platform(raw)
    return f"{os_name}/{arch}" + (f"/{variant}" if variant else "")


def platforms_support(platforms_csv: str, want: str) -> bool:
    want_os, want_arch, want_var = parse_platform(want)
    for raw in (platforms_csv or "").split(","):
        p_os, p_arch, p_var = parse_platform(raw.strip())
        if (p_os, p_arch) != (want_os, want_arch):
            continue
        if p_var is None:
            return True
        if want_var == p_var:
            return True
    return False


def entry_supports_platform(entry: dict, platform: str) -> bool:
    if not platform:
        return True
    platform = canonical_platform(platform)
    for target in entry.get("targets") or []:
        if platforms_support(target.get("platforms", ""), platform):
            return True
    return False


def collect_non_eol(data: dict, platform: str | None = None) -> list[dict]:
    platform = platform or ""
    include: list[dict] = []
    for family, entries in (data or {}).items():
        for entry in entries or []:
            if not entry or entry.get("eol"):
                continue
            name = entry.get("name")
            if not name:
                continue
            if platform and not entry_supports_platform(entry, platform):
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
    data = load_templates(Path(args.templates))
    changed = parse_changed(args.changed)
    all = args.all.lower() == "true"
    include: list[dict[str, str]] = []
    stage_details: list[dict[str, str]] = []
    want_platform = canonical_platform(args.platform) if args.platform else ""
    for item in collect_non_eol(data, args.platform or None):
        if (
            not all
            and changed
            and (item["family"], item["distro"]) not in changed
        ):
            continue
        include.append(item)
        entries = data.get(item["family"], []) or []
        entry = next(
            (e for e in entries if e and e.get("name") == item["distro"]), None
        )
        if not entry:
            continue
        for target in entry.get("targets") or []:
            stage = target.get("target")
            if not stage:
                continue
            platforms = target.get("platforms", "")
            if want_platform and not platforms_support(platforms, want_platform):
                continue
            stage_details.append(
                {
                    "family": item["family"],
                    "distro": item["distro"],
                    "stage": stage,
                    "platforms": platforms,
                }
            )
    families = sorted({item["family"] for item in include})
    core.set_output("distros", include)
    core.set_output("families", families)
    core.set_output("stages", stage_details)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
