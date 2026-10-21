import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import oss_ready_check


SCRIPT = Path(oss_ready_check.__file__).resolve()


class ScanTests(unittest.TestCase):
    def test_finds_common_files_case_insensitively(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "readme.MD").write_text("", encoding="utf-8")
            (root / "license.TXT").write_text("", encoding="utf-8")

            rows = oss_ready_check.scan(root)
            statuses = {check: status for _, status, check, _, _ in rows}

            self.assertEqual(statuses["README / project overview"], "Found")
            self.assertEqual(statuses["License"], "Found")

    def test_detects_alternate_ci_and_test_directory_names(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".gitlab-ci.yml").write_text("", encoding="utf-8")
            (root / "Spec").mkdir()

            rows = oss_ready_check.scan(root)
            details = {check: detail for _, _, check, detail, _ in rows}

            self.assertIn(".gitlab-ci.yml", details["CI workflow"])
            self.assertIn("Spec/", details["Test directory"])


class ReportTests(unittest.TestCase):
    def test_markdown_hides_absolute_path_and_includes_essential_guidance(self):
        with tempfile.TemporaryDirectory(prefix="private-path-") as temp:
            root = Path(temp) / "sample-project"
            root.mkdir()
            report = oss_ready_check.render_markdown(root.name, oss_ready_check.scan(root))

            self.assertIn("# OSS readiness checklist: `sample-project`", report)
            self.assertNotIn(str(root), report)
            self.assertIn("## Essential next steps", report)

    def test_json_report_is_parseable_and_lists_missing_essentials(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "sample-project"
            root.mkdir()
            report = json.loads(oss_ready_check.render_json(root.name, oss_ready_check.scan(root)))

            self.assertEqual(report["project"], "sample-project")
            self.assertEqual(report["summary"]["missing_essential"], ["README / project overview", "License"])
            self.assertFalse(report["summary"]["is_certification"])

    def test_strict_mode_exit_status_depends_on_readme_and_license(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "sample-project"
            root.mkdir()
            missing = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), str(root), "--strict"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(missing.returncode, 1, missing.stderr)

            (root / "README.md").write_text("Sample project\n", encoding="utf-8")
            (root / "LICENSE").write_text("Sample license\n", encoding="utf-8")
            ready = subprocess.run(
                [sys.executable, "-B", str(SCRIPT), str(root), "--strict"],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(ready.returncode, 0, ready.stderr)


if __name__ == "__main__":
    unittest.main()
