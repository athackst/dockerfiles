#!/usr/bin/env python3
"""Unit tests for dockerfiles_templates.api."""

from __future__ import annotations

import unittest

from dockerfiles_templates import (
    Templates,
    canonical_platform,
    filter_targets_by_platform,
    parse_platform,
    platforms_support,
)


class TemplatesApiTestCase(unittest.TestCase):
    def test_from_dict_rejects_duplicate_family_name(self) -> None:
        with self.assertRaises(ValueError):
            Templates.from_dict(
                {
                    "dockerfiles": [
                        {
                            "family": "ros2",
                            "name": "jazzy",
                            "distro": "jazzy",
                            "base_image": "ubuntu:24.04",
                            "targets": [
                                {
                                    "target": "base",
                                    "platforms": ["linux/amd64"],
                                }
                            ],
                        },
                        {
                            "family": "ros2",
                            "name": "jazzy",
                            "distro": "jazzy",
                            "base_image": "ubuntu:24.04",
                            "targets": [
                                {
                                    "target": "dev",
                                    "platforms": ["linux/amd64"],
                                }
                            ],
                        },
                    ]
                }
            )

    def test_from_dict_rejects_schema_invalid(self) -> None:
        with self.assertRaises(ValueError):
            Templates.from_dict(
                {
                    "dockerfiles": [
                        {
                            "family": "ros2",
                            "name": "jazzy",
                            "distro": "jazzy",
                            "base_image": "ubuntu:24.04",
                            # missing required targets
                        }
                    ]
                }
            )

    def test_entries_filters_family_eol_and_platform(self) -> None:
        templates = Templates.from_dict(
            {
                "dockerfiles": [
                    {
                        "family": "ros2",
                        "name": "jazzy",
                        "distro": "jazzy",
                        "base_image": "ubuntu:24.04",
                        "eol": "2099-01-01",
                        "targets": [
                            {
                                "target": "base",
                                "platforms": ["linux/amd64", "linux/arm64"],
                            }
                        ],
                    },
                    {
                        "family": "ros2",
                        "name": "foxy",
                        "distro": "foxy",
                        "base_image": "ubuntu:20.04",
                        "eol": "2020-01-01",
                        "targets": [
                            {
                                "target": "base",
                                "platforms": ["linux/amd64"],
                            }
                        ],
                    },
                    {
                        "family": "gz",
                        "name": "harmonic",
                        "distro": "harmonic",
                        "base_image": "ubuntu:22.04",
                        "targets": [
                            {
                                "target": "base",
                                "platforms": ["linux/amd64"],
                            }
                        ],
                    },
                ]
            }
        )

        entries = templates.entries(family="ros2", eol=False)
        self.assertEqual([e["name"] for e in entries], ["jazzy"])

        entries = templates.entries(family="ros2", eol=True)
        self.assertEqual([e["name"] for e in entries], ["jazzy", "foxy"])

        entries = templates.entries(platform="linux/arm64")
        self.assertEqual(
            [(e["family"], e["name"]) for e in entries], [("ros2", "jazzy")]
        )

    def test_get_entry_honors_eol_filter(self) -> None:
        templates = Templates.from_dict(
            {
                "dockerfiles": [
                    {
                        "family": "ros2",
                        "name": "foxy",
                        "distro": "foxy",
                        "base_image": "ubuntu:20.04",
                        "eol": "2020-01-01",
                        "targets": [
                            {
                                "target": "base",
                                "platforms": ["linux/amd64"],
                            }
                        ],
                    }
                ]
            }
        )
        self.assertIsNone(templates.get_entry("ros2", "foxy", eol=False))
        self.assertIsNotNone(templates.get_entry("ros2", "foxy", eol=True))

    def test_targets_for_platform(self) -> None:
        templates = Templates.from_dict(
            {
                "dockerfiles": [
                    {
                        "family": "ros2",
                        "name": "jazzy",
                        "distro": "jazzy",
                        "base_image": "ubuntu:24.04",
                        "targets": [
                            {"target": "base", "platforms": ["linux/amd64"]},
                            {"target": "dev", "platforms": ["linux/arm64"]},
                        ],
                    }
                ]
            }
        )
        entry = templates.get_entry("ros2", "jazzy", eol=True)
        assert entry is not None
        targets = templates.targets_for_platform(entry, "linux/arm64")
        self.assertEqual([t["target"] for t in targets], ["dev"])

    def test_platform_helpers(self) -> None:
        self.assertEqual(parse_platform("amd64"), ("linux", "amd64", None))
        self.assertEqual(parse_platform("linux/arm/v7"), ("linux", "arm", "v7"))
        self.assertEqual(canonical_platform("linux-arm-v7"), "linux/arm/v7")

        self.assertTrue(platforms_support(["linux/arm"], "linux/arm/v7"))
        self.assertFalse(platforms_support(["linux/arm/v7"], "linux/arm/v6"))

        targets = [
            {"target": "base", "platforms": ["linux/amd64"]},
            {"target": "dev", "platforms": ["linux/arm64"]},
        ]
        filtered = filter_targets_by_platform(targets, "linux/arm64")
        self.assertEqual([t["target"] for t in filtered], ["dev"])


if __name__ == "__main__":
    unittest.main()
