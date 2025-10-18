#!/usr/bin/env python3
"""Unit tests for the docker-targets helper script."""

from __future__ import annotations

import importlib.util
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


def load_module() -> object:
    module_path = Path(__file__).resolve().parents[1] / "get_targets.py"
    spec = importlib.util.spec_from_file_location(
        "docker_targets_under_test", module_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[misc]
    return module


TARGETS_MODULE = load_module()


class GetTargetsTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._cwd = os.getcwd()
        self._tmpdir = tempfile.TemporaryDirectory()
        os.chdir(self._tmpdir.name)
        self.core_mock = MagicMock()
        TARGETS_MODULE.core = self.core_mock

    def tearDown(self) -> None:
        os.chdir(self._cwd)
        self._tmpdir.cleanup()

    def _write_templates(self, content: str) -> Path:
        path = Path("templates.yml")
        path.write_text(textwrap.dedent(content), encoding="utf-8")
        return path

    def _outputs(self) -> dict[str, list]:
        captured: dict[str, list] = {}
        for call in self.core_mock.set_output.call_args_list:
            name, value = call.args[:2]
            captured[name] = value
        return captured

    def test_main_filters_by_changed_files_and_sets_outputs(self) -> None:
        self._write_templates(
            """
            ros2:
              - name: rolling
                targets:
                  - target: base
                    platforms: linux/amd64
              - name: humble
                eol: true
            gazebo:
              - name: garden
            """
        )

        argv = [
            "get_targets.py",
            "--platform",
            "linux/amd64",
            "--changed",
            "ros2/rolling.Dockerfile,ignores/me.txt",
        ]
        with patch.object(sys, "argv", argv):
            exit_code = TARGETS_MODULE.main()

        self.assertEqual(exit_code, 0)
        outputs = self._outputs()
        self.assertIn("distros", outputs)
        self.assertIn("families", outputs)
        self.assertIn("stages", outputs)

        distros = outputs["distros"]
        self.assertEqual(distros, [{"family": "ros2", "distro": "rolling"}])
        self.assertEqual(outputs["families"], ["ros2"])
        self.assertEqual(
            outputs["stages"],
            [
                {
                    "family": "ros2",
                    "distro": "rolling",
                    "stage": "base",
                    "platforms": "linux/amd64",
                }
            ],
        )

    def test_main_returns_all_when_flag_set(self) -> None:
        self._write_templates(
            """
            ros2:
              - name: rolling
                targets:
                  - target: base
            gazebo:
              - name: garden
            """
        )

        argv = [
            "get_targets.py",
            "--all",
            "true",
            "--changed",
            "ros2/rolling.Dockerfile",
        ]
        with patch.object(sys, "argv", argv):
            exit_code = TARGETS_MODULE.main()

        self.assertEqual(exit_code, 0)
        outputs = self._outputs()
        distros = outputs["distros"]
        self.assertEqual(
            sorted(distros, key=lambda x: (x["family"], x["distro"])),
            [
                {"family": "gazebo", "distro": "garden"},
                {"family": "ros2", "distro": "rolling"},
            ],
        )
        self.assertEqual(sorted(outputs["families"]), ["gazebo", "ros2"])
        self.assertEqual(
            outputs["stages"],
            [
                {
                    "family": "ros2",
                    "distro": "rolling",
                    "stage": "base",
                    "platforms": "",
                }
            ],
        )

    def test_main_with_no_changes_produces_empty_outputs(self) -> None:
        self._write_templates(
            """
            ros2:
              - name: rolling
                targets:
                  - target: base
            """
        )

        argv = [
            "get_targets.py",
            "--all",
            "false",
            "--changed",
            "",
        ]
        with patch.object(sys, "argv", argv):
            exit_code = TARGETS_MODULE.main()

        self.assertEqual(exit_code, 0)
        outputs = self._outputs()
        self.assertEqual(outputs.get("distros"), [])
        self.assertEqual(outputs.get("families"), [])
        self.assertEqual(outputs.get("stages"), [])

    def test_collect_non_eol_respects_platform_filter(self) -> None:
        data = {
            "ros2": [
                {
                    "name": "rolling",
                    "targets": [
                        {"target": "base", "platforms": "linux/amd64"},
                        {"target": "dev", "platforms": "linux/arm64"},
                    ],
                }
            ]
        }
        results = TARGETS_MODULE.collect_non_eol(data, platform="linux/arm64")
        self.assertEqual(results, [{"family": "ros2", "distro": "rolling"}])

        results = TARGETS_MODULE.collect_non_eol(data, platform="linux/ppc64le")
        self.assertEqual(results, [])

    def test_parse_changed_ignores_non_dockerfiles(self) -> None:
        raw = "ros2/rolling.Dockerfile\nros2/README.md,gazebo/garden.Dockerfile"
        changed = TARGETS_MODULE.parse_changed(raw)
        self.assertEqual(
            changed,
            {("ros2", "rolling"), ("gazebo", "garden")},
        )


if __name__ == "__main__":
    unittest.main()
