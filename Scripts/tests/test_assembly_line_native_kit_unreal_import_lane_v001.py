"""Offline/static contract tests for the one-shot native Assembly-kit intake lane."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = ROOT / "Scripts"
BASELINE = SCRIPTS / "assembly_line_native_kit_unreal_import_baseline_v001.json"
FREEZER = SCRIPTS / "freeze_assembly_line_native_kit_unreal_import_baseline_v001.py"
COMMON = SCRIPTS / "assembly_line_native_kit_unreal_runtime_v001.py"
IMPORTER = SCRIPTS / "import_assembly_line_native_kit_v001.py"
VALIDATOR = SCRIPTS / "validate_assembly_line_native_kit_v001.py"
RUNNER = SCRIPTS / "run_assembly_line_native_kit_unreal_import_lane_v001.ps1"
DOC = ROOT / "Docs/AssemblyShop/ASSEMBLY_LINE_NATIVE_KIT_UNREAL_IMPORT_LANE_v001.md"
TARGET = ROOT / "Content/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001"
AUDITS = ROOT / "Saved/Audits/AssemblyShop/AssemblyLineNativeKit_v001/UnrealImportLane_v001"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class AssemblyNativeKitLaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = json.loads(BASELINE.read_text(encoding="utf-8-sig"))
        cls.freezer = FREEZER.read_text(encoding="utf-8")
        cls.common = COMMON.read_text(encoding="utf-8")
        cls.importer = IMPORTER.read_text(encoding="utf-8")
        cls.validator = VALIDATOR.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_python_parsers(self) -> None:
        for path in (FREEZER, COMMON, IMPORTER, VALIDATOR):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))

    def test_frozen_identity_and_authorities(self) -> None:
        baseline = self.baseline
        self.assertEqual(baseline["$schema"], "lineboss/assembly-line-native-kit-v001/unreal-import-baseline/v1")
        self.assertEqual(baseline["status"], "FROZEN__ASSEMBLY_LINE_NATIVE_KIT_V001_UNREAL_IMPORT_BASELINE_V001")
        self.assertEqual(baseline["source"]["file_count"], 62)
        self.assertEqual(baseline["source"]["asset_count"], 8)
        self.assertEqual(baseline["source"]["lod_record_count"], 24)
        self.assertEqual(baseline["source"]["roundtrip_record_count"], 48)
        self.assertEqual(baseline["source"]["triangle_totals"], {"LOD0": 10188, "LOD1": 4512, "LOD2": 1652})
        for rel, expected in baseline["source"]["authorities"].items():
            self.assertEqual(sha256(ROOT / baseline["source"]["root"] / rel), expected, rel)

    def test_exact_assets_lods_uv_bounds_pivots_and_material_semantics(self) -> None:
        expected = {"SkilletCarrier", "SequencedPartsCart", "WheelTireRack", "CockpitInstallAssist",
                    "HeavyMarriageGantry", "ErgonomicLiftPlatform", "WheelAlignmentBed", "EOLInspectionArch"}
        self.assertEqual(set(self.baseline["assets"]), expected)
        self.assertEqual(sum(len(row["lods"]) for row in self.baseline["assets"].values()), 24)
        self.assertEqual(len({row["package_path"] for row in self.baseline["assets"].values()}), 8)
        for key, spec in self.baseline["assets"].items():
            chain = [row["triangles"] for row in spec["lods"]]
            self.assertEqual(chain, spec["triangle_chain"], key)
            self.assertGreater(chain[0], chain[1], key)
            self.assertGreater(chain[1], chain[2], key)
            for lod, row in enumerate(spec["lods"]):
                self.assertEqual(row["lod"], lod)
                self.assertEqual(row["uv_layers"], 1)
                self.assertTrue(row["material_slots"])
                self.assertEqual(len(row["material_slots"]), len(set(row["material_slots"])))
                self.assertEqual(row["expected_unreal_bounds"]["pivot_cm"], [0.0, 0.0, 0.0])

    def test_per_asset_collision_is_suitable_and_nanite_manual_lod_policy(self) -> None:
        complex_assets = {key for key, value in self.baseline["assets"].items()
                          if value["collision"]["mode"] == "COMPLEX_AS_SIMPLE"}
        self.assertEqual(complex_assets, {"CockpitInstallAssist", "HeavyMarriageGantry", "EOLInspectionArch"})
        for key, value in self.baseline["assets"].items():
            collision = value["collision"]
            if key in complex_assets:
                self.assertEqual((collision["simple_count"], collision["convex_count"]), (0, 0))
            else:
                self.assertEqual((collision["simple_count"], collision["convex_count"]), (1, 0))
        contract = self.baseline["import_contract"]
        self.assertEqual(contract["lod_screen_sizes"], [1.0, 0.45, 0.18])
        self.assertFalse(contract["nanite_enabled"])
        self.assertFalse(contract["auto_compute_lod_screen_size"])
        self.assertFalse(contract["import_materials"])
        self.assertFalse(contract["import_textures"])
        self.assertEqual(contract["custom_lods_requested"], 16)

    def test_complete_project_protection_and_exact_maps(self) -> None:
        groups = {row["name"] for row in self.baseline["protected"]["groups"]}
        self.assertTrue({"complete_source_tree", "complete_config_tree", "campaign_save_games",
                         "all_existing_content_outside_target_namespace", "exact_press_v913_map",
                         "exact_restored_press_map", "exact_body_map", "exact_paint_map",
                         "exact_one_factory_map"}.issubset(groups))
        expected = {
            "press_v913": "26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6",
            "restored_press": "D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5",
            "body": "8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F",
            "paint": "2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069",
            "one_factory": "750FB6C93BBE8220467F5BF9656C4017F0D9E2706B35C413460AF20CEB9EB682",
        }
        self.assertEqual({key: row["sha256"] for key, row in self.baseline["protected"]["maps"].items()}, expected)

    def test_freezer_and_lane_are_fresh_only_and_non_destructive(self) -> None:
        self.assertNotIn("import unreal", self.freezer)
        self.assertNotIn("subprocess", self.freezer)
        self.assertIn("refusing to overwrite existing baseline", self.freezer)
        self.assertIn("PASS__FULL_SOURCE_AND_PROTECTED_BASELINE_REVERIFY", self.freezer)
        self.assertFalse(TARGET.exists())
        self.assertFalse(AUDITS.exists())
        for forbidden in ("delete_asset(", "delete_directory(", "load_level(", "save_current_level(",
                          '"replace_existing": True', '"replace_existing_settings": True'):
            self.assertNotIn(forbidden, self.importer)
        self.assertIn('"replace_existing": False', self.importer)
        self.assertIn("subsystem.import_lod", self.importer)
        self.assertIn("finally:", self.importer)
        self.assertIn("restore_attempted_in_finally", self.importer)
        self.assertIn("PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW", self.importer)

    def test_validator_is_independent_read_only_full_hash_gate(self) -> None:
        for forbidden in ("save_loaded_asset(", "save_asset(", "delete_asset(", "delete_directory(",
                          "AssetImportTask(", "import_lod(", "load_level(", "save_current_level("):
            self.assertNotIn(forbidden, self.validator)
        self.assertIn("import_pid == os.getpid()", self.validator)
        self.assertIn("full_hash=True", self.validator)
        self.assertIn("target_after != target_before", self.validator)

    def test_runtime_and_runner_pin_real_baseline_and_two_fresh_full_editor_processes(self) -> None:
        baseline_hash = sha256(BASELINE)
        self.assertIn(f'EXPECTED_BASELINE_SHA256 = "{baseline_hash}"', self.common)
        self.assertEqual(self.runner.count("Invoke-GuardedProcess $Editor"), 2)
        self.assertIn("-NoCompile", self.runner)
        self.assertIn("-NullRHI", self.runner)
        self.assertIn("$null = $Process.Handle", self.runner)
        self.assertIn("$Process.Refresh()", self.runner)
        self.assertIn("$null -eq $ExitCode", self.runner)
        self.assertNotIn("Build.bat", self.runner)
        paths = {"baseline": BASELINE, "freezer": FREEZER, "common": COMMON,
                 "importer": IMPORTER, "validator": VALIDATOR}
        for label, path in paths.items():
            match = re.search(rf"^\s*{label}\s*=\s*'([0-9A-F]{{64}})'", self.runner, re.MULTILINE)
            self.assertIsNotNone(match, label)
            self.assertEqual(match.group(1), sha256(path), label)

    def test_documented_static_state_and_exact_one_shot_command(self) -> None:
        self.assertIn("Static-only preparation complete", self.doc)
        self.assertIn("exactly 8 StaticMesh packages", self.doc)
        self.assertIn("24 authored LODs", self.doc)
        self.assertIn("No Unreal or UBT process was launched", self.doc)
        self.assertIn("IMPORT_FROZEN_ASSEMBLY_LINE_NATIVE_KIT_V001_BASELINE_V001_ONCE", self.doc)


if __name__ == "__main__":
    unittest.main()
