"""Offline safety and evidence tests for detailed OneFactory Press recovery."""

from __future__ import annotations

import ast
import copy
import importlib.util
import json
from pathlib import Path
import unittest


PROJECT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = PROJECT / "Scripts/one_factory_detailed_press_v001_contract.py"
EXPORTER_PATH = PROJECT / "Scripts/audit_one_factory_detailed_press_v438_source_v001.py"
SPEC = importlib.util.spec_from_file_location("detailed_press_contract", CONTRACT_PATH)
CONTRACT = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(CONTRACT)


def material(path: str = "/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial") -> dict:
    return {
        "object_path": path,
        "class_path": "/Script/Engine.Material",
        "parent_path": "",
        "map_owned": False,
        "scalar_parameters": {},
        "vector_parameters": {},
        "texture_parameters": {},
    }


def transforms(location: list[float]) -> dict:
    return {
        "world_location_cm": list(location),
        "world_rotation_deg": [0.0, 0.0, 0.0],
        "world_scale": [1.0, 1.0, 1.0],
        "relative_location_cm": [
            location[0] - CONTRACT.TRAIN_DATUM_CM[0],
            location[1] - CONTRACT.TRAIN_DATUM_CM[1],
            location[2] - CONTRACT.TRAIN_DATUM_CM[2],
        ],
        "relative_rotation_deg": [0.0, 0.0, 0.0],
        "relative_scale": [1.0, 1.0, 1.0],
    }


def valid_manifest() -> dict:
    capture = json.loads(
        (PROJECT / CONTRACT.SOURCE_CAPTURE_RELATIVE).read_text(encoding="utf-8")
    )
    source_rows = [
        row for row in capture["actors"]
        if CONTRACT.TRAIN_SCOPE_TAG in row.get("tags", [])
    ]
    actors = []
    for source in source_rows:
        location = [float(value) for value in source["location_cm"]]
        row = {
            "label": source["label"],
            "class_name": source["class"],
            "class_path": "/Script/LineBossCarFactory." + source["class"],
            "tags": list(source["tags"]),
            **transforms(location),
        }
        if source["class"] == CONTRACT.LEGACY_AUTHORITY_CLASS:
            row["materialization_policy"] = "excluded_current_native_constructor"
            row["components"] = []
        else:
            row["materialization_policy"] = "eligible_visual_only"
            row["seed_projection"] = copy.deepcopy(source)
            component = {
                "component_name": "PresentationVisual",
                "class_path": "/Script/Engine.StaticMeshComponent",
                "component_tags": [],
                **transforms(location),
            }
            if source["class"] == "TextRenderActor":
                component.update({
                    "visual_kind": "text",
                    "text": "TRAIN A",
                    "font_path": "/Engine/EngineFonts/Roboto.Roboto",
                    "materials": [material()],
                })
            else:
                component.update({
                    "visual_kind": "static_mesh",
                    "mesh_path": "/Engine/BasicShapes/Cube.Cube",
                    "materials": [material()],
                })
            row["components"] = [component]
        actors.append(row)
    return {
        "$schema": CONTRACT.RAW_MANIFEST_SCHEMA,
        "source_map": CONTRACT.SOURCE_MAP,
        "source_map_sha256_before": CONTRACT.SOURCE_MAP_SHA256,
        "source_map_sha256_after": CONTRACT.SOURCE_MAP_SHA256,
        "source_map_saved": False,
        "scope_tag": CONTRACT.TRAIN_SCOPE_TAG,
        "train_datum_cm": list(CONTRACT.TRAIN_DATUM_CM),
        "project_asset_provenance": [],
        "actors": actors,
    }


