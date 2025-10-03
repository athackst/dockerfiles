#!/usr/bin/env python3
"""Ad-hoc harness for inspecting merge_manifests behaviour."""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure the parent directory (containing merge_manifests.py) is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import merge_manifests  # noqa:E402


def main() -> None:
    base_dir = Path(__file__).parent
    paths = sorted(base_dir.glob("bake-metadata-*.json"))
    print(f"Discovered metadata files: {[p.name for p in paths]}")

    targets = merge_manifests.collect_targets(paths)
    print("Collected targets:")
    for name, entries in targets.items():
        print(f"  {name}: {len(entries)} entries")
        for entry in entries:
            print(f"    - image: {entry['image']}, digest: {entry['digest']}")

    merged = merge_manifests.ensure_release_targets("ros2", "humble", targets)
    print("Filtered release targets:")
    for name, entries in merged.items():
        print(f"  {name}: {len(entries)} entries")


if __name__ == "__main__":
    main()
