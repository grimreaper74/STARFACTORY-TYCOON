"""Offline regression and contract tests for Assembly retry v003."""

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
BASELINE = SCRIPTS / "assembly_line_native_kit_incident_retry_baseline_v003_final.json"
FREEZER = SCRIPTS / "freeze_assembly_line_native_kit_incident_retry_baseline_v003.py"
RUNTIME = SCRIPTS / "assembly_line_native_kit_incident_retry_runtime_v003.py"
VALIDATOR = SCRIPTS / "revalidate_assembly_line_native_kit_incident_v003.py"
RUNNER = SCRIPTS / "run_assembly_line_native_kit_incident_retry_v003.ps1"
PATH_TEST = SCRIPTS / "tests/test_assembly_line_native_kit_execute_python_path_v003.ps1"
DOC = ROOT / "Docs/AssemblyShop/ASSEMBLY_LINE_NATIVE_KIT_INCIDENT_RETRY_v003.md"
FAILED_RUN = ROOT / "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v002/20260815T030646Z-e8c9a5eb"
V003_AUDIT = ROOT / "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v003"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class IncidentRetryV003Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
        cls.freezer = FREEZER.read_text(encoding="utf-8")
        cls.runtime = RUNTIME.read_text(encoding="utf-8")
        cls.validator = VALIDATOR.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")
        cls.path_test = PATH_TEST.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_python_parsers_and_baseline_pin(self) -> None:
        for path in (FREEZER, RUNTIME, VALIDATOR):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        self.assertEqual(self.baseline["$schema"], "lineboss/assembly-native-kit-v001/incident-retry-baseline/v3")
        self.assertEqual(self.baseline["status"],
                         "FROZEN__ASSEMBLY_NATIVE_KIT_V001_INCIDENT_RETRY_BASELINE_V003__FORWARD_SLASH_EXECUTE_PATH")
        self.assertIn(f'EXPECTED_BASELINE_SHA256 = "{sha256(BASELINE)}"', self.runtime)

    def test_failed_v002_attempt_is_exactly_preserved_and_python_never_executed(self) -> None:
        retry = self.baseline["retry_incident"]
        self.assertEqual(retry["classification"], "EXECUTE_PYTHON_PATH_BACKSLASH_R_BECAME_CARRIAGE_RETURN")
        self.assertFalse(retry["python_executed"])
        self.assertFalse(retry["asset_validation_executed"])
        self.assertEqual(retry["content_writes"], [])
        expected = {
            "fresh_load_recovery_validation.log": "9BC7F87884532B794F4FB49D9B13082A6ED4C48D0C46325730E2DBB4E78E9B72",
            "fresh_load_recovery_validation.stderr.log": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
            "fresh_load_recovery_validation.stdout.log": "E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855",
            "incident_recovery_summary_v002.json": "CEBFD5239081C66FFCEEE84FCDB593DE5D588D01C06B4B6B5F89CEE7FD3362EC",
        }
        self.assertEqual({Path(row["path"]).name: row["sha256"] for row in retry["evidence"]}, expected)
        for name, digest in expected.items():
            self.assertEqual(sha256(FAILED_RUN / name), digest, name)
        log = (FAILED_RUN / "fresh_load_recovery_validation.log").read_bytes()
        self.assertIn(b"Scripts" + bytes([13]) + b"evalidate_assembly_line_native_kit_incident_v002.py", log)
        self.assertFalse((FAILED_RUN / "fresh_load_recovery_validation_receipt_v002.json").exists())
        self.assertFalse((FAILED_RUN / "fresh_load_recovery_validation_failure_v002.json").exists())

    def test_complete_protection_includes_original_v002_and_failed_run(self) -> None:
        groups = {row["name"]: row for row in self.baseline["protected"]["groups"]}
        self.assertEqual(groups["failed_v002_recovery_run_exact_evidence"]["file_count"], 4)
        self.assertEqual(groups["v002_recovery_static_authority"]["file_count"], 8)
        self.assertEqual(groups["complete_source_tree_278"]["file_count"], 278)
        self.assertEqual(groups["all_existing_content_including_eight_imported_packages"]["file_count"], 15333)
        self.assertEqual(groups["superseded_v003_pre_ui_v005_baseline"]["file_count"], 1)
        self.assertEqual(self.baseline["protected"]["file_count"], 15713)

    def test_command_line_contract_requires_forward_slashes_and_no_control_characters(self) -> None:
        contract = self.baseline["command_line_contract"]
        self.assertEqual(contract["execute_python_path_separator"], "/")
        self.assertFalse(contract["backslash_or_control_character_authorized"])
        self.assertIn(".Replace('\\','/')", self.runner)
        self.assertIn("IndexOfAny([char[]](0..31))", self.runner)
        self.assertIn("$ValidatorExecutePath", self.runner)
        self.assertIn("$ExecutePythonArgument", self.runner)
        self.assertNotIn("('-ExecutePythonScript=\"{0}\"' -f $Validator)", self.runner)
        exact = ('-ExecutePythonScript="C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/'
                 'Scripts/revalidate_assembly_line_native_kit_incident_v003.py"')
        self.assertIn(exact, self.runner)
        self.assertIn(exact, self.path_test)

    def test_powershell_command_line_regression_executes_offline(self) -> None:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PATH_TEST)],
            cwd=ROOT, capture_output=True, text=True, timeout=30, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS__EXECUTE_PYTHON_PATH_FORWARD_SLASH_NO_CONTROL_ESCAPE_V003", result.stdout)

    def test_runner_has_one_validator_no_importer_and_hash_pins(self) -> None:
        self.assertEqual(self.runner.count("Invoke-GuardedProcess $Editor"), 1)
        self.assertNotIn("import_assembly_line_native_kit_v001.py", self.runner)
        self.assertIn("-NoCompile", self.runner)
        self.assertIn("PASS__V003_INCIDENT_BOUND_RETRY_BASELINE_FULL_REVERIFY", self.runner)
        paths = {"baseline": BASELINE, "freezer": FREEZER, "runtime": RUNTIME, "validator": VALIDATOR}
        for label, path in paths.items():
            match = re.search(rf"^\s*{label}\s*=\s*'([0-9A-F]{{64}})'", self.runner, re.MULTILINE)
            self.assertIsNotNone(match, label)
            self.assertEqual(match.group(1), sha256(path), label)

    def test_validator_is_read_only_and_full_hash_gated(self) -> None:
        for forbidden in ("AssetImportTask(", "import_asset", "import_lod(", "save_loaded_asset(", "save_asset(",
                          "delete_asset(", "delete_directory(", "save_current_level("):
            self.assertNotIn(forbidden, self.validator)
        self.assertIn("full_hash=True", self.validator)
        self.assertIn("target_after != target_before", self.validator)
        self.assertIn('"execute_python_path_separator": "/"', self.validator)

    def test_static_only_unconsumed_doc(self) -> None:
        self.assertFalse(V003_AUDIT.exists())
        self.assertIn("Static-only preparation complete", self.doc)
        self.assertIn("carriage return", self.doc)
        self.assertIn("REVALIDATE_EXISTING_ASSEMBLY_NATIVE_KIT_V001_INCIDENT_V003_ONCE", self.doc)


if __name__ == "__main__":
    unittest.main()
