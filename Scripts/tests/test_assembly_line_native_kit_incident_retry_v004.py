"""Offline contract tests for chronology-safe Assembly retry v004."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = ROOT / "Scripts"
BASELINE = SCRIPTS / "assembly_line_native_kit_incident_retry_baseline_v004.json"
FREEZER = SCRIPTS / "freeze_assembly_line_native_kit_incident_retry_baseline_v004.py"
RUNTIME = SCRIPTS / "assembly_line_native_kit_incident_retry_runtime_v004.py"
VALIDATOR = SCRIPTS / "revalidate_assembly_line_native_kit_incident_v004.py"
RUNNER = SCRIPTS / "run_assembly_line_native_kit_incident_retry_v004.ps1"
PATH_TEST = SCRIPTS / "tests/test_assembly_line_native_kit_execute_python_path_v004.ps1"
DOC = ROOT / "Docs/AssemblyShop/ASSEMBLY_LINE_NATIVE_KIT_INCIDENT_RETRY_v004.md"
FAILED_V003 = ROOT / "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v003/20260815T032759Z-6c42095d"
V004_AUDIT = ROOT / "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v004"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class IncidentRetryV004Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
        cls.freezer = FREEZER.read_text(encoding="utf-8")
        cls.runtime = RUNTIME.read_text(encoding="utf-8")
        cls.validator = VALIDATOR.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_python_and_powershell_parsers(self) -> None:
        for path in (FREEZER, RUNTIME, VALIDATOR):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        command = (
            "$t=$null;$e=$null;[void][System.Management.Automation.Language.Parser]::ParseFile("
            f"'{RUNNER}',[ref]$t,[ref]$e);if($e.Count){{exit 1}}"
        )
        result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", command],
                                capture_output=True, text=True, timeout=30, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_baseline_and_live_source_are_current(self) -> None:
        self.assertEqual(self.baseline["$schema"],
                         "lineboss/assembly-native-kit-v001/incident-retry-baseline/v4")
        self.assertIn("CHRONOLOGY_SEPARATED_FROM_CURRENT_SOURCE", self.baseline["status"])
        self.assertIn(f'EXPECTED_BASELINE_SHA256 = "{sha256(BASELINE)}"', self.runtime)
        expected = {
            "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.h":
                "2C5442B15B94504CEA085A3F46F4740BCC4FD0A83CDE70DB37E3C7D0FC04673B",
            "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.cpp":
                "849C7E1ACD6A02B27126831202E774E8C922E422050904EC3DF5349C6D01CA30",
        }
        for rel, digest in expected.items():
            self.assertEqual(sha256(ROOT / rel), digest)

    def test_history_is_pinned_but_not_applied_to_live_source(self) -> None:
        old = self.baseline["retry_v003_incident"]["historical_bridge_hashes"]
        current = self.baseline["retry_v003_incident"]["current_frozen_bridge_hashes"]
        self.assertNotEqual(old, current)
        self.assertFalse(self.baseline["policy"]["historical_hashes_applied_to_live_files"])
        self.assertNotIn("v002.verify_incident(", self.runtime)
        self.assertNotIn("v003.verify_retry_incident(", self.runtime)
        self.assertIn("recorded_historical != HISTORICAL_BRIDGE_HASHES", self.runtime)
        self.assertIn("item[\"sha256\"] != expected", self.runtime)

    def test_failed_v003_evidence_is_exact_and_read_only(self) -> None:
        expected = {
            "fresh_load_recovery_validation_failure_v003.json": "6483892E83834472030E513B401B86DD5FA2E2A69B0C43FFA553DFEAAF6B2143",
            "fresh_load_recovery_validation.log": "896C9EC609C5D268334C00BA3D6C977C303EBC04E044BA3293C1CE7B1E51C25F",
            "fresh_load_recovery_validation.stderr.log": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
            "fresh_load_recovery_validation.stdout.log": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
            "incident_recovery_summary_v003.json": "046F877BF247055C7739A29FE8BC9D37C0A6FEB2EB5452977CDD4641915EFA1F",
        }
        self.assertEqual({path.name: sha256(path) for path in FAILED_V003.iterdir() if path.is_file()}, expected)
        incident = self.baseline["retry_v003_incident"]
        self.assertTrue(incident["python_executed"])
        self.assertFalse(incident["asset_validation_executed"])
        self.assertEqual(incident["content_writes"], [])

    def test_complete_protected_inventory(self) -> None:
        groups = {row["name"]: row for row in self.baseline["protected"]["groups"]}
        self.assertEqual(groups["failed_v002_recovery_run_exact_evidence"]["file_count"], 4)
        self.assertEqual(groups["failed_v003_recovery_run_exact_evidence"]["file_count"], 5)
        self.assertEqual(groups["v003_retry_static_authority"]["file_count"], 10)
        self.assertEqual(groups["complete_source_tree_278"]["file_count"], 278)
        self.assertEqual(self.baseline["protected"]["file_count"], 15727)

    def test_validator_and_runner_are_static_read_only(self) -> None:
        for forbidden in ("AssetImportTask(", "import_asset", "import_lod(", "save_loaded_asset(",
                          "save_asset(", "delete_asset(", "delete_directory(", "save_current_level("):
            self.assertNotIn(forbidden, self.validator)
        self.assertIn("verify_chronology_and_current", self.validator)
        self.assertIn("full_hash=True", self.validator)
        self.assertIn("target_after != target_before", self.validator)
        self.assertEqual(self.runner.count("Invoke-GuardedProcess $Editor"), 1)
        self.assertNotIn("import_assembly_line_native_kit_v001.py", self.runner)
        self.assertIn("-NoCompile", self.runner)
        paths = {"baseline": BASELINE, "freezer": FREEZER, "runtime": RUNTIME, "validator": VALIDATOR}
        for label, path in paths.items():
            match = re.search(rf"^\s*{label}\s*=\s*'([0-9A-F]{{64}})'", self.runner, re.MULTILINE)
            self.assertIsNotNone(match, label)
            self.assertEqual(match.group(1), sha256(path), label)

    def test_execute_python_path_regression_runs_offline(self) -> None:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PATH_TEST)],
            cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS__EXECUTE_PYTHON_PATH_FORWARD_SLASH_NO_CONTROL_ESCAPE_V004", result.stdout)
        exact = ('-ExecutePythonScript="C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/'
                 'Scripts/revalidate_assembly_line_native_kit_incident_v004.py"')
        self.assertIn(exact, self.runner)

    def test_documented_and_unconsumed(self) -> None:
        self.assertFalse(V004_AUDIT.exists())
        self.assertIn("Static-only preparation is complete", self.doc)
        self.assertIn("REVALIDATE_EXISTING_ASSEMBLY_NATIVE_KIT_V001_INCIDENT_V004_ONCE", self.doc)


if __name__ == "__main__":
    unittest.main()
