"""Verify named defects and controls with the same final harness and immutable source."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
BASE = "97289f110f7e9f89acdfe242098cb2d08e8b979e"


@unittest.skipUnless(sys.platform == "darwin", "macOS synthetic host")
class OwnershipBaselineTests(unittest.TestCase):
    def test_exact_baseline_failures_and_controls(self):
        with tempfile.TemporaryDirectory(prefix="window-control-baseline-") as directory:
            root = Path(directory)
            archive = subprocess.check_output([
                "git", "-C", str(ROOT), "archive", BASE, "4D Plugin API", "support",
                "4DPlugin-Window-Control.cpp", "4DPlugin-Window-Control.h",
            ])
            subprocess.run(["tar", "-x", "-C", str(root)], input=archive, check=True)
            results = root / "results.json"
            run = subprocess.run(
                [sys.executable, str(ROOT / ".github/tests/test_ownership.py")],
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                     "OWNERSHIP_SOURCE_ROOT": str(root), "OWNERSHIP_BASELINE_COPY": "1",
                     "OWNERSHIP_RESULTS": str(results)},
                capture_output=True, text=True, timeout=180,
            )
            self.assertEqual(run.returncode, 1, run.stdout + run.stderr)
            rows = json.loads(results.read_text())
            expected_failures = set()
            actual_failures = set()
            for row in rows:
                name, text, empty, kind = (row[key] for key in ("name", "text", "empty", "kind"))
                key = (name, text, empty, kind)
                fails = (
                    (name.startswith("set-") and empty == "allocated")
                    or name in ("blob-allocation-failure", "copy-traits",
                                "copy-array", "assign-array", "copy-blob", "assign-blob")
                    or (name.startswith("get-") and (
                        (kind in ("string", "picture", "object", "collection")
                         and not (name == "get-c" and kind == "collection")
                         and not (kind == "string" and not text and empty == "null"))
                        or kind == "error-poison"
                        or (name == "get-a" and kind == "error-kind0")))
                    or (name == "stringify" and kind in (
                        "error-poison", "error-kind0", "error-handle", "error-first-handle",
                        "error-copy", "copy-string", "copy-picture", "copy-collection",
                        "copy-boolean", "copy-real"))
                )
                if fails:
                    expected_failures.add(key)
                if not row["passed"]:
                    actual_failures.add(key)
                if name in ("copy-array", "assign-array", "copy-blob", "assign-blob"):
                    self.assertIn("AddressSanitizer: heap-use-after-free", row["output"])
            self.assertEqual(len(rows), 154)
            self.assertEqual(len(expected_failures), 72)
            self.assertEqual(actual_failures, expected_failures)
            print("BASELINE 154 cases: 72 named failures (4 ASan unsafe copies), 82 controls pass")
            if os.environ.get("OWNERSHIP_BASELINE_LOG_DIR"):
                destination = Path(os.environ["OWNERSHIP_BASELINE_LOG_DIR"])
                (destination / "baseline-ownership.log").write_text(run.stdout + run.stderr)
                (destination / "baseline-ownership.json").write_text(results.read_text())


if __name__ == "__main__":
    unittest.main()
