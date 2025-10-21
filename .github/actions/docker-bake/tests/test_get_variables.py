import importlib.util
import json
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch


def load_get_variables_module():
    # Ensure the parent directory (containing merge_manifests.py) is importable
    module_path = Path(__file__).resolve().parents[1] / "get_variables.py"
    spec = importlib.util.spec_from_file_location(
        "get_variables_under_test", module_path
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)  # type: ignore[call-arg]
    return module


class GetVariablesTestCase(unittest.TestCase):
    def setUp(self):
        self.original_cwd = os.getcwd()
        self.tmpdir = tempfile.TemporaryDirectory()
        os.chdir(self.tmpdir.name)
        self.module = load_get_variables_module()
        self.core_mock = MagicMock()
        self.module.core = self.core_mock

    def tearDown(self):
        os.chdir(self.original_cwd)
        self.tmpdir.cleanup()

    def _write_templates(self, content: str) -> None:
        Path("templates.yml").write_text(textwrap.dedent(content), encoding="utf-8")

    def _run_main(self, argv: list[str]) -> int:
        with patch.object(sys, "argv", argv):
            return self.module.main()

    def _outputs_dict(self) -> dict[str, str]:
        return {
            call.args[0]: call.args[1]
            for call in self.core_mock.set_output.call_args_list
        }

    def test_main_emits_expected_outputs(self):
        self._write_templates(
            """
            ros2:
              - name: rolling
                eol: false
                targets:
                  - target: base
                    platforms: linux/amd64,linux/arm64
                  - target: dev
                    platforms: linux/amd64
            """
        )

        exit_code = self._run_main(
            [
                "get_variables.py",
                "--family",
                "ros2",
                "--distro",
                "rolling",
                "--platform",
                "linux/amd64",
                "--ghcr-username",
                "gh",
                "--docker-username",
                "dk",
                "--digest",
            ]
        )

        self.assertEqual(exit_code, 0)
        self.core_mock.set_failed.assert_not_called()

        outputs = self._outputs_dict()
        self.assertEqual(outputs["platform"], "linux/amd64")
        self.assertEqual(outputs["group"], "ros2-rolling-linux-amd64")

        stages = json.loads(outputs["stages"])
        self.assertEqual(stages, ["base", "dev"])

        stage_targets = json.loads(outputs["stage_targets"])
        self.assertEqual(stage_targets, ["ros2-rolling-base", "ros2-rolling-dev"])

        set_lines = outputs["set_lines"]
        self.assertIn("ghcr.io/gh/ros2", set_lines)
        self.assertIn("docker.io/dk/ros2", set_lines)

    def test_main_sets_exists_false_when_targets_missing(self):
        self._write_templates(
            """
            ros2:
              - name: rolling
                eol: false
                targets:
                  - target: base
                    platforms: linux/arm64
            """
        )

        exit_code = self._run_main(
            [
                "get_variables.py",
                "--family",
                "ros2",
                "--distro",
                "rolling",
                "--platform",
                "linux/amd64",
            ]
        )

        self.assertEqual(exit_code, 0)
        self.core_mock.set_failed.assert_not_called()

        outputs = self._outputs_dict()
        self.assertEqual(outputs, {"exists": False})

    def test_main_fails_when_distro_missing(self):
        self._write_templates(
            """
            ros2:
              - name: humble
                eol: false
                targets:
                  - target: base
                    platforms: linux/amd64
            """
        )

        exit_code = self._run_main(
            [
                "get_variables.py",
                "--family",
                "ros2",
                "--distro",
                "rolling",
                "--platform",
                "linux/amd64",
            ]
        )

        self.assertEqual(exit_code, 1)
        self.core_mock.set_failed.assert_called()
        self.assertEqual(self._outputs_dict(), {})


if __name__ == "__main__":
    unittest.main()
