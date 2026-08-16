"""Offline contract tests for the incident-bound native robot clean import lane."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = ROOT / "Scripts"
BASELINE_PATH = SCRIPTS / "body_shop_robot_native_unreal_import_baseline_v001.json"
FREEZER_PATH = SCRIPTS / "freeze_body_shop_robot_native_unreal_import_baseline_v001.py"
DISPOSITION_PATH = SCRIPTS / "body_shop_robot_native_unreal_recovery_contract_v001.json"
DISPOSITION_FREEZER_PATH = SCRIPTS / "freeze_body_shop_robot_native_unreal_recovery_v001.py"
ARCHIVER_PATH = SCRIPTS / "archive_body_shop_robot_native_failed_import_v001.py"
IMPORTER_PATH = SCRIPTS / "import_body_shop_robot_native_v001.py"
VALIDATOR_PATH = SCRIPTS / "validate_body_shop_robot_native_v001.py"
RUNNER_PATH = SCRIPTS / "run_body_shop_robot_native_unreal_import_lane_v001.ps1"
DOC_PATH = ROOT / "Docs/BodyShop/BODYSHOP_ROBOT_NATIVE_UNREAL_IMPORT_LANE_v001.md"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def pinned_constant(text: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}\s*=\s*\"([0-9A-F]{{64}})\"", text, re.MULTILINE)
    if not match:
        raise AssertionError(f"missing 64-character {name} constant")
    return match.group(1)


class NativeRobotLaneContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8-sig"))
        cls.disposition = json.loads(DISPOSITION_PATH.read_text(encoding="utf-8-sig"))
        cls.disposition_freezer = DISPOSITION_FREEZER_PATH.read_text(encoding="utf-8")
        cls.archiver = ARCHIVER_PATH.read_text(encoding="utf-8")
        cls.importer = IMPORTER_PATH.read_text(encoding="utf-8")
        cls.validator = VALIDATOR_PATH.read_text(encoding="utf-8")
        cls.runner = RUNNER_PATH.read_text(encoding="utf-8")
        cls.document = DOC_PATH.read_text(encoding="utf-8")

    def test_corrected_high_elbow_source_is_exactly_pinned(self) -> None:
        source = self.baseline["source"]
        self.assertEqual(source["authority_hashes"], {
            "Audit/FROZEN_v001.json": "C11F95D4EC8B57C2D2D89AD63D44589C8A46FF0A6169DD37E733A25C0AA7C3CB",
            "MANIFEST_v001.json": "2797633628F0D295850A62319BB4D3E84ABA87BEB3C2B303C26FE7E17DBF1D4E",
            "Authority/LB_BodyShopRobotNative_v001.blend": "91DC4262FEA06C63B49A2E457ACB30F2E70576CEC92B2EA4D6FF2FC7F7C55E3B",
            "Audit/contact_fk_validation_v001.json": "29A0DCB9EF64191E7558B9E79562540CF1DFC98F1BC7D95CDAC25D3B4F6FA963",
            "Audit/geometry_inventory_v001.json": "8B334351E194F61033F269FBFB2BF45686AD4A3AC28C58536A04E2E3A1B61E82",
            "Audit/roundtrip_validation_v001.json": "FA784FB2D05781CDD5DA54D5E168225CB0D000A48E6F5CCCECB3A6E1F84CE9DB",
        })
        self.assertEqual(source["all_source_file_count"], 66)
        self.assertEqual(source["frozen_row_count"], 63)
        self.assertEqual(source["contact_summary"]["samples"], 18)
        self.assertEqual(source["contact_summary"]["passed"], 18)
        self.assertEqual(source["high_elbow_gate"]["gate"], "PASS")
        self.assertGreaterEqual(source["high_elbow_gate"]["minimum_elbow_rise_above_shoulder_cm"], 45.0)
        self.assertIn(
            "Audit/SupersededEvidence/pre_monotonic_blender_generation_stdout.log",
            source["freeze_excluded_but_baseline_pinned"],
        )

    def test_exact_eight_assets_twenty_four_fbx_and_strict_monotonic_uv_contract(self) -> None:
        assets = self.baseline["assets"]
        self.assertEqual(set(assets), {"Base", "CGun", "J1", "J2", "J3", "J4", "J5", "J6"})
        self.assertEqual(sum(len(row["lods"]) for row in assets.values()), 24)
        totals = [sum(asset["lods"][lod]["triangles"] for asset in assets.values()) for lod in range(3)]
        self.assertEqual(totals, [2628, 1964, 1356])
        self.assertEqual([row["triangles"] for row in assets["Base"]["lods"]], [468, 372, 228])
        for key, asset in assets.items():
            triangles = [row["triangles"] for row in asset["lods"]]
            self.assertGreater(triangles[0], triangles[1], key)
            self.assertGreater(triangles[1], triangles[2], key)
            self.assertEqual([row["source_uv_layers"] for row in asset["lods"]], [1, 1, 1])
            self.assertTrue(all(row["source_uv_layer_names"] == ["UVMap"] for row in asset["lods"]))
            self.assertEqual([row["lod"] for row in asset["lods"]], [0, 1, 2])
            self.assertEqual("/Tools/" in asset["package_path"], key == "CGun")

    def test_clean_import_contract_is_exact(self) -> None:
        contract = self.baseline["import_contract"]
        self.assertTrue(contract["fresh_destination_only"])
        self.assertEqual(contract["custom_lod_route"],
                         "LEGACY_FBX_WITH_INTERCHANGE_FEATURE_FLAG_TEMPORARILY_DISABLED")
        self.assertEqual(contract["interchange_fbx_cvar"], "Interchange.FeatureFlags.Import.FBX")
        self.assertTrue(contract["interchange_previous_value_captured_and_restored_in_finally"])
        self.assertEqual(contract["strict_per_asset_triangle_order"], "LOD0_GT_LOD1_GT_LOD2")
        self.assertEqual(contract["expected_uv_channels_per_lod"], 1)
        self.assertEqual(contract["lod_screen_sizes"], [1.0, 0.55, 0.25])
        self.assertFalse(contract["auto_compute_lod_screen_size"])
        self.assertEqual(contract["screen_size_persistence_passes"], 2)
        self.assertIn("AFTER_ALL_LOD_IMPORT", contract["screen_size_write_order"])
        self.assertIn("ZERO_SIMPLE", contract["collision"])

    def test_two_failed_runs_and_invalid_namespace_are_incident_bound(self) -> None:
        disposition = self.disposition
        self.assertEqual(disposition["status"],
                         "FROZEN__TWO_FAILED_RUNS_AND_EXACT_INVALID_NAMESPACE__ARCHIVE_AND_ATOMIC_MOVE__CLEAN_IMPORT_ONLY")
        self.assertEqual(len(disposition["failed_runs"]), 2)
        self.assertEqual([row["file_count"] for row in disposition["failed_runs"]], [7, 27])
        self.assertEqual([row["inventory_sha256"] for row in disposition["failed_runs"]], [
            "F25A877C4F0388F7468E848FFE60CD1D8F627D215FF219004E0FBD7CA6DE04BA",
            "5AD7F15B28E41B8FC4023B6E5EECD48ECBDC0E20951AC930B5C3E56029111C3E",
        ])
        self.assertEqual(disposition["invalid_namespace"]["package_count"], 8)
        self.assertEqual(len(disposition["diagnosis"]["installed_engine_evidence"]), 5)
        self.assertEqual(disposition["fresh_import"]["lod0_packages_created"], 8)
        self.assertEqual(disposition["fresh_import"]["legacy_custom_lods_appended"], 16)
        self.assertFalse(disposition["fresh_import"]["replace_existing"])
        self.assertFalse(disposition["fresh_import"]["reuse_existing_packages"])

    def test_protected_maps_config_source_saves_and_existing_assets_are_pinned(self) -> None:
        protected = self.baseline["protected"]
        self.assertEqual(protected["body_shop_map_sha256"], "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F")
        self.assertEqual(protected["press_v913_map_sha256"], "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6")
        names = {row["name"] for row in protected["groups"]}
        self.assertTrue({"config_tree", "body_shop_existing_content", "complete_source_tree",
                         "save_games", "weld_shop_existing_promoted_and_meshed_content"}.issubset(names))
        self.assertEqual(protected["file_count"], len(protected["files"]))
        self.assertEqual(len(protected["inventory_sha256"]), 64)
        by_path = {row["path"]: row for row in protected["files"]}
        self.assertEqual(
            by_path["Source/LineBossCarFactory/LBBodyShopPresentationPaletteTests.cpp"]["sha256"],
            "F65C920788A36C9717019FE7835CEB9BAA58ED00E4391EE193F09D634DE6CEA2",
        )

    def test_active_body_shop_rejects_old_runtime_but_legacy_scope_is_preserved(self) -> None:
        gate = self.baseline["active_body_shop_binding"]
        self.assertEqual(gate["status"], "PASS__ACTIVE_BODYSHOP_BINDINGS_USE_ONLY_NATIVE_V001_ROBOT_AND_OPEN_CGUN")
        self.assertEqual(gate["forbidden_matches"], [])
        self.assertEqual(gate["forbidden_old_runtime_token"], "WeldRobotRuntime_v001")
        self.assertEqual(len(gate["required_object_paths"]), 8)
        self.assertIn("Source/LineBossCarFactory/LBBodyWeldLineActor.cpp",
                      gate["archived_legacy_scope_not_semantically_rejected"])

    def test_baseline_and_disposition_hashes_are_cross_pinned(self) -> None:
        baseline_hash = sha256(BASELINE_PATH)
        disposition_hash = sha256(DISPOSITION_PATH)
        self.assertEqual(pinned_constant(self.disposition_freezer, "EXPECTED_BASELINE_SHA256"), baseline_hash)
        self.assertEqual(pinned_constant(self.importer, "EXPECTED_BASELINE_SHA256"), baseline_hash)
        self.assertEqual(pinned_constant(self.validator, "EXPECTED_BASELINE_SHA256"), baseline_hash)
        self.assertEqual(pinned_constant(self.archiver, "EXPECTED_CONTRACT_SHA256"), disposition_hash)
        self.assertEqual(pinned_constant(self.importer, "EXPECTED_DISPOSITION_CONTRACT_SHA256"), disposition_hash)
        self.assertEqual(pinned_constant(self.validator, "EXPECTED_DISPOSITION_CONTRACT_SHA256"), disposition_hash)

    def test_archiver_exclusively_copies_then_atomically_moves_without_delete(self) -> None:
        self.assertIn('destination.open("xb")', self.archiver)
        self.assertIn("DESTINATION.rename(moved_root)", self.archiver)
        self.assertGreaterEqual(self.archiver.count("verify_exact_recursive_file_inventory("), 5)
        self.assertIn("DISPOSITION_MODE_ENV", self.archiver)
        self.assertIn("exact destructive disposition acknowledgement", self.archiver)
        self.assertIn("verify_file(path, expected", self.archiver)
        self.assertNotIn("unlink(", self.archiver)
        self.assertNotIn("rmtree(", self.archiver)
        self.assertNotIn("Remove-Item", self.archiver)
        self.assertIn('"content_packages_deleted": 0', self.archiver)
        self.assertIn('"automatic_cleanup": "NOT_PERFORMED"', self.archiver)

    def test_importer_is_fresh_only_and_scopes_the_legacy_lod_cvar(self) -> None:
        self.assertIn("unreal.AssetImportTask()", self.importer)
        self.assertIn("unreal.FbxFactory()", self.importer)
        self.assertIn('"replace_existing": False', self.importer)
        self.assertIn('"reuse_existing_packages": False', self.importer)
        self.assertNotIn("prevalidate_recovery_mesh", self.importer)
        self.assertNotIn("verify_exact_partial_namespace", self.importer)
        self.assertNotIn("delete_asset(", self.importer)
        self.assertNotIn("load_level(", self.importer)
        self.assertIn("subsystem.import_lod", self.importer)
        self.assertIn("finally:", self.importer)
        self.assertIn("INTERCHANGE_FBX_CVAR", self.importer)
        self.assertIn("verify_exact_project_path_inventory", self.importer)
        self.assertIn('"existing_lods_reimported": []', self.importer)

    def test_screen_sizes_are_written_after_rebuilds_and_reapplied(self) -> None:
        nanite = self.importer.index("subsystem.set_nanite_settings")
        screen = self.importer.index("subsystem.set_lod_screen_sizes", nanite)
        self.assertLess(nanite, screen)
        self.assertEqual(self.importer.count("subsystem.set_lod_screen_sizes(mesh, screen_sizes)"), 2)
        self.assertIn("finish_all_asset_compilation()", self.importer[nanite:screen])
        self.assertIn('"no_build_after_final_set": True', self.importer)
        self.assertIn('"global_final_phase_after_all_mesh_preparation": True', self.importer)

    def test_validator_is_read_only_and_fresh_process_gated(self) -> None:
        for forbidden in ("save_loaded_asset(", "save_asset(", "delete_asset(", "load_level(", "save_current_level("):
            self.assertNotIn(forbidden, self.validator)
        self.assertIn("import_pid == os.getpid()", self.validator)
        self.assertIn("target_package_hashes_unchanged_by_fresh_load", self.validator)
        self.assertIn("strict_per_asset_triangle_monotonicity", self.validator)
        self.assertIn("exactly_one_uv_channel_on_all_24_lods", self.validator)
        self.assertIn("verify_clean_disposition_archive", self.validator)
        self.assertIn("verify_exact_project_path_inventory", self.validator)

    def test_runner_is_two_process_ps51_safe_no_ubt_and_fully_pinned(self) -> None:
        self.assertEqual(self.runner.count("Invoke-GuardedProcess $Editor"), 2)
        self.assertNotIn("Build.bat", self.runner)
        self.assertNotIn("UnrealEditor-Cmd.exe", self.runner)
        self.assertIn("-NoCompile", self.runner)
        self.assertIn("$null = $Process.Handle", self.runner)
        self.assertIn("$null -eq $ExitCode", self.runner)
        for label, path in (
            ("baseline", BASELINE_PATH), ("freezer", FREEZER_PATH),
            ("disposition_contract", DISPOSITION_PATH),
            ("disposition_freezer", DISPOSITION_FREEZER_PATH), ("archiver", ARCHIVER_PATH),
            ("importer", IMPORTER_PATH), ("validator", VALIDATOR_PATH),
        ):
            match = re.search(rf"^\s*{label}\s*=\s*'([0-9A-F]{{64}})'", self.runner, re.MULTILINE)
            self.assertIsNotNone(match, f"runner lacks final {label} hash")
            self.assertEqual(match.group(1), sha256(path))

    def test_document_contains_final_hashes_and_exact_acknowledgement(self) -> None:
        for path in (BASELINE_PATH, FREEZER_PATH, DISPOSITION_PATH, DISPOSITION_FREEZER_PATH,
                     ARCHIVER_PATH, IMPORTER_PATH, VALIDATOR_PATH, RUNNER_PATH):
            self.assertIn(sha256(path), self.document)
        self.assertIn(
            "ARCHIVE_TWO_FAILED_RUNS_MOVE_INVALID_NAMESPACE_AND_CLEAN_IMPORT_"
            "HIGH_ELBOW_MONOTONIC_V001_ONCE",
            self.document,
        )
        self.assertIn("NO_CLEAN_IMPORT_UE_RUN_YET", self.document)


if __name__ == "__main__":
    unittest.main()
