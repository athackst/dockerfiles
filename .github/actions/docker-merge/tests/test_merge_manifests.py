#!/usr/bin/env python3
"""Unit tests for merge_manifests helpers."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


def load_module():
    module_path = Path(__file__).resolve().parents[1] / "merge_manifests.py"
    spec = importlib.util.spec_from_file_location(
        "merge_manifests_under_test", module_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[misc]
    return module


MERGE_MODULE = load_module()


class MergeManifestsTestCase(unittest.TestCase):
    fixtures_dir = Path(__file__).parent / "fixtures"

    def _write_metadata(self, payload: dict) -> Path:
        tmp = tempfile.NamedTemporaryFile("w", delete=False, suffix=".json")
        json.dump(payload, tmp)
        tmp.close()
        return Path(tmp.name)

    def test_collect_targets_parses_metadata_and_deduplicates(self):
        payload = {
            "ros2-rolling-base": {
                "image.name": "ghcr.io/acme/ros2:rolling-base",
                "containerimage.digest": "sha256:abc",
                "buildx.build.provenance": {
                    "invocation": {"environment": {"platform": "linux/amd64"}}
                },
            },
            "ros2-rolling-dev": {
                "containerimage.name": "docker.io/acme/ros2:rolling-dev",
                "containerimage.descriptor": {"digest": "sha256:def"},
                "buildx.build.provenance": {
                    "invocation": {"environment": {"platform": "linux/amd64"}}
                },
            },
        }
        path = self._write_metadata(payload)

        targets = MERGE_MODULE.collect_targets([path])

        self.assertIn("ros2-rolling-base", targets)
        self.assertIn("ros2-rolling-dev", targets)
        base_entries = targets["ros2-rolling-base"]
        self.assertEqual(len(base_entries), 1)
        self.assertEqual(
            base_entries[0]["image"], "ghcr.io/acme/ros2:rolling-base"
        )
        self.assertEqual(base_entries[0]["digest"], "sha256:abc")
        self.assertEqual(base_entries[0]["platform"], "linux/amd64")

    def test_ensure_release_targets_filters_and_raises(self):
        target_map = {
            "ros2-rolling": [{"image": "skip", "digest": "sha"}],
            "ros2-rolling-base": [{"image": "ok", "digest": "sha"}],
            "ros2-rolling-dev": [{"image": "ok2", "digest": "sha2"}],
            "ros2-humble-base": [{"image": "other", "digest": "sha3"}],
        }

        filtered = MERGE_MODULE.ensure_release_targets(
            "ros2", "rolling", target_map
        )

        self.assertEqual(
            set(filtered.keys()), {"ros2-rolling-base", "ros2-rolling-dev"}
        )

        with self.assertRaises(ValueError):
            MERGE_MODULE.ensure_release_targets("ros2", "foxy", target_map)

    def test_build_refs_and_compute_tags(self):
        entries = [
            {"image": "ghcr.io/acme/ros2:rolling-base", "digest": "sha256:001"},
            {
                "image": "ghcr.io/acme/ros2@sha256:002",
                "digest": "sha256:unused",
            },
        ]
        refs = MERGE_MODULE.build_refs(entries)
        self.assertEqual(
            refs,
            [
                "ghcr.io/acme/ros2:rolling-base@sha256:001",
                "ghcr.io/acme/ros2@sha256:002",
            ],
        )

        tags = MERGE_MODULE.compute_tags(
            family="ros2",
            distro="rolling",
            stage="base",
            gh_owner="acme",
            dockerhub_username="acmehub",
            extra_tag="2025-01-01",
        )
        self.assertIn("ghcr.io/acme/ros2:rolling-base", tags)
        self.assertIn("ghcr.io/acme/ros2:rolling-base-2025-01-01", tags)
        self.assertIn("docker.io/acmehub/ros2:rolling-base", tags)
        self.assertIn("docker.io/acmehub/ros2:rolling-base-2025-01-01", tags)

    def test_collect_targets_with_real_metadata_fixtures(self):
        paths = sorted(
            self.fixtures_dir.glob("bake-metadata-ros2-humble-linux-*.json")
        )
        self.assertGreaterEqual(
            len(paths), 2, "Expected fixture metadata files"
        )

        targets = MERGE_MODULE.collect_targets(paths)
        self.assertIn("ros2-humble-base", targets)
        self.assertIn("ros2-humble-dev", targets)
        self.assertIn("ros2-humble-full", targets)
        # arm64 fixtures do not include the gazebo stage.
        self.assertIn("ros2-humble-gazebo", targets)

        base_entries = targets["ros2-humble-base"]
        digests = {entry["digest"] for entry in base_entries}
        self.assertEqual(len(base_entries), 2)
        self.assertEqual(
            digests,
            {
                "sha256:33f69049e6669819db6f3cce0befbb4b6b6aa7ef742c862d840af50983ea0e48",  # noqa:E501
                "sha256:ffceda33bb4a147b69cd01e894eaa87bf2aa6ebc449300ad8c8f2525b7b91a47",  # noqa:E501
            },
        )


if __name__ == "__main__":
    unittest.main()
