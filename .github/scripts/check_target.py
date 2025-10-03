#!/usr/bin/env python3
from __future__ import annotations
import argparse
from typing import Any, Dict, List

from ruamel.yaml import YAML
from actions_toolkit import core


def load_yaml(path: str) -> Dict[str, Any]:
    yaml = YAML(typ="safe")
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f)
    return data or {}


def find_target(
        data: Dict[str, Any],
        label: str,
        tag: str,
        target: str) -> Dict[str, str]:
    entries: List[Dict[str, Any]] = (data.get(label) or [])
    for entry in entries:
        if entry.get("name") == tag:
            for t in (entry.get("targets") or []):
                if t.get("target") == target:
                    platforms = (t.get("platforms") or "").strip()
                    return {"exists": "true", "platforms": platforms}
            break
    return {"exists": "false", "platforms": ""}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--label",  required=True)
    p.add_argument("--tag",    required=True)
    p.add_argument("--target", required=True)
    p.add_argument("--file", default="templates.yml")
    args = p.parse_args()

    try:
        data = load_yaml(args.file)
    except Exception as e:
        core.error(f"[check-target] Error reading {args.file}: {e}")
        core.set_output("exists", "false")
        core.set_output("platforms", "")
        return 0

    result = find_target(data, args.label, args.tag, args.target)
    core.info(
        f"[check-target] "
        f"label={args.label} tag={args.tag} target={args.target} "
        f"exists={result['exists']} platforms={result['platforms']}"
    )
    core.set_output("exists", result["exists"])
    core.set_output("platforms", result["platforms"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
