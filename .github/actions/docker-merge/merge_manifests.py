#!/usr/bin/env python3
"""Merge per-platform bake metadata into multi-arch manifests."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Set

MetadataEntries = Dict[str, List[Dict[str, str]]]


def parse_args() -> argparse.Namespace:
    """Configure and parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Create multi-arch manifests from bake metadata."
    )
    parser.add_argument("--family", required=True, help="Program/family (e.g., ros2).")
    parser.add_argument(
        "--distro", required=True, help="Distro/release (e.g., rolling)."
    )
    parser.add_argument(
        "--metadata-list",
        required=True,
        help="Newline/comma separated list of metadata paths.",
    )
    parser.add_argument("--gh-owner", default="", help="GHCR owner/org for final tags.")
    parser.add_argument(
        "--dockerhub-username",
        default="",
        help="Docker Hub user/org for final tags.",
    )
    parser.add_argument(
        "--extra-tag",
        default="",
        help="Optional suffix appended to each manifest tag (e.g., date or ref).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the imagetools commands without executing.",
    )
    return parser.parse_args()


def _split_metadata_list(raw: str) -> List[str]:
    """Return non-empty tokens from a comma/newline delimited string."""
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


def resolve_metadata_paths(spec: str) -> List[Path]:
    """Resolve metadata spec into concrete JSON file paths."""
    paths: List[Path] = []
    tokens = _split_metadata_list(spec or "")
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


def collect_targets(paths: Iterable[Path]) -> MetadataEntries:
    """Aggregate target entries from all metadata files."""
    result: MetadataEntries = {}
    for path in paths:
        with path.open("r", encoding="utf-8") as fh:
            try:
                payload = json.load(fh)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
        if not isinstance(payload, dict):
            continue
        for name, node in payload.items():
            if not isinstance(node, dict):
                continue
            image = (
                node.get("image.name")
                or node.get("containerimage.name")
                or node.get("name")
            )
            digest = node.get("containerimage.digest")
            if not digest:
                descriptor = node.get("containerimage.descriptor", {})
                if isinstance(descriptor, dict):
                    digest = descriptor.get("digest")
            if not image or not digest:
                continue
            provenance = node.get("buildx.build.provenance", {})
            platform = ""
            if isinstance(provenance, dict):
                invocation = provenance.get("invocation", {})
                if isinstance(invocation, dict):
                    environment = invocation.get("environment", {})
                    if isinstance(environment, dict):
                        platform = environment.get("platform", "") or ""
            result.setdefault(name, []).append(
                {"image": image, "digest": digest, "platform": platform}
            )
    # Collapse duplicates per target/digest.
    deduped: MetadataEntries = {}
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


def ensure_release_targets(
    family: str, distro: str, target_map: MetadataEntries
) -> MetadataEntries:
    """Filter the collected targets down to a specific release."""
    release_prefix = f"{family}-{distro}"
    filtered: MetadataEntries = {}
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
    """Convert image/digest pairs into imagetools reference strings."""
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


def compute_tags(
    family: str,
    distro: str,
    stage: str,
    gh_owner: str,
    dockerhub_username: str,
    extra_tag: str = "",
) -> List[str]:
    """Return manifest tags for all configured registries."""
    suffix = f"{distro}-{stage}"
    extra = extra_tag.strip()
    if extra:
        extra = extra.replace("/", "-")
        extra = "-".join(extra.split())
    tags: List[str] = []
    if gh_owner:
        tags.append(f"ghcr.io/{gh_owner}/{family}:{suffix}")
        if extra:
            tags.append(f"ghcr.io/{gh_owner}/{family}:{suffix}-{extra}")
    if dockerhub_username:
        tags.append(f"docker.io/{dockerhub_username}/{family}:{suffix}")
        if extra:
            tags.append(f"docker.io/{dockerhub_username}/{family}:{suffix}-{extra}")
    return tags


def write_output(name: str, value: str) -> None:
    """Emit a GitHub Actions output key/value pair."""
    output_path = os.environ.get("GITHUB_OUTPUT")
    if not output_path:
        return
    with open(output_path, "a", encoding="utf-8") as fh:
        fh.write(f"{name}={value}\n")


def main() -> int:
    """Entry point for the merge manifest script."""
    args = parse_args()
    metadata_paths = resolve_metadata_paths(args.metadata_list)
    target_map = collect_targets(metadata_paths)
    release_targets = ensure_release_targets(args.family, args.distro, target_map)

    created_tags: Dict[str, List[str]] = {}
    prefix = f"{args.family}-{args.distro}-"
    for target, entries in sorted(release_targets.items()):
        if not target.startswith(prefix):
            continue
        stage_name = target[len(prefix) :]
        refs = build_refs(entries)
        if not refs:
            continue
        tags = compute_tags(
            args.family,
            args.distro,
            stage_name,
            args.gh_owner,
            args.dockerhub_username,
            args.extra_tag,
        )
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
