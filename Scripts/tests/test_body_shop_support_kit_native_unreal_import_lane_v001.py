"""Offline contract tests for the guarded native support-kit import lane.

The suite deliberately supports the pre-freeze checkpoint: when the protected
baseline is absent it proves the lane remains cryptographically disabled.  Once
the baseline is cut, those same tests require real SHA-256 pins everywhere.
"""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = ROOT / "Scripts"
BASELINE_PATH = SCRIPTS / "body_shop_support_kit_native_unreal_import_baseline_v001.json"
FREEZER_PATH = SCRIPTS / "freeze_body_shop_support_kit_native_unreal_import_baseline_v001.py"
IMPORTER_PATH = SCRIPTS / "import_body_shop_support_kit_native_v001.py"
VALIDATOR_PATH = SCRIPTS / "validate_body_shop_support_kit_native_v001.py"
RUNNER_PATH = SCRIPTS / "run_body_shop_support_kit_native_unreal_import_lane_v001.ps1"
DOC_PATH = ROOT / "Docs/BodyShop/BODYSHOP_SUPPORT_KIT_NATIVE_UNREAL_IMPORT_LANE_v001.md"
ZERO_HASH = "0" * 64


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def pinned_constant(text: str, name: str) -> str:
    match = re.search(rf'^{re.escape(name)}\s*=\s*"([0-9A-F]{{64}})"', text, re.MULTILINE)
    if not match:
        raise AssertionError(f"missing 64-character {name} constant")
    return match.group(1)


class NativeSupportKitLaneContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = (
            json.loads(BASELINE_PATH.read_text(encoding="utf-8-sig"))
            if BASELINE_PATH.is_file() else None
        )
        cls.freezer = FREEZER_PATH.read_text(encoding="utf-8")
        cls.importer = IMPORTER_PATH.read_text(encoding="utf-8")
        cls.validator = VALIDATOR_PATH.read_text(encoding="utf-8")
        cls.runner = RUNNER_PATH.read_text(encoding="utf-8")
        cls.document = DOC_PATH.read_text(encoding="utf-8")

    def require_baseline(self) -> dict:
        if self.baseline is None:
            self.skipTest("protected baseline intentionally not cut at provisional checkpoint")
        return self.baseline

    def test_frozen_source_authorities_are_hard_pinned_in_freezer(self) -> None:
        expected = {
            "A4E4BF52C46F93EF5A084A708D94A7B2B920ABDC702CF655B5A8569920A9AD6F",
            "F0EFB621EC94C0D5E4806487576E1C6AE13EE8158A68A8D445052D6F33C700EC",
            "5D69E9F6D4770475BC91AD1EAC61F528EEA3F7D8C4A3979BFF6F92B5ACC60F18",
            "1DC636BD128CC5CA37161638F92E63DA566BE7F14A293833280643F9A4441A67",
            "8933C5A746070FEB6B628786E7BD52543D96D8162CCC3B27D2BF37618D098A4A",
            "FD78070F1E68950241035ED8B4AFDA79BD94E10F43759EBCB712AA674CB3A627",
        }
        self.assertTrue(all(value in self.freezer for value in expected))
        self.assertIn("expected 90 files", self.freezer)
        self.assertIn("len(frozen_rows) != 89", self.freezer)
        self.assertIn("exports_passed", self.freezer)
        self.assertIn("!= 72", self.freezer)

    def test_provisional_checkpoint_is_cryptographically_disabled(self) -> None:
        importer_pin = pinned_constant(self.importer, "EXPECTED_BASELINE_SHA256")
        validator_pin = pinned_constant(self.validator, "EXPECTED_BASELINE_SHA256")
        runner_baseline = re.search(
            r"^\s*baseline\s*=\s*'([0-9A-F]{64})'", self.runner, re.MULTILINE
        ).group(1)
        if self.baseline is None:
            self.assertEqual(importer_pin, ZERO_HASH)
            self.assertEqual(validator_pin, ZERO_HASH)
            self.assertEqual(runner_baseline, ZERO_HASH)
            self.assertIn("NOT_RUNNABLE__PROTECTED_BASELINE_NOT_CUT", self.document)
        else:
            actual = sha256(BASELINE_PATH)
            self.assertNotEqual(actual, ZERO_HASH)
            self.assertEqual(importer_pin, actual)
            self.assertEqual(validator_pin, actual)
            self.assertEqual(runner_baseline, actual)

    def test_freezer_is_offline_and_single_output_scoped(self) -> None:
        self.assertNotIn("import unreal", self.freezer)
        self.assertNotIn("subprocess", self.freezer)
        self.assertNotIn("UnrealEditor", self.freezer)
        self.assertIn("OUTPUT.write_text", self.freezer)
        self.assertNotIn("unlink(", self.freezer)
        self.assertIn("refusing to overwrite existing baseline", self.freezer)

    def test_importer_is_pristine_namespace_only_and_non_destructive(self) -> None:
        self.assertIn('DEST = "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v001"', self.importer)
        self.assertIn('"replace_existing": False', self.importer)
        self.assertIn('"replace_existing_settings": False', self.importer)
        self.assertNotIn('"replace_existing": True', self.importer)
        self.assertNotIn("delete_asset(", self.importer)
        self.assertNotIn("delete_directory(", self.importer)
        self.assertNotIn("load_level(", self.importer)
        self.assertNotIn("save_current_level(", self.importer)
        self.assertIn("v001 refuses every pre-existing lane result", self.importer)
        self.assertIn("PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW", self.importer)

    def test_exact_lod_material_pivot_and_collision_operations_are_guarded(self) -> None:
        self.assertIn("subsystem.import_lod", self.importer)
        self.assertEqual(self.importer.count("subsystem.set_lod_screen_sizes(mesh, screen_sizes)"), 2)
        nanite = self.importer.index("subsystem.set_nanite_settings")
        collision = self.importer.index("add_simple_collisions", nanite)
        screen = self.importer.index("subsystem.set_lod_screen_sizes", collision)
        self.assertLess(nanite, collision)
        self.assertLess(collision, screen)
        self.assertIn("ScriptingCollisionShapeType.BOX", self.importer)
        self.assertIn("CTF_USE_DEFAULT", self.importer)
        self.assertIn("floor-centred pivot contract drift", self.importer)
        self.assertIn("per-LOD section/material order drift", self.importer)
        self.assertIn('"no_build_after_final_set": True', self.importer)

    def test_validator_is_independent_read_only_and_fresh_process_gated(self) -> None:
        for forbidden in (
            "save_loaded_asset(", "save_asset(", "delete_asset(", "delete_directory(",
            "load_level(", "save_current_level(", "AssetImportTask(", "import_lod(",
        ):
            self.assertNotIn(forbidden, self.validator)
        self.assertIn("import_pid == os.getpid()", self.validator)
        self.assertIn("verify_protected_full", self.validator)
        self.assertIn("target_after != target_before", self.validator)
        self.assertIn("manual_lod_screen_sizes_persisted_after_fresh_process_load", self.validator)
        self.assertIn("floor_centred_pivots_and_dimensions_persisted", self.validator)

    def test_runner_is_two_fresh_editor_processes_no_ubt_and_ps51_safe(self) -> None:
        self.assertEqual(self.runner.count("Invoke-GuardedProcess $Editor"), 2)
        self.assertNotIn("Build.bat", self.runner)
        self.assertNotRegex(self.runner, r"(?im)^\s*(?:&|Start-Process).*UnrealBuildTool")
        self.assertNotIn("UnrealEditor-Cmd.exe", self.runner)
        self.assertIn("-NoCompile", self.runner)
        self.assertIn("$null = $Process.Handle", self.runner)
        self.assertIn("$Process.Refresh()", self.runner)
        self.assertIn("$null -eq $ExitCode", self.runner)
        self.assertIn("refuses every pre-existing result (PASS or FAIL)", self.runner)
        self.assertIn("IMPORT_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V001_ONCE", self.runner)

    def test_frozen_baseline_exact_assets_and_protection(self) -> None:
        baseline = self.require_baseline()
        expected_keys = {
            "PanelStillageEmpty", "PanelStillageFull", "EmptyReturnCart",
            "ComponentServicePallet", "SmallPartsCrate", "SmallPartsBin",
            "ElectricalCabinet", "HMIPedestal", "GuardPanel2m", "GuardGate2m",
            "UtilityPedestal", "ExtractionPedestal",
        }
        self.assertEqual(set(baseline["assets"]), expected_keys)
        self.assertEqual(sum(len(row["lods"]) for row in baseline["assets"].values()), 36)
        self.assertEqual(len({row["package_path"] for row in baseline["assets"].values()}), 12)
        self.assertEqual(baseline["source"]["triangle_totals"], {
            "LOD0": 20408, "LOD1": 7580, "LOD2": 1780,
        })
        self.assertEqual(baseline["source"]["all_source_file_count"], 90)
        self.assertEqual(baseline["source"]["frozen_row_count"], 89)
        groups = {row["name"] for row in baseline["protected"]["groups"]}
        self.assertEqual(groups, {
            "project_descriptor", "current_source_tree", "current_config_tree",
            "all_existing_content_outside_new_support_namespace", "campaign_save_games",
        })
        self.assertEqual(
            baseline["protected"]["press_v913_map_sha256"],
            "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
        )
        self.assertEqual(
            baseline["protected"]["body_shop_map_sha256"],
            "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F",
        )

    def test_frozen_baseline_import_contract(self) -> None:
        baseline = self.require_baseline()
        contract = baseline["import_contract"]
        self.assertEqual(contract["lod_screen_sizes"], [1.0, 0.45, 0.18])
        self.assertEqual(contract["screen_size_persistence_passes"], 2)
        self.assertFalse(contract["auto_compute_lod_screen_size"])
        self.assertFalse(contract["import_materials"])
        self.assertFalse(contract["import_textures"])
        self.assertFalse(contract["auto_generate_collision"])
        self.assertEqual(len(contract["material_bindings"]), 9)
        self.assertEqual(contract["collision"], "ONE_DETERMINISTIC_AABB_BOX_PER_ASSET__USE_DEFAULT")
        for spec in baseline["assets"].values():
            self.assertEqual(spec["collision"]["simple_count"], 1)
            self.assertEqual(spec["collision"]["convex_count"], 0)
            self.assertEqual([lod["lod"] for lod in spec["lods"]], [0, 1, 2])
            self.assertTrue(all(lod["source"].lower().endswith(".fbx") for lod in spec["lods"]))
            for lod in spec["lods"]:
                self.assertAlmostEqual(lod["expected_unreal_bounds"]["minimum_cm"][2], 0.0)

    def test_final_runner_hashes_match_all_lane_inputs(self) -> None:
        if self.baseline is None:
            for label in ("baseline", "freezer", "importer", "validator"):
                match = re.search(rf"^\s*{label}\s*=\s*'([0-9A-F]{{64}})'", self.runner, re.MULTILINE)
                self.assertIsNotNone(match)
                self.assertEqual(match.group(1), ZERO_HASH)
            return
        paths = {
            "baseline": BASELINE_PATH,
            "freezer": FREEZER_PATH,
            "importer": IMPORTER_PATH,
            "validator": VALIDATOR_PATH,
        }
        for label, path in paths.items():
            match = re.search(rf"^\s*{label}\s*=\s*'([0-9A-F]{{64}})'", self.runner, re.MULTILINE)
            self.assertIsNotNone(match, f"runner lacks {label} hash")
            self.assertEqual(match.group(1), sha256(path))

    def test_documented_scope_and_no_execution_checkpoint(self) -> None:
        self.assertIn("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v001", self.document)
        self.assertIn("exactly 12", self.document)
        self.assertIn("36 FBX", self.document)
        self.assertIn("IMPORT_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V001_ONCE", self.document)
        self.assertIn("NO_SUPPORT_KIT_UNREAL_RUN_YET", self.document)


if __name__ == "__main__":
    unittest.main()
