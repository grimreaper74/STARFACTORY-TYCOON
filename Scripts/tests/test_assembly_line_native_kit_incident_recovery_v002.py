"""Offline contract tests for incident-bound Assembly recovery v002."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = ROOT / "Scripts"
BASELINE = SCRIPTS / "assembly_line_native_kit_incident_recovery_baseline_v002.json"
FREEZER = SCRIPTS / "freeze_assembly_line_native_kit_incident_recovery_baseline_v002.py"
RUNTIME = SCRIPTS / "assembly_line_native_kit_incident_recovery_runtime_v002.py"
VALIDATOR = SCRIPTS / "revalidate_assembly_line_native_kit_incident_v002.py"
RUNNER = SCRIPTS / "run_assembly_line_native_kit_incident_recovery_v002.ps1"
DOC = ROOT / "Docs/AssemblyShop/ASSEMBLY_LINE_NATIVE_KIT_INCIDENT_RECOVERY_v002.md"
AUDIT = ROOT / "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/IncidentRecovery_v002"
ORIGINAL_RUN = ROOT / "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/UnrealImportLane_v001/20260815T025138Z-2b421583"
TARGET = ROOT / "Content/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class IncidentRecoveryV002Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
        cls.freezer = FREEZER.read_text(encoding="utf-8")
        cls.runtime = RUNTIME.read_text(encoding="utf-8")
        cls.validator = VALIDATOR.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_python_parsers_and_successor_identity(self) -> None:
        for path in (FREEZER, RUNTIME, VALIDATOR):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        self.assertEqual(self.baseline["$schema"], "lineboss/assembly-native-kit-v001/incident-recovery-baseline/v2")
        self.assertEqual(self.baseline["status"],
                         "FROZEN__ASSEMBLY_NATIVE_KIT_V001_INCIDENT_RECOVERY_BASELINE_V002__READ_ONLY_REVALIDATION_ONLY")
        self.assertIn(f'EXPECTED_BASELINE_SHA256 = "{sha256(BASELINE)}"', self.runtime)

    def test_incident_is_exact_two_additions_and_no_removal(self) -> None:
        incident = self.baseline["incident"]
        self.assertEqual(incident["old_source_count"], 276)
        self.assertEqual(incident["settled_source_count"], 278)
        self.assertEqual(incident["removed_files"], [])
        expected = {
            "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.h":
                "5D24296B0FF7239276793DCA0232DBFB239E6C393B0ED7EA2D767F15BFF7F8C8",
            "Source/LineBossCarFactory/LBOneFactoryCaptureBridge.cpp":
                "447C04E64A2F322754C6F78523A34A59D9E133B3D949B766064D9FD112F15ECD",
        }
        self.assertEqual({path: row["sha256"] for path, row in incident["exact_added_files"].items()}, expected)
        self.assertEqual(len(list((ROOT / "Source").rglob("*.*"))), 278)

    def test_original_lane_and_incident_evidence_are_exactly_preserved(self) -> None:
        incident = self.baseline["incident"]
        self.assertEqual(incident["original_baseline"]["sha256"],
                         "041C802023D14ADE7EC418EF7488679D7F4A03550471AE38E2DC80B310E731BA")
        self.assertEqual(incident["successful_import_receipt"]["sha256"],
                         "C0E1F8D3E7B6EEBB2780067671AF408C53368DEA9370B3AA56B9F7F3AAFD49F7")
        self.assertEqual(incident["original_validation_failure_receipt"]["sha256"],
                         "269F732E2433EEC7948EB17F6FFE453D18F6CEEA3CF70239A99B67517799D57B")
        self.assertEqual(sha256(ORIGINAL_RUN / "import_receipt_v001.json"),
                         incident["successful_import_receipt"]["sha256"])
        self.assertEqual(sha256(ORIGINAL_RUN / "fresh_load_validation_failure_v001.json"),
                         incident["original_validation_failure_receipt"]["sha256"])
        groups = {row["name"]: row for row in self.baseline["protected"]["groups"]}
        self.assertEqual(groups["incident_original_run_receipts_and_logs"]["file_count"], 9)
        self.assertEqual(groups["original_lane_static_authority"]["file_count"], 9)

    def test_existing_eight_packages_match_pass_receipt(self) -> None:
        expected = {
            "SM_LB_Assembly_SequencedPartsCart_v001.uasset": "25D094761F8C1FE4C13C2A0F17849F846E5A9C9025AC1D1947F9E808719D77C1",
            "SM_LB_Assembly_SkilletCarrier_v001.uasset": "A7C270011AB26453D16D352E3A8118E8A3F985B886080341D19EFE124D45527A",
            "SM_LB_Assembly_WheelTireRack_v001.uasset": "6BFF53032877BB588FBA6F28BB4549B21AAC4B0578B06B9ABCE527AFA762FA5E",
            "SM_LB_Assembly_CockpitInstallAssist_v001.uasset": "5F148BDF168FA66CB6B0149D8340BF0A4F6D88E75E3757B4C9461C1BC3D43540",
            "SM_LB_Assembly_HeavyMarriageGantry_v001.uasset": "F19E3F3421F24D37B3549F686C562270CD2BDBE331F1D22EF2088198F1B44F9D",
            "SM_LB_Assembly_ErgonomicLiftPlatform_v001.uasset": "88676C5368E5B2724506AF1119E599877D218F5D5EA2C62A6AC7AB8CAC5104DB",
            "SM_LB_Assembly_EOLInspectionArch_v001.uasset": "9544FEC3F37348361A50E2BDB4CB398812F08689322B27CF5A5CFFA4DF7BC9BB",
            "SM_LB_Assembly_WheelAlignmentBed_v001.uasset": "093F7F3C54B63AA029A90CF4C604FA88873AE331C43D6D44F9FAAE3E90E88661",
        }
        files = list(TARGET.rglob("*.uasset"))
        self.assertEqual(len(files), 8)
        self.assertEqual({path.name: sha256(path) for path in files}, expected)
        self.assertEqual({Path(row["path"]).name: row["sha256"]
                          for row in self.baseline["incident"]["target_packages"]}, expected)

    def test_read_only_policy_and_complete_protected_settled_state(self) -> None:
        policy = self.baseline["policy"]
        for key in ("importer_authorized", "content_writes_authorized", "asset_or_level_saves_authorized",
                    "reimport_delete_overwrite_authorized", "original_baseline_run_receipts_logs_mutation_authorized"):
            self.assertFalse(policy[key], key)
        self.assertTrue(policy["independent_fresh_process_required"])
        groups = {row["name"] for row in self.baseline["protected"]["groups"]}
        self.assertTrue({"complete_source_tree_278", "complete_config_tree", "campaign_save_games",
                         "all_existing_content_including_eight_imported_packages",
                         "frozen_assembly_source_authority", "original_lane_static_authority",
                         "incident_original_run_receipts_and_logs", "exact_press_v913_map",
                         "exact_restored_press_map", "exact_body_map", "exact_paint_map",
                         "exact_one_factory_map"}.issubset(groups))
        self.assertEqual(self.baseline["protected"]["file_count"], 15700)

    def test_validator_has_no_import_or_asset_content_write_api(self) -> None:
        for forbidden in ("AssetImportTask(", "import_asset", "import_lod(", "save_loaded_asset(", "save_asset(",
                          "delete_asset(", "delete_directory(", "load_level(", "save_current_level("):
            self.assertNotIn(forbidden, self.validator)
        self.assertIn("full_hash=True", self.validator)
        self.assertIn("target_after != target_before", self.validator)
        self.assertIn('"content_writes": []', self.validator)
        self.assertIn('"importer_launched": False', self.validator)

    def test_runner_is_one_fresh_full_editor_process_and_pins_inputs(self) -> None:
        self.assertEqual(self.runner.count("Invoke-GuardedProcess $Editor"), 1)
        self.assertNotIn("import_assembly_line_native_kit_v001.py", self.runner)
        self.assertIn("-NoCompile", self.runner)
        self.assertIn("-NullRHI", self.runner)
        self.assertIn("$null = $Process.Handle", self.runner)
        self.assertIn("$Process.Refresh()", self.runner)
        self.assertIn("$null -eq $ExitCode", self.runner)
        self.assertIn("PASS__INCIDENT_BOUND_SUCCESSOR_BASELINE_FULL_REVERIFY", self.runner)
        paths = {"baseline": BASELINE, "freezer": FREEZER, "runtime": RUNTIME, "validator": VALIDATOR}
        for label, path in paths.items():
            match = re.search(rf"^\s*{label}\s*=\s*'([0-9A-F]{{64}})'", self.runner, re.MULTILINE)
            self.assertIsNotNone(match, label)
            self.assertEqual(match.group(1), sha256(path), label)

    def test_static_only_doc_and_one_use_namespace(self) -> None:
        self.assertFalse(AUDIT.exists())
        self.assertIn("Static-only preparation complete", self.doc)
        self.assertIn("never launches the importer", self.doc)
        self.assertIn("278-file Source tree", self.doc)
        self.assertIn("REVALIDATE_EXISTING_ASSEMBLY_NATIVE_KIT_V001_INCIDENT_V002_ONCE", self.doc)


if __name__ == "__main__":
    unittest.main()