class PreservedEvidenceTests(unittest.TestCase):
    def test_exact_preserved_evidence_passes_without_unreal(self):
        result = CONTRACT.validate_preserved_evidence(PROJECT)
        self.assertEqual(result["actor_count"], 338)
        self.assertEqual(result["visual_actor_count"], 337)
        self.assertEqual(result["v449_fidelity_fallback"]["material_slot_count"], 306)
        self.assertEqual(result["v449_fidelity_fallback"]["unique_material_count"], 13)

    def test_forbidden_provenance_is_fail_closed(self):
        forbidden = (
            "/Game/LineBoss/Candidates/Meshy/SM_Robot_v001",
            "/Game/Vendor/Industrial/SM_Press_v001",
            "/Game/Developers/Greg/Validation/SM_Press_v001",
            "/Game/LineBoss/Candidates/PressTrains/Complete_v700/SM_Press_v700",
            "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913",
        )
        for path in forbidden:
            with self.subTest(path=path):
                self.assertIsNotNone(CONTRACT.forbidden_reference_reason(path))
        for path in (
            CONTRACT.SOURCE_MAP,
            CONTRACT.V449_RUNTIME_MESH,
            "/Game/LineBoss/Candidates/PressTrains/InstalledPBR_v383/M_Test_v383",
            "/Engine/BasicShapes/Cube.Cube",
        ):
            with self.subTest(path=path):
                self.assertIsNone(CONTRACT.forbidden_reference_reason(path))


class ExtractionManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = valid_manifest()

    def test_exact_manifest_and_grouping_plan_pass(self):
        summary = CONTRACT.validate_extraction_manifest(self.manifest)
        self.assertEqual(summary["actor_count"], 338)
        self.assertEqual(summary["visual_actor_count"], 337)
        plan = CONTRACT.compile_materialization_plan(self.manifest)
        represented = (
            plan["hism_instance_count"]
            + plan["static_component_count"]
            + plan["text_component_count"]
        )
        self.assertEqual(represented, 337)
        self.assertFalse(plan["presentation_policy"]["represents_process_wip"])
        self.assertEqual(plan["presentation_policy"]["collision"], "NoCollision")
        joined = json.dumps(plan)
        self.assertNotIn(CONTRACT.LEGACY_AUTHORITY_LABEL, joined)

    def test_manifest_rejects_forbidden_material(self):
        manifest = copy.deepcopy(self.manifest)
        visual = next(row for row in manifest["actors"] if row["components"])
        visual["components"][0]["materials"][0]["object_path"] = (
            "/Game/LineBoss/Candidates/PressTrains/Meshy_v864/M_Bad_v864"
        )
        with self.assertRaisesRegex(CONTRACT.ContractError, "forbidden reference"):
            CONTRACT.validate_extraction_manifest(manifest)

    def test_manifest_rejects_visual_inventory_drift(self):
        manifest = copy.deepcopy(self.manifest)
        visual = next(
            row for row in manifest["actors"]
            if row["class_name"] == "StaticMeshActor"
        )
        visual["seed_projection"]["location_cm"][0] += 1.0
        with self.assertRaisesRegex(CONTRACT.ContractError, "seed signature mismatch"):
            CONTRACT.validate_extraction_manifest(manifest)

    def test_manifest_rejects_materializing_legacy_authority(self):
        manifest = copy.deepcopy(self.manifest)
        legacy = next(
            row for row in manifest["actors"]
            if row["class_name"] == CONTRACT.LEGACY_AUTHORITY_CLASS
        )
        legacy["components"] = [{"visual_kind": "static_mesh"}]
        with self.assertRaisesRegex(CONTRACT.ContractError, "legacy authority"):
            CONTRACT.validate_extraction_manifest(manifest)

    def test_map_owned_material_requires_snapshot_and_becomes_clone_plan(self):
        manifest = copy.deepcopy(self.manifest)
        visual = next(row for row in manifest["actors"] if row["components"])
        source_material = visual["components"][0]["materials"][0]
        source_material.update({
            "object_path": CONTRACT.SOURCE_MAP + ":PersistentLevel.MID_Test",
            "parent_path": "/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial",
            "map_owned": True,
            "vector_parameters": {"Tint": [0.1, 0.2, 0.3, 1.0]},
        })
        plan = CONTRACT.compile_materialization_plan(manifest)
        planned_materials = [
            material
            for group in plan["hism_groups"]
            for material in group["materials"]
        ] + [
            material
            for component in plan["static_components"]
            for material in component["materials"]
        ]
        clone = next(
            material for material in planned_materials
            if material.get("material_clone_id")
        )
        self.assertEqual(clone["object_path"], "")
        self.assertEqual(clone["parent_path"], source_material["parent_path"])

        source_material["parent_path"] = ""
        with self.assertRaisesRegex(CONTRACT.ContractError, "lacks a reusable parent"):
            CONTRACT.validate_extraction_manifest(manifest)

    def test_transient_dynamic_material_is_also_cloned(self):
        manifest = copy.deepcopy(self.manifest)
        visual = next(
            row for row in manifest["actors"]
            if row["class_name"] == "StaticMeshActor"
        )
        source_material = visual["components"][0]["materials"][0]
        source_material.update({
            "object_path": "/Engine/Transient.MaterialInstanceDynamic_7",
            "class_path": "/Script/Engine.MaterialInstanceDynamic",
            "parent_path": "/Engine/EngineMaterials/DefaultMaterial.DefaultMaterial",
        })
        plan = CONTRACT.compile_materialization_plan(manifest)
        planned = [
            material
            for group in plan["hism_groups"]
            for material in group["materials"]
        ]
        self.assertTrue(any(row.get("material_clone_id") for row in planned))

    def test_instanced_source_requires_and_preserves_every_transform(self):
        manifest = copy.deepcopy(self.manifest)
        visual = next(
            row for row in manifest["actors"]
            if row["class_name"] == "StaticMeshActor"
        )
        component = visual["components"][0]
        component["visual_kind"] = "instanced_static_mesh"
        first = {"instance_index": 0, **transforms(visual["world_location_cm"])}
        second_location = list(visual["world_location_cm"])
        second_location[0] += 25.0
        second = {"instance_index": 1, **transforms(second_location)}
        component["source_instance_count"] = 2
        component["source_instances"] = [first, second]
        summary = CONTRACT.validate_extraction_manifest(manifest)
        self.assertEqual(summary["render_primitive_count"], 338)
        plan = CONTRACT.compile_materialization_plan(manifest)
        represented = (
            plan["hism_instance_count"]
            + plan["static_component_count"]
            + plan["text_component_count"]
        )
        self.assertEqual(represented, 338)

        component["source_instances"].pop()
        with self.assertRaisesRegex(CONTRACT.ContractError, "exact instance transforms"):
            CONTRACT.validate_extraction_manifest(manifest)

    def test_project_asset_provenance_must_exactly_cover_references(self):
        manifest = copy.deepcopy(self.manifest)
        visual = next(row for row in manifest["actors"] if row["components"])
        visual["components"][0]["mesh_path"] = (
            "/Game/LineBoss/Candidates/PressTrains/InstalledPBR_v383/SM_Test_v383"
        )
        with self.assertRaisesRegex(CONTRACT.ContractError, "does not exactly cover"):
            CONTRACT.validate_extraction_manifest(manifest)


class ToolingStaticSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exporter = EXPORTER_PATH.read_text(encoding="utf-8")
        cls.contract = CONTRACT_PATH.read_text(encoding="utf-8")

    def test_scripts_parse(self):
        self.assertIsInstance(ast.parse(self.exporter, filename=str(EXPORTER_PATH)), ast.Module)
        self.assertIsInstance(ast.parse(self.contract, filename=str(CONTRACT_PATH)), ast.Module)

    def test_unreal_exporter_has_no_content_or_actor_mutation_calls(self):
        lowered = self.exporter.lower()
        for forbidden in (
            "save_current_level(",
            "save_asset(",
            "save_loaded_asset(",
            "duplicate_asset(",
            "delete_asset(",
            "rename_asset(",
            "spawn_actor",
            "destroy_actor",
            "set_actor_",
            "set_editor_property(",
        ):
            self.assertNotIn(forbidden, lowered)
        self.assertIn("source_map_saved\": False", self.exporter)
        self.assertIn("protected_after != protected_before", self.exporter)

    def test_detailed_runtime_keeps_the_exact_existing_pairing_seam(self):
        player_builder = (
            PROJECT / "Source/LineBossCarFactory/LBOneFactoryPlayerBuilderSubsystem.cpp"
        ).read_text(encoding="utf-8")
        presentation = (
            PROJECT / "Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.h"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "ALBOneFactoryPressStarterPresentationActor::StaticClass()",
            player_builder,
        )
        self.assertIn("268-item station contract", presentation)
        self.assertIn("verified pre-Meshy v449 Press aggregate", presentation)
        self.assertIn("Two private static-mesh components", presentation)
        self.assertNotIn("OneFactoryDetailedPressPresentation", player_builder)


if __name__ == "__main__":
    unittest.main()
