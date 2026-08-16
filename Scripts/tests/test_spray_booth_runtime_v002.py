"""Static/offline contract tests for original procedural spray booth v002."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
import re
import unittest


PROJECT = Path(__file__).resolve().parents[2]
AUTHORITY = PROJECT / "SourceAssets/Candidate/PaintShop/SprayBoothRuntime_v002/Authority"
IMPORTER = PROJECT / "Scripts/import_spray_booth_runtime_v002.py"
VALIDATOR = PROJECT / "Scripts/validate_spray_booth_runtime_v002.py"
RUNNER = PROJECT / "Scripts/run_spray_booth_runtime_v002_validation.ps1"
RECOVERY = PROJECT / (
    "Scripts/recover_spray_booth_runtime_v002_collision_incident_"
    "20260815T014836Z_v003.ps1"
)
SUCCESSOR = AUTHORITY / "unreal_lane_recovery_authority_v003.json"
DOC = PROJECT / "Docs/PaintShop/SPRAY_BOOTH_RUNTIME_V002_UNREAL_LANE.md"
PYTHON_STUB = PROJECT / "Intermediate/PythonStub/unreal.py"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class SprayBoothRuntimeV002Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generator = (AUTHORITY / "generate_LB_PaintSprayBooth_Runtime_LOD1_v002.py").read_text()
        cls.exporter = (AUTHORITY / "export_LB_PaintSprayBooth_Runtime_LOD0_v002.py").read_text()
        cls.audit_script = (AUTHORITY / "Audit/audit_roundtrip_v002.py").read_text()
        cls.importer = IMPORTER.read_text()
        cls.validator = VALIDATOR.read_text()
        cls.runner = RUNNER.read_text()
        cls.recovery = RECOVERY.read_text()
        cls.doc = DOC.read_text()
        cls.manifest = json.loads((AUTHORITY / "authority_manifest_v002.json").read_text())
        cls.roundtrip = json.loads((AUTHORITY / "Audit/roundtrip_validation_v002.json").read_text())
        cls.successor = json.loads(SUCCESSOR.read_text())

    def test_python_and_powershell_static_syntax(self):
        for path in (
            AUTHORITY / "generate_LB_PaintSprayBooth_Runtime_LOD1_v002.py",
            AUTHORITY / "export_LB_PaintSprayBooth_Runtime_LOD0_v002.py",
            AUTHORITY / "Audit/audit_roundtrip_v002.py", IMPORTER, VALIDATOR,
        ):
            self.assertIsInstance(ast.parse(path.read_text(), filename=str(path)), ast.Module)
        self.assertIn("Set-StrictMode -Version Latest", self.runner)
        self.assertIn("Set-StrictMode -Version Latest", self.recovery)

    def test_two_independent_original_source_lods(self):
        self.assertTrue(self.manifest["status"].startswith("PASS__TWO_ORIGINAL_PROCEDURAL"))
        self.assertEqual([row["triangles"] for row in self.manifest["lods"]], [3804, 420])
        self.assertNotIn("import_scene", self.generator)
        self.assertIn("primitive_cube_add", self.generator)
        self.assertIn("primitive_cylinder_add", self.generator)
        self.assertIn("no Meshy", self.manifest["provenance"])

    def test_roundtrip_geometry_material_uv_and_portals(self):
        self.assertEqual(self.roundtrip["failures"], [])
        for key, triangles in (("lod0", 3804), ("lod1_fbx", 420), ("lod1_glb", 420)):
            row = self.roundtrip[key]
            self.assertTrue(all(
                abs(actual - expected) <= 0.00001
                for actual, expected in zip(row["bounds_m"]["dimensions"], (12.0, 5.0, 4.5))
            ))
            self.assertEqual(row["triangles"], triangles)
            self.assertEqual(row["degenerate_triangles"], 0)
            self.assertEqual(row["uv_covered_meshes"], row["objects"])
            self.assertEqual(len(row["materials"]), 6)
        self.assertEqual(len(self.roundtrip["lod0_collision_objects"]), 3)
        self.assertFalse(self.roundtrip["portal_contract"]["ucx_blocks_portal"])
        self.assertEqual(self.roundtrip["robots"], 0)
        self.assertEqual(self.roundtrip["screens"], 0)

    def test_frozen_binary_authorities_match_manifest(self):
        for relative, row in self.manifest["files"].items():
            path = PROJECT / relative
            self.assertTrue(path.is_file(), relative)
            self.assertEqual(path.stat().st_size, row["bytes"], relative)
            self.assertEqual(sha(path), row["sha256"], relative)

    def test_successor_authority_pins_exact_incident_and_reflection_truth(self):
        self.assertTrue(self.successor["status"].startswith(
            "FROZEN__EXACT_COLLISION_INCIDENT_DIAGNOSED"))
        incident = self.successor["incident"]
        self.assertEqual(incident["run_id"], "20260815T014836Z")
        evidence_rows = [
            incident["failed_import_log"], incident["partial_package"],
            incident["read_only_diagnostic"]["script"],
            incident["read_only_diagnostic"]["log"],
            incident["read_only_diagnostic"]["extended_log"],
        ]
        for row in evidence_rows:
            path = PROJECT / row["path"]
            self.assertTrue(path.is_file(), row["path"])
            self.assertEqual(path.stat().st_size, row["bytes"], row["path"])
            self.assertEqual(sha(path), row["sha256"], row["path"])
        observed = incident["read_only_diagnostic"]["observed"]
        self.assertEqual(observed, {
            "lod_count": 2, "triangles": [3804, 420], "box_elems": 0,
            "sphere_elems": 0, "sphyl_elems": 0,
            "tapered_capsule_elems": 0, "convex_elems": 3,
            "static_mesh_editor_simple_collision_count": 0,
        })
        self.assertEqual(
            self.successor["collision_acceptance"]["runtime_aggregate_geometry_counts"],
            {"box_elems": 0, "sphere_elems": 0, "sphyl_elems": 0,
             "tapered_capsule_elems": 0, "convex_elems": 3},
        )
        self.assertTrue(
            self.successor["collision_acceptance"]["simple_collision_count_is_not_collision_acceptance"])

        stub = PYTHON_STUB.read_text(encoding="utf-8-sig")
        convex_start = stub.index("class KConvexElem(KShapeElem):")
        convex_end = stub.index("class KLevelSetElem", convex_start)
        convex_reflection = stub[convex_start:convex_end]
        self.assertNotIn("vertex_data", convex_reflection)
        self.assertNotIn("elem_box", convex_reflection)
        self.assertIn("- ``convex_elems`` (Array[KConvexElem])", stub)

    def test_unreal_lane_is_exact_fresh_namespace(self):
        destination = "/Game/LineBoss/Candidates/PaintShop/SprayBoothRuntime_v002"
        for source in (self.importer, self.validator, self.runner):
            self.assertIn(destination, source)
        self.assertIn("not lib.does_directory_exist(DEST)", self.importer)
        self.assertIn("replace_existing\": False", self.importer)
        self.assertIn("subsystem.import_lod(mesh, 1", self.importer)
        self.assertIn("one_convex_hull_per_ucx\": True", self.importer)
        self.assertIn("nanite.enabled = False", self.importer)
        self.assertIn("set_lod_screen_sizes", self.importer)
        for source in (self.importer, self.validator):
            self.assertIn('get_editor_property("body_setup")', source)
            self.assertIn('get_editor_property("agg_geom")', source)
            for field in ("box_elems", "sphere_elems", "sphyl_elems",
                          "tapered_capsule_elems", "convex_elems"):
                self.assertIn(field, source)
            self.assertIn("BODY_SETUP_AGG_GEOM_EXACT_TYPE_COUNTS", source)
            self.assertIn("get_convex_collision_count", source)
            self.assertNotIn("get_simple_collision_count(mesh)) == 3", source)
            self.assertNotIn('"simple_collision_count": 3', source)
        self.assertIn("lib.save_loaded_asset(material, only_if_is_dirty=False)", self.importer)
        self.assertIn("package_file_evidence(expected_packages)", self.importer)
        self.assertIn('receipt.get("package_files") != package_files', self.validator)
        self.assertNotIn("save_loaded_asset", self.validator)
        self.assertNotIn("save_current_level", self.importer + self.validator)

    def test_runner_pins_scripts_and_uses_two_fresh_processes_without_ubt(self):
        self.assertIn(sha(IMPORTER), self.runner)
        self.assertIn(sha(VALIDATOR), self.runner)
        self.assertIn(sha(SUCCESSOR), self.runner)
        self.assertEqual(len(re.findall(r"& \$Editor \$Project", self.runner)), 2)
        self.assertNotIn("Build.bat", self.runner)
        self.assertNotIn("UnrealBuildTool", self.runner.replace("'UnrealBuildTool'", ""))
        self.assertIn("Get-ProtectedSnapshot", self.runner)
        self.assertIn("LINE_BOSS_SPRAY_BOOTH_RUNTIME_V002_IMPORT_PASS", self.runner)
        self.assertIn("LINE_BOSS_SPRAY_BOOTH_RUNTIME_V002_VALIDATION_PASS", self.runner)
        self.assertIn("Assert-CollisionEvidence", self.runner)
        self.assertIn("BODY_SETUP_AGG_GEOM_EXACT_TYPE_COUNTS", self.runner)

    def test_incident_recovery_is_hash_bound_preserving_and_one_shot(self):
        for path in (IMPORTER, VALIDATOR, RUNNER, SUCCESSOR):
            self.assertIn(sha(path), self.recovery)
        for expected in (
            "B2EAC396E3C285750F10E2A57920C42D13FB80B1374DF3FB4AF537E581EEE0D8",
            "AA2181E79CA8C7AAB14D3A0B92CB6E608A326887D10C6F7F69AD74D880806898",
            "9D7679D1CE949CBFC270B1F936E009442B99401DA5B5A45AF1F8B42B56A16C02",
            "E99A176FB01D8DACC91303FE0FE5183F7AB86C2D10235D3069F56A01DCCA78DF",
        ):
            self.assertIn(expected, self.recovery)
        self.assertEqual(
            self.recovery.count("& $Runner -EngineRoot $EngineRoot"), 1)
        self.assertIn("Copy-Item -LiteralPath $FailedPackage", self.recovery)
        self.assertIn("Move-Item -LiteralPath $DestinationDisk", self.recovery)
        self.assertIn("Incident_20260815T014836Z", self.recovery)
        self.assertIn("recovery is one-use only", self.recovery)
        self.assertIn("Assert-SameSnapshot", self.recovery)
        self.assertNotIn("Remove-Item", self.recovery)
        self.assertNotIn("delete_asset", self.recovery.lower())
        self.assertNotIn("UnrealEditor-Cmd.exe", self.recovery)

    def test_documentation_routes_existing_incident_only_through_recovery(self):
        self.assertIn("20260815T014836Z", self.doc)
        self.assertIn("B2EAC396E3C285750F10E2A57920C42D13FB80B1374DF3FB4AF537E581EEE0D8", self.doc)
        self.assertIn(RECOVERY.name, self.doc)
        self.assertIn("convex_elems", self.doc)
        self.assertNotIn("NOT RUN IN UE", self.doc)


if __name__ == "__main__":
    unittest.main()
