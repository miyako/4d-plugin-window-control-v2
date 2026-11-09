"""Immutable intake evidence, also valid after a genuine helper-created bump."""

import importlib.util
from pathlib import Path
import re
import stat
import subprocess
import sys
import unittest
import xml.etree.ElementTree as ET

import yaml


ROOT = Path(__file__).resolve().parents[2]
BASE = "c7dcedc8af73dfc03753ae4698eb8e24158afc90"
COORDINATED = "ab6b4cbe4c3458d819906615562ec4035ceee816"
FALLBACK = "534fee2d133e0ed51aa331c6d3e1e47543f23475"
MARKETING = "7c6252067985a40963aeb212bcb03f869ed18667"
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location(
    "contract_source", ROOT / ".github/scripts/source_version.py"
)
source = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(source)


def original(path, sha=BASE):
    return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{sha}:{path}"])


def block(workflow, name):
    return workflow.split(f"      - name: {name}\n", 1)[1].split(
        "\n      - name:", 1
    )[0].rstrip()


class RepositoryContractTests(unittest.TestCase):
    def test_header_history_not_buggy_body_controls_authority(self):
        path = ".github/workflows/bump-version.yml"
        header, body = original(path).decode().split("name: Bump version", 1)
        self.assertIn("MARKETING_VERSION/CURRENT_PROJECT_VERSION AND Info.plist", header)
        self.assertIn("CFBundleShortVersionString/CFBundleVersion", header)
        self.assertIn('KEY="MARKETING_VERSION"', body)
        self.assertIn('KEY="CURRENT_PROJECT_VERSION"', body)
        self.assertIn("falling back to CURRENT_PROJECT_VERSION", original(path, FALLBACK).decode())
        self.assertIn("# Bumps MARKETING_VERSION", original(path, MARKETING).decode())
        message = subprocess.check_output(
            ["git", "-C", str(ROOT), "show", "-s", "--format=%B", COORDINATED], text=True,
        )
        self.assertIn("MARKETING_VERSION, CURRENT_PROJECT_VERSION", message)
        self.assertEqual(source.AUTHORITY, "coordinated")
        release = original(".github/workflows/release.yml").decode()
        self.assertIn("  push:\n    tags:\n      - 'v*.*.*'", release)
        self.assertNotIn("pull_request:", release)
        self.assertNotIn("branches:", release)

    def test_source_has_only_authorized_version_token_changes(self):
        current = source.read(ROOT)
        self.assertEqual(source.SETTING_COUNT, 6)
        for path in source.SOURCE_PATHS:
            with self.subTest(path=path):
                before = original(path)
                if path == source.PROJECT:
                    expected = re.sub(
                        rb"((?:MARKETING_VERSION|CURRENT_PROJECT_VERSION) = )[^;]+;",
                        lambda m: m[1] + current.encode() + b";", before,
                    )
                elif path == source.LOCALIZED:
                    old = re.search(rb'CFBundleShortVersionString = "([^"]+)"', before)[1]
                    expected = before.replace(old, current.encode())
                    self.assertNotIn(b"\n", before)
                    self.assertIn(b"\r", before)
                else:
                    expected = re.sub(
                        rb"(<key>CFBundleShortVersionString</key>\s*<string>)[^<]+",
                        lambda m: m[1] + current.encode(), before,
                    )
                self.assertEqual((ROOT / path).read_bytes(), expected)
                self.assertEqual(stat.S_IMODE((ROOT / path).stat().st_mode), 0o644)
        self.assertNotIn(b"<key>CFBundleVersion</key>", (ROOT / source.PLIST).read_bytes())

    def test_all_unrelated_original_bytes_and_modes_preserved(self):
        tree = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-tree", "-r", BASE], text=True,
        ).splitlines()
        allowed = {*map(str, source.SOURCE_PATHS), "README.md",
                   ".github/workflows/bump-version.yml", ".github/workflows/release.yml"}
        for line in tree:
            record, name = line.split("\t")
            if name in allowed:
                continue
            with self.subTest(path=name):
                self.assertEqual((ROOT / name).read_bytes(), original(name))
                self.assertEqual(stat.S_IMODE((ROOT / name).stat().st_mode),
                                 int(record.split()[0], 8) & 0o777)

    def test_exactly_two_independent_manual_entries(self):
        paths = sorted((ROOT / ".github/workflows").glob("*.yml"))
        self.assertEqual(len(paths), 2)
        workflows = [yaml.safe_load(path.read_text()) for path in paths]
        bump, build = workflows
        self.assertEqual(bump["name"], "Bump version")
        self.assertEqual(build["name"], "Build")
        self.assertEqual(set(bump[True]), {"workflow_dispatch"})
        self.assertEqual(set(build[True]), {"workflow_dispatch"})
        self.assertIsNone(build[True]["workflow_dispatch"])
        self.assertEqual(bump[True]["workflow_dispatch"]["inputs"], {
            "mode": {"type": "choice", "description": "Semantic version bump",
                     "options": ["patch", "minor", "major"], "default": "patch",
                     "required": True},
        })
        for workflow in workflows:
            for job in workflow["jobs"].values():
                for step in job["steps"]:
                    if step.get("uses", "").startswith("actions/checkout@"):
                        self.assertEqual(step["with"]["ref"], "${{ github.sha }}")
        self.assertEqual(build["concurrency"],
                         {"group": "release-publication", "cancel-in-progress": False})
        self.assertEqual(set(build["jobs"]), {"version", "build-macos"})
        self.assertEqual(build["jobs"]["build-macos"]["needs"], ["version"])
        content = paths[1].read_text()
        for absent in ("windows-latest", "pwsh", "shell: cmd", "softprops/",
                       "${{ inputs.", "github.ref_name", "refs/heads/master"):
            self.assertNotIn(absent, content)
        names = [
            "validate source and publication availability", "import Developer ID certificate",
            "store notarytool credentials", "build macOS plugin (universal)",
            "verify universal binary", "codesign", "package, notarize & staple",
            "create GitHub Release",
        ]
        self.assertEqual([content.index(f"- name: {name}\n") for name in names],
                         sorted(content.index(f"- name: {name}\n") for name in names))

    def test_actual_native_topology_outputs_resources_and_original_notes(self):
        before = original(".github/workflows/release.yml").decode()
        after = (ROOT / ".github/workflows/release.yml").read_text()
        for name in ("import Developer ID certificate", "store notarytool credentials"):
            self.assertEqual(block(before, name), block(after, name))
        secrets = r"\$\{\{ secrets\.([A-Z_]+) \}\}"
        self.assertEqual(re.findall(secrets, before), re.findall(secrets, after))
        self.assertNotIn("build-windows:", before)
        self.assertNotIn("i386", before)
        self.assertNotIn("otool", before)
        self.assertNotIn("otool", after)
        release = yaml.safe_load(before)["jobs"]["build-macos"]["steps"][-1]
        self.assertEqual(set(release["with"]), {"tag_name", "name", "files"})
        project = (ROOT / source.PROJECT).read_text()
        self.assertIn('SYMROOT = "$(SRCROOT)/test/Plugins";', project)
        self.assertEqual(project.count('CONFIGURATION_BUILD_DIR = "$(BUILD_DIR)";'), 2)
        self.assertIn('CONFIGURATION_BUILD_DIR="$PWD/test/Plugins"', after)
        for required in ("-configuration Default", 'ARCHS="arm64 x86_64"',
                         "ONLY_ACTIVE_ARCH=NO", "MACOS_DEPLOYMENT_TARGET: '10.13'",
                         "codesign --verify --deep --strict", 'stapler staple "$DMG_PATH"'):
            self.assertIn(required, before)
            self.assertIn(required, after)
        for resource in ("InfoPlist.strings in Resources", "constants.xlf in CopyFiles",
                         "manifest.json in CopyFiles", "Cocoa.framework in Frameworks"):
            self.assertIn(resource, project)
        # Dormant Windows project is evidence, not permission to invent a native job.
        ns = {"m": "http://schemas.microsoft.com/developer/msbuild/2003"}
        tree = ET.parse(ROOT / "Window Control.vcxproj")
        condition = "'$(Configuration)|$(Platform)'=='Release|x64'"
        outdirs = [node.text for node in tree.findall(".//m:OutDir", ns)
                   if node.get("Condition") == condition]
        self.assertEqual(outdirs, [
            "$(ProjectDir)test\\plugins\\$(ProjectName).bundle\\contents\\windows64\\",
        ])
        self.assertEqual({node.text for node in tree.findall(".//m:PlatformToolset", ns)}, {"v140"})


if __name__ == "__main__":
    unittest.main()
