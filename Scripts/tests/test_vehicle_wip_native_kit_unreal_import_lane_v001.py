from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = ROOT / "Scripts"
CONTRACT = SCRIPTS / "vehicle_wip_native_kit_unreal_import_contract_v001.json"
BASELINE = SCRIPTS / "vehicle_wip_native_kit_unreal_import_baseline_v001.json"
BASELINE_SHA = SCRIPTS / "vehicle_wip_native_kit_unreal_import_baseline_v001.sha256"
FREEZER = SCRIPTS / "prepare_vehicle_wip_native_kit_unreal_import_baseline_v001.py"
COMMON = SCRIPTS / "vehicle_wip_native_kit_unreal_runtime_v001.py"
IMPORTER = SCRIPTS / "import_vehicle_wip_native_kit_v001.py"
VALIDATOR = SCRIPTS / "validate_vehicle_wip_native_kit_v001.py"
RUNNER = SCRIPTS / "run_vehicle_wip_native_kit_unreal_import_lane_v001.ps1"
DOC = ROOT / "Docs/VEHICLE_WIP_NATIVE_KIT_UNREAL_IMPORT_LANE_v001.md"
DEST = ROOT / "Content/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001"
AUDITS = ROOT / "Saved/Audits/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001/UnrealImportLane_v001"
EXPECTED_CONTRACT_SHA256 = "87D9FD32964CC0AD0F4AA52CC6F27A0E23BFDA23A18B2F714E6E2807CCA9684D"


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest().upper()


class VehicleWIPNativeUnrealLaneStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        cls.freezer = FREEZER.read_text(encoding="utf-8")
        cls.common = COMMON.read_text(encoding="utf-8")
        cls.importer = IMPORTER.read_text(encoding="utf-8")
        cls.validator = VALIDATOR.read_text(encoding="utf-8")
        cls.runner = RUNNER.read_text(encoding="utf-8")
        cls.doc = DOC.read_text(encoding="utf-8")

    def test_static_contract_is_exact_clean_room_source_only(self) -> None:
        self.assertEqual(sha256(CONTRACT), EXPECTED_CONTRACT_SHA256)
        self.assertEqual(self.contract["$schema"], "lineboss/vehicle-wip-native-kit-v001/unreal-static-import-contract/v1")
        self.assertEqual(self.contract["status"], "READY__STATIC_SOURCE_CONTRACT_ONLY__WAITING_FOR_SHARED_PROJECT_BASELINE")
        self.assertEqual(self.contract["provenance_status"], "PASS__AFFIRMATIVE_ALLOWLIST__NO_ZERO_CALL_INFERENCE")
        source = self.contract["source"]
        self.assertEqual((source["logical_asset_count"], source["authored_lod_count"], source["fbx_source_count"]), (16, 48, 48))
        self.assertEqual(source["fresh_fbx_glb_roundtrip_count"], 96)
        for key in ("manifest", "frozen_receipt", "frozen_sidecar", "build_receipt", "geometry_gate", "roundtrip_gate", "provenance_gate"):
            row = source[key]
            self.assertEqual(sha256(ROOT / row["path"]), row["sha256"], key)

    def test_exact_native_namespace_never_reuses_meshy_candidate_namespaces(self) -> None:
        destination = self.contract["destination"]
        self.assertEqual(destination["namespace"], "/Game/LineBoss/Native/Vehicles/Cairnwell2040/VehicleWIPNativeKit_v001")
        self.assertEqual(destination["expected_asset_count"], 16)
        self.assertTrue(destination["must_be_absent_before_run"])
        for spec in self.contract["assets"].values():
            self.assertTrue(spec["package_path"].startswith(destination["namespace"] + "/"))
            for forbidden in destination["forbidden_existing_or_meshy_namespaces"]:
                self.assertFalse(spec["package_path"].startswith(forbidden))

    def test_all_roles_lods_hashes_geometry_uv_pivot_bounds_and_materials(self) -> None:
        expected_layers = {"Underbody", "SideFrame_L", "SideFrame_R", "UpperStructure", "RoofClosures",
                           "InteriorTrim", "PowertrainChassis", "RollingGear", "GlassLightsFinish"}
        expected_panels = {"Hood", "Roof", "FrontDoor_L", "RearDoor_L", "FrontFender_L", "QuarterPanel_L", "Tailgate"}
        layers = {key for key, spec in self.contract["assets"].items() if spec["kind"] == "Layer"}
        panels = {key for key, spec in self.contract["assets"].items() if spec["kind"] == "Panel"}
        self.assertEqual(layers, expected_layers)
        self.assertEqual(panels, expected_panels)
        self.assertEqual(sum(len(spec["lods"]) for spec in self.contract["assets"].values()), 48)
        totals = [0, 0, 0]
        for key, spec in self.contract["assets"].items():
            chain = [int(row["triangles"]) for row in spec["lods"]]
            self.assertEqual(chain, spec["triangle_chain"], key)
            self.assertGreater(chain[0], chain[1], key)
            self.assertGreater(chain[1], chain[2], key)
            if spec["kind"] == "Layer":
                totals = [totals[i] + chain[i] for i in range(3)]
            for lod, row in enumerate(spec["lods"]):
                self.assertEqual(row["lod"], lod)
                self.assertEqual(row["uv_layers"], 1)
                self.assertEqual(row["degenerate_triangles"], 0)
                self.assertEqual(row["expected_unreal_bounds"]["pivot_cm"], [0.0, 0.0, 0.0])
                self.assertTrue(row["material_slots"])
                source = ROOT / row["source"]
                self.assertEqual(source.stat().st_size, row["source_bytes"])
                self.assertEqual(sha256(source), row["source_sha256"])
        self.assertEqual(totals, [24720, 12500, 4332])

    def test_lod_screen_nanite_collision_navigation_and_material_policy(self) -> None:
        contract = self.contract["import_contract"]
        self.assertEqual(contract["lod_screen_sizes"], [1.0, 0.35, 0.12])
        self.assertFalse(contract["auto_compute_lod_screen_size"])
        self.assertFalse(contract["nanite_enabled"])
        self.assertFalse(contract["auto_generate_collision"])
        self.assertFalse(contract["import_materials"])
        self.assertFalse(contract["import_textures"])
        for spec in self.contract["assets"].values():
            self.assertEqual((spec["collision"]["simple_count"], spec["collision"]["convex_count"]), (0, 0))
            self.assertEqual(spec["collision"]["navigation_component_policy"], "CanEverAffectNavigation=false")

    def test_baseline_and_target_are_intentionally_absent_until_paint_settles(self) -> None:
        self.assertFalse(BASELINE.exists())
        self.assertFalse(BASELINE_SHA.exists())
        self.assertFalse(DEST.exists())
        self.assertFalse(AUDITS.exists())
        self.assertIn("DO NOT run the creation mode until the shared OneFactory Paint integration", self.freezer)
        self.assertIn("No whole-project baseline has been cut yet", self.doc)

    def test_prepared_python_is_syntactically_valid_without_importing_unreal(self) -> None:
        for path in (FREEZER, COMMON, IMPORTER, VALIDATOR):
            compile(path.read_text(encoding="utf-8"), str(path), "exec")

    def test_freezer_is_offline_fresh_only_and_full_protection_ready(self) -> None:
        self.assertNotIn("import unreal", self.freezer)
        self.assertNotIn("subprocess", self.freezer)
        self.assertIn("refusing to overwrite existing vehicle-WIP baseline", self.freezer)
        self.assertIn("complete_source_tree", self.freezer)
        self.assertIn("all_existing_content_outside_new_native_namespace", self.freezer)
        self.assertIn("campaign_save_games", self.freezer)
        self.assertIn("PASS__FULL_SOURCE_AND_PROTECTED_BASELINE_REVERIFY", self.freezer)

    def test_importer_is_fresh_only_non_destructive_and_custom_lod_guarded(self) -> None:
        for forbidden in ("delete_asset(", "delete_directory(", "load_level(", "save_current_level(",
                          '"replace_existing": True', '"replace_existing_settings": True'):
            self.assertNotIn(forbidden, self.importer)
        self.assertIn('"replace_existing": False', self.importer)
        self.assertIn("subsystem.import_lod", self.importer)
        self.assertIn("finally:", self.importer)
        self.assertIn("restore_attempted_in_finally", self.importer)
        self.assertIn("custom_lods_requested\": 32", self.importer)
        self.assertIn("PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW", self.importer)

    def test_validator_is_independent_read_only_and_reloads_all_gates(self) -> None:
        for forbidden in ("save_loaded_asset(", "save_asset(", "delete_asset(", "delete_directory(",
                          "AssetImportTask(", "import_lod(", "load_level(", "save_current_level("):
            self.assertNotIn(forbidden, self.validator)
        self.assertIn("import_pid == os.getpid()", self.validator)
        self.assertIn("target_after != target_before", self.validator)
        self.assertIn("lane.validate_mesh", self.validator)

    def test_runner_is_deferred_two_fresh_process_no_compile(self) -> None:
        self.assertEqual(self.runner.count("Invoke-GuardedProcess $Editor"), 2)
        self.assertIn("-NoCompile", self.runner)
        self.assertIn("-NullRHI", self.runner)
        self.assertNotIn("Build.bat", self.runner)
        self.assertIn("Assert-NoProcesses", self.runner)
        self.assertIn("IMPORT_FROZEN_VEHICLE_WIP_NATIVE_KIT_V001_BASELINE_V001_ONCE", self.runner)
        self.assertIn("Full offline source/protected baseline reverify failed", self.runner)


if __name__ == "__main__":
    unittest.main()
