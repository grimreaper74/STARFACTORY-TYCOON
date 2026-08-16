"""Offline contract tests for the final native support-kit import lane v002."""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = ROOT / "Scripts"
BASELINE_PATH = SCRIPTS / "body_shop_support_kit_native_unreal_import_baseline_v002.json"
FREEZER_PATH = SCRIPTS / "freeze_body_shop_support_kit_native_unreal_import_baseline_v002.py"
IMPORTER_PATH = SCRIPTS / "import_body_shop_support_kit_native_v001_lane_v002.py"
VALIDATOR_PATH = SCRIPTS / "validate_body_shop_support_kit_native_v001_lane_v002.py"
RUNNER_PATH = SCRIPTS / "run_body_shop_support_kit_native_unreal_import_lane_v002.ps1"
DOC_PATH = ROOT / "Docs/BodyShop/BODYSHOP_SUPPORT_KIT_NATIVE_UNREAL_IMPORT_LANE_v002.md"

PROVISIONAL_V001_HASHES = {
    SCRIPTS / "freeze_body_shop_support_kit_native_unreal_import_baseline_v001.py":
        "5F0783286A5F32E8740AE4BC0049021BAB73F41FCC1B7DD340ACE55BA2E1D27B",
    SCRIPTS / "import_body_shop_support_kit_native_v001.py":
        "A911433021C50D78D2CDA26757468A3490A9CE0AAE43667446B124E13741147A",
    SCRIPTS / "validate_body_shop_support_kit_native_v001.py":
        "9E6ECAE2B978686585CD1E5215957F2555181131C3ED36BFE56E75D63FAB8ADC",
    SCRIPTS / "run_body_shop_support_kit_native_unreal_import_lane_v001.ps1":
        "F1E9DA58655345ABF65DFCAC5FCB764CE5855D8826BA2C064F145CDE5C5AF631",
    SCRIPTS / "tests/test_body_shop_support_kit_native_unreal_import_lane_v001.py":
        "8171FDC3200D1C3F184C9BCB800F894B4B3BA5B95768790AC8685E7691574A74",
    ROOT / "Docs/BodyShop/BODYSHOP_SUPPORT_KIT_NATIVE_UNREAL_IMPORT_LANE_v001.md":
        "B006CB6D824D64F308C8FE21C63460E05846F47AAB68A7F49A5F5E6B3ABF64E1",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def pinned_constant(text: str, name: str) -> str:
    match = re.search(rf'^{re.escape(name)}\s*=\s*"([0-9A-F]{{64}})"', text, re.MULTILINE)
    if not match:
        raise AssertionError(f"missing 64-character {name} constant")
    return match.group(1)


class NativeSupportKitLaneV002ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8-sig"))
        cls.freezer = FREEZER_PATH.read_text(encoding="utf-8")
        cls.importer = IMPORTER_PATH.read_text(encoding="utf-8")
        cls.validator = VALIDATOR_PATH.read_text(encoding="utf-8")
        cls.runner = RUNNER_PATH.read_text(encoding="utf-8")
        cls.document = DOC_PATH.read_text(encoding="utf-8")

    def test_disabled_provisional_v001_lane_is_byte_preserved(self) -> None:
        for path, expected in PROVISIONAL_V001_HASHES.items():
            self.assertTrue(path.is_file(), str(path))
            self.assertEqual(sha256(path), expected, str(path))
        self.assertFalse((SCRIPTS / "body_shop_support_kit_native_unreal_import_baseline_v001.json").exists())

    def test_frozen_source_authorities_are_hard_pinned(self) -> None:
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

    def test_baseline_identity_and_all_lane_pins_are_real(self) -> None:
        actual = sha256(BASELINE_PATH)
        self.assertEqual(
            self.baseline["$schema"],
            "lineboss/bodyshop-support-kit-native-v001-unreal-import-baseline/v2",
        )
        self.assertEqual(
            self.baseline["status"],
            "FROZEN__BODYSHOP_SUPPORT_KIT_NATIVE_V001_UNREAL_IMPORT_BASELINE_V002",
        )
        self.assertEqual(pinned_constant(self.importer, "EXPECTED_BASELINE_SHA256"), actual)
        self.assertEqual(pinned_constant(self.validator, "EXPECTED_BASELINE_SHA256"), actual)
        self.assertNotEqual(actual, "0" * 64)

    def test_freezer_is_offline_one_output_and_destination_absence_gated(self) -> None:
        self.assertNotIn("import unreal", self.freezer)
        self.assertNotIn("subprocess", self.freezer)
        self.assertNotIn("UnrealEditor", self.freezer)
        self.assertIn("OUTPUT.write_text", self.freezer)
        self.assertNotIn("unlink(", self.freezer)
        self.assertIn("refusing to overwrite existing baseline", self.freezer)
        self.assertIn("isolated destination already exists", self.freezer)

    def test_exact_12_assets_three_lods_monotonic_uv_material_bounds_and_pivots(self) -> None:
        baseline = self.baseline
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
        self.assertTrue(baseline["source"]["strict_per_asset_monotonic_triangles"])
        self.assertEqual(baseline["source"]["exact_uv_layers_per_lod"], ["UVMap"])
        for key, spec in baseline["assets"].items():
            lods = spec["lods"]
            triangles = [int(row["triangles"]) for row in lods]
            self.assertEqual(spec["triangle_chain"], triangles, key)
            self.assertTrue(spec["strict_monotonic_triangles"], key)
            self.assertGreater(triangles[0], triangles[1], key)
            self.assertGreater(triangles[1], triangles[2], key)
            self.assertGreater(triangles[2], 0, key)
            self.assertEqual([row["lod"] for row in lods], [0, 1, 2], key)
            for row in lods:
                self.assertEqual(row["uv_layers"], ["UVMap"], key)
                self.assertEqual(row["transform"], {
                    "location": [0.0, 0.0, 0.0],
                    "rotation_euler": [0.0, 0.0, 0.0],
                    "scale": [1.0, 1.0, 1.0],
                })
                bounds = row["expected_unreal_bounds"]
                self.assertAlmostEqual(bounds["minimum_cm"][2], 0.0)
                self.assertAlmostEqual(bounds["minimum_cm"][0] + bounds["maximum_cm"][0], 0.0)
                self.assertAlmostEqual(bounds["minimum_cm"][1] + bounds["maximum_cm"][1], 0.0)
                self.assertTrue(row["material_slots"])
                self.assertEqual(len(row["material_slots"]), len(set(row["material_slots"])))

    def test_exact_protected_authorities_and_native_robot_packages(self) -> None:
        protected = self.baseline["protected"]
        groups = {row["name"] for row in protected["groups"]}
        self.assertEqual(groups, {
            "project_descriptor", "complete_source_tree", "complete_config_tree",
            "body_shop_map", "press_v913_map", "restored_press_map",
            "current_native_robot_packages", "all_existing_content_outside_new_support_namespace",
            "campaign_save_games",
        })
        self.assertEqual(
            protected["press_v913_map_sha256"],
            "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
        )
        self.assertEqual(
            protected["restored_press_map_sha256"],
            "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5",
        )
        self.assertEqual(
            protected["body_shop_map_sha256"],
            "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F",
        )
        robots = protected["current_native_robot_packages"]
        self.assertEqual(len(robots), 8)
        self.assertTrue(all(path.endswith(".uasset") for path in robots))
        self.assertTrue(all(row["sha256"] and int(row["bytes"]) > 0 for row in robots.values()))

    def test_import_contract_is_exact_and_deterministic(self) -> None:
        contract = self.baseline["import_contract"]
        self.assertEqual(contract["lod_screen_sizes"], [1.0, 0.45, 0.18])
        self.assertEqual(contract["screen_size_persistence_passes"], 2)
        self.assertFalse(contract["auto_compute_lod_screen_size"])
        self.assertFalse(contract["import_materials"])
        self.assertFalse(contract["import_textures"])
        self.assertFalse(contract["auto_generate_collision"])
        self.assertFalse(contract["nanite_enabled"])
        self.assertEqual(contract["expected_uv_channels_per_lod"], 1)
        self.assertEqual(len(contract["material_bindings"]), 9)
        for spec in self.baseline["assets"].values():
            self.assertEqual(spec["collision"]["simple_count"], 1)
            self.assertEqual(spec["collision"]["convex_count"], 0)

    def test_importer_is_pristine_namespace_only_non_destructive_and_legacy_lod_guarded(self) -> None:
        self.assertIn('DEST = "/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v001"', self.importer)
        self.assertIn('"replace_existing": False', self.importer)
        self.assertIn('"replace_existing_settings": False', self.importer)
        self.assertNotIn('"replace_existing": True', self.importer)
        self.assertNotIn("delete_asset(", self.importer)
        self.assertNotIn("delete_directory(", self.importer)
        self.assertNotIn("load_level(", self.importer)
        self.assertNotIn("save_current_level(", self.importer)
        self.assertIn('"factory": unreal.FbxFactory()', self.importer)
        self.assertIn('INTERCHANGE_FBX_CVAR = "Interchange.FeatureFlags.Import.FBX"', self.importer)
        self.assertIn("custom_lods_requested\": 24", self.importer)
        self.assertIn('f"{INTERCHANGE_FBX_CVAR} {previous}"', self.importer)
        self.assertIn("restore_attempted_in_finally", self.importer)
        self.assertIn("PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW", self.importer)

    def test_importer_and_validator_cover_every_runtime_mesh_contract(self) -> None:
        for text in (self.importer, self.validator):
            self.assertIn("strict monotonic triangle", text)
            self.assertIn("UV channel", text)
            self.assertIn("floor-centred pivot", text)
            self.assertIn("section/material", text)
            self.assertIn("collision/Nanite", text)
            self.assertIn("lod_screen_sizes", text)
            self.assertIn("material_bindings", text)
        self.assertIn("subsystem.import_lod", self.importer)
        self.assertEqual(self.importer.count("subsystem.set_lod_screen_sizes(mesh, screen_sizes)"), 2)
        self.assertIn("ScriptingCollisionShapeType.BOX", self.importer)
        self.assertIn("CTF_USE_DEFAULT", self.importer)
        self.assertIn('"no_build_after_final_set": True', self.importer)

    def test_validator_is_independent_read_only_and_full_hash_gated(self) -> None:
        for forbidden in (
            "save_loaded_asset(", "save_asset(", "delete_asset(", "delete_directory(",
            "load_level(", "save_current_level(", "AssetImportTask(", "import_lod(",
        ):
            self.assertNotIn(forbidden, self.validator)
        self.assertIn("import_pid == os.getpid()", self.validator)
        self.assertIn("verify_protected_full", self.validator)
        self.assertIn("target_after != target_before", self.validator)
        self.assertIn("strict_per_asset_monotonic_triangles_persisted", self.validator)
        self.assertIn("exact_one_uv_channel_per_lod_persisted", self.validator)

    def test_runner_is_two_fresh_editor_processes_no_ubt_and_ps51_safe(self) -> None:
        self.assertEqual(self.runner.count("Invoke-GuardedProcess $Editor"), 2)
        self.assertNotIn("Build.bat", self.runner)
        self.assertNotRegex(self.runner, r"(?im)^\s*(?:&|Start-Process).*UnrealBuildTool")
        self.assertNotIn("UnrealEditor-Cmd.exe", self.runner)
        self.assertIn("-NoCompile", self.runner)
        self.assertIn("$null = $Process.Handle", self.runner)
        self.assertIn("$Process.Refresh()", self.runner)
        self.assertIn("$null -eq $ExitCode", self.runner)
        self.assertIn("ShaderCompileWorker", self.runner)
        self.assertIn("refuses every pre-existing result (PASS or FAIL)", self.runner)
        self.assertIn("IMPORT_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V001_BASELINE_V002_ONCE", self.runner)

    def test_runner_hashes_match_all_frozen_lane_inputs(self) -> None:
        paths = {
            "baseline": BASELINE_PATH,
            "freezer": FREEZER_PATH,
            "importer": IMPORTER_PATH,
            "validator": VALIDATOR_PATH,
        }
        for label, path in paths.items():
            match = re.search(rf"^\s*{label}\s*=\s*'([0-9A-F]{{64}})'", self.runner, re.MULTILINE)
            self.assertIsNotNone(match, f"runner lacks {label} hash")
            self.assertEqual(match.group(1), sha256(path), label)

    def test_documented_supersession_scope_and_one_shot_command(self) -> None:
        self.assertIn("v001 provisional lane remains byte-for-byte preserved", self.document)
        self.assertIn("/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v001", self.document)
        self.assertIn("exactly 12", self.document)
        self.assertIn("36 FBX", self.document)
        self.assertIn("Press v913", self.document)
        self.assertIn("restored full Press map", self.document)
        self.assertIn("eight current native robot packages", self.document)
        self.assertIn("IMPORT_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V001_BASELINE_V002_ONCE", self.document)
        self.assertIn("NO_UNREAL_OR_UBT_EXECUTED_DURING_V002_FINALISATION", self.document)


if __name__ == "__main__":
    unittest.main()
