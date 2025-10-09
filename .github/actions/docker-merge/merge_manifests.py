#!/usr/bin/env python3
"""Merge per-platform bake metadata into multi-arch manifests."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create multi-arch manifests from bake metadata."
    )
    parser.add_argument("--family",
                        required=True,
                        help="Program/family (e.g., ros2).")
    parser.add_argument("--distro",
                        required=True,
                        help="Distro/release (e.g., rolling).")
    parser.add_argument("--metadata",
                        action="append",
                        default=[],
                        help="Path to a bake metadata JSON file (repeatable).")
    parser.add_argument("--metadata-list",
                        default="",
                        help="Newline/comma separated list of metadata paths.")
    parser.add_argument("--gh-owner",
                        default="",
                        help="GHCR owner/org for final tags.")
    parser.add_argument("--dockerhub-username",
                        default="",
                        help="Docker Hub user/org for final tags.")
    parser.add_argument("--dry-run",
                        action="store_true",
                        help="Print the imagetools commands without executing.")
    return parser.parse_args()


def _split_metadata_list(raw: str) -> List[str]:
    tokens: List[str] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            continue
        for part in line.split(","):
            item = part.strip()
            if item:
                tokens.append(item)
    return tokens


def resolve_metadata_paths(args: argparse.Namespace) -> List[Path]:
    paths: List[Path] = []
    tokens = list(args.metadata)
    tokens.extend(_split_metadata_list(args.metadata_list))
    for token in tokens:
        path = Path(token).expanduser()
        if path.is_dir():
            for candidate in sorted(path.glob("*.json")):
                paths.append(candidate)
        else:
            if not path.exists():
                raise FileNotFoundError(f"Metadata file not found: {path}")
            paths.append(path)
    if not paths:
        raise ValueError("No metadata files provided.")
    return paths


def walk_metadata(node: Any,
                  target: Optional[str],
                  platform: Optional[str],
                  acc: Dict[str, List[Dict[str, str]]]) -> None:
    if isinstance(node, dict):
        current_platform = node.get("platform", platform)
        if "target" in node and isinstance(node["target"], dict):
            for name, child in node["target"].items():
                walk_metadata(child, name, current_platform, acc)
        if "targets" in node and isinstance(node["targets"], dict):
            for name, child in node["targets"].items():
                walk_metadata(child, name, current_platform, acc)
        if "outputs" in node and isinstance(node["outputs"], dict):
            outputs = node["outputs"]
            images = outputs.get("images") or outputs.get("image") or []
            if isinstance(images, dict):
                images = [images]
            if isinstance(images, list):
                for entry in images:
                    image_name = None
                    digest = None
                    entry_platform = current_platform
                    if isinstance(entry, dict):
                        image_name = entry.get("name")
                        digest = entry.get("digest") or entry.get("imageDigest")
                        entry_platform = entry.get("platform") or entry_platform
                        if not image_name and isinstance(entry.get("names"), list):
                            image_name = entry["names"][0]
                    elif isinstance(entry, str):
                        image_name = entry
                    if image_name and digest:
                        acc.setdefault(target or "", []).append(
                            {
                                "image": image_name,
                                "digest": digest,
                                "platform": entry_platform or "",
                            }
                        )
        if "descriptor" in node and isinstance(node["descriptor"], dict):
            desc = node["descriptor"]
            reference = desc.get("reference") or desc.get("ref")
            digest = desc.get("digest")
            if reference and digest:
                base = reference.split("@", 1)[0]
                acc.setdefault(target or "", []).append(
                    {
                        "image": base,
                        "digest": digest,
                        "platform": desc.get("platform") or current_platform or "",
                    }
                )
        for key, value in node.items():
            if key in {"target", "targets", "outputs", "descriptor"}:
                continue
            walk_metadata(value, target, current_platform, acc)
    elif isinstance(node, list):
        for item in node:
            walk_metadata(item, target, platform, acc)


def collect_targets(paths: Iterable[Path]) -> Dict[str, List[Dict[str, str]]]:
    result: Dict[str, List[Dict[str, str]]] = {}
    for path in paths:
        with path.open("r", encoding="utf-8") as fh:
            try:
                payload = json.load(fh)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
        walk_metadata(payload, target=None, platform=None, acc=result)
    # Collapse duplicates per target/digest.
    deduped: Dict[str, List[Dict[str, str]]] = {}
    for target, entries in result.items():
        combo: Dict[str, Dict[str, str]] = {}
        for entry in entries:
            digest = entry.get("digest")
            image = entry.get("image")
            if not digest or not image:
                continue
            combo[f"{image}@{digest}"] = {
                "image": image,
                "digest": digest,
                "platform": entry.get("platform", ""),
            }
        if combo:
            deduped[target] = list(combo.values())
    return deduped


def ensure_release_targets(family: str,
                           distro: str,
                           target_map: Dict[str, List[Dict[str, str]]]
                           ) -> Dict[str, List[Dict[str, str]]]:
    release_prefix = f"{family}-{distro}"
    filtered: Dict[str, List[Dict[str, str]]] = {}
    for target, entries in target_map.items():
        if not target:
            continue
        if target == release_prefix:
            # Skip the aggregate release group.
            continue
        if not target.startswith(f"{release_prefix}-"):
            continue
        filtered[target] = entries
    if not filtered:
        raise ValueError(
            f"No target entries for release '{release_prefix}' in metadata."
        )
    return filtered


def build_refs(entries: List[Dict[str, str]]) -> List[str]:
    refs: Set[str] = set()
    for entry in entries:
        image = entry.get("image", "")
        digest = entry.get("digest", "")
        if not image or not digest:
            continue
        if "@sha256:" in image:
            # Already a digest reference.
            refs.add(image)
        else:
            refs.add(f"{image}@{digest}")
    return sorted(refs)


def compute_tags(family: str,
                 distro: str,
                 stage: str,
                 gh_owner: str,
                 dockerhub_username: str) -> List[str]:
    suffix = f"{distro}-{stage}"
    tags: List[str] = []
    if gh_owner:
        tags.append(f"ghcr.io/{gh_owner}/{family}:{suffix}")
    if dockerhub_username:
        tags.append(f"docker.io/{dockerhub_username}/{family}:{suffix}")
    return tags


def write_output(name: str, value: str) -> None:
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}={value}\n")


def main() -> int:
    args = parse_args()
    metadata_paths = resolve_metadata_paths(args)
    target_map = collect_targets(metadata_paths)
    release_targets = ensure_release_targets(args.family, args.distro, target_map)

    created_tags: Dict[str, List[str]] = {}
    for target, entries in sorted(release_targets.items()):
        stage = target.split(f"{args.family}-{args.distro}-", 1)
        if len(stage) != 2 or not stage[1]:
            continue
        stage_name = stage[1]
        refs = build_refs(entries)
        if not refs:
            continue
        tags = compute_tags(args.family,
                            args.distro,
                            stage_name,
                            args.gh_owner,
                            args.dockerhub_username)
        if not tags:
            raise ValueError("No destination tags specified for merge action.")
        cmd = ["docker", "buildx", "imagetools", "create"]
        for tag in tags:
            cmd.extend(["--tag", tag])
        cmd.extend(refs)
        print(f"[merge] {target}: creating manifest with {len(refs)} refs")
        print("        tags:", ", ".join(tags))
        print("        refs:", ", ".join(refs))
        if not args.dry_run:
            subprocess.run(cmd, check=True)
        created_tags[stage_name] = tags

    if not created_tags:
        raise ValueError("No manifests were created.")

    write_output("created_tags", json.dumps(created_tags))
    print("[merge] Created manifests for stages:")
    for stage, tags in created_tags.items():
        print(f"  - {stage}: {', '.join(tags)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
