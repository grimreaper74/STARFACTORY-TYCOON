"""Offline safety tests for the isolated 2126 overhead playable-map builder."""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
BUILDER = PROJECT / "Tools" / "build_pressshop_2126_overhead_playable_v001.py"


def load_builder_module():
    previous_unreal = sys.modules.get("unreal")
    sys.modules["unreal"] = types.ModuleType("unreal")
    try:
        spec = importlib.util.spec_from_file_location("pressshop_overhead_builder_test_subject", BUILDER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        if previous_unreal is None:
            sys.modules.pop("unreal", None)
        else:
            sys.modules["unreal"] = previous_unreal


MODULE = load_builder_module()


def valid_layer(assembly_id, layer_id, actor_label, kind="base", authority_label=None, state=None):
    row = {
        "id": layer_id,
        "actor_label": actor_label,
        "kind": kind,
        "mesh_asset": "/Engine/BasicShapes/Plane.Plane",
        "material_asset": "/Game/LineBoss/Test/M_Test.M_Test",
        "transform": {
            "location_cm": [100.0, 200.0, 20.0],
            "rotation_deg": [0.0, 0.0, 0.0],
            "scale": [1.0, 1.0, 1.0],
        },
        "collision_enabled": False,
        "asset_package_ready": True,
        "tags": [MODULE.LAYER_TAG],
        "source_sha256": "a" * 64,
    }
    if kind in MODULE.MOVING_LAYER_KINDS:
        row["runtime_binding"] = {
            "ready": True,
            "authority_actor_label": authority_label,
            "motion_channel": "authoritative_phase",
            "binding_tag": "LB.Binding.{}.{}".format(assembly_id, layer_id),
        }
    if kind == "frame_state":
        row["frame_state"] = state
        row["anchor_px"] = [1024, 1024]
        row["initially_visible"] = state == "open"
    return row


def valid_runtime_manifest(animation_hash=None):
    animation_hash = animation_hash or MODULE.ANIMATION_CONTRACT_SHA256
    authority_rows = []
    assemblies = []
    controller_classes = []
    for index, assembly_id in enumerate(sorted(MODULE.REQUIRED_ASSEMBLY_IDS), start=1):
        authority_label = "AUTH | {}".format(assembly_id)
        class_name = "LBTestAuthorityController{:02d}".format(index)
        authority_rows.append({
            "actor_label": authority_label,
            "class_name": class_name,
            "assembly_id": assembly_id,
        })
        controller_classes.append(class_name)
        assembly = {
            "id": assembly_id,
            "runtime_ready": True,
            "layers": [
                valid_layer(
                    assembly_id,
                    "{}_base".format(assembly_id),
                    "VIS | {} | base".format(assembly_id),
                )
            ],
        }
        machine_ids = sorted(MODULE.PRESS_FRAME_STATIONS) if assembly_id == "S02_TO_S06_PRESS_STATIONS" else [assembly_id]
        assembly["machines"] = machine_ids
        assembly["status_beacons"] = []
        for machine_index, machine_id in enumerate(machine_ids, start=1):
            assembly["status_beacons"].append({
                "machine_id": machine_id,
                "authority_actor_label": authority_label,
                "component_class": MODULE.NATIVE_BEACON_COMPONENT_CLASS,
                "component_name": "{}_StatusBeacon_{:02d}".format(assembly_id, machine_index),
                "anchor_relative_cm": [float(machine_index * 10), 0.0, 80.0],
                "state_source": "{}::AuthoritativeOperatingState".format(class_name),
                "visual_contract": MODULE.NATIVE_BEACON_VISUAL_CONTRACT,
                "uses_emissive_mid": True,
                "uses_point_light_glow": True,
                "point_light_glow_restrained": True,
                "gameplay_state_driven": True,
                "baked_colour_only": False,
                "decorative_loop": False,
                "state_mapping": {
                    "green": ["Ready", "Running"],
                    "amber": ["Idle", "Waiting", "Moving"],
                    "red": ["Stopped", "Fault", "Emergency"],
                },
            })
        if assembly_id == "S02_TO_S06_PRESS_STATIONS":
            frame_sets = []
            for station in sorted(MODULE.PRESS_FRAME_STATIONS):
                state_layers = {}
                for state in MODULE.PRESS_FRAME_STATES:
                    layer_id = "{}_{}".format(station, state)
                    assembly["layers"].append(
                        valid_layer(
                            assembly_id,
                            layer_id,
                            "VIS | {} | {}".format(station, state),
                            kind="frame_state",
                            authority_label=authority_label,
                            state=state,
                        )
                    )
                    state_layers[state] = layer_id
                frame_sets.append({
                    "station": station,
                    "mode": "GAMEPLAY_TIMED_EXACT_ANCHOR_FRAME_STATES",
                    "exact_anchor_all_states": True,
                    "world_z_screen_translation_forbidden": True,
                    "authoritative_phase_source": "ALBPressTrainAStation::SlideProgress",
                    "states": state_layers,
                })
            assembly["frame_state_sets"] = frame_sets
        assembly["effect_bindings"] = []
        for effect_index, contract_effect in enumerate(sorted(MODULE.REQUIRED_EFFECTS_BY_ASSEMBLY[assembly_id]), start=1):
            effect_id = "{}_FX_{:02d}".format(assembly_id, effect_index)
            anchor_tag = "LB.EffectAnchor.{}".format(effect_id)
            layer_id = None
            implementation = "native_component"
            colour_role = None
            if contract_effect in MODULE.CYAN_STATE_EFFECTS:
                layer_id = "{}_cyan_{}".format(assembly_id, effect_index)
                effect_layer = valid_layer(
                    assembly_id,
                    layer_id,
                    "VIS | {} | cyan {:02d}".format(assembly_id, effect_index),
                    kind="effect_mask",
                    authority_label=authority_label,
                )
                effect_layer["tags"].append(anchor_tag)
                assembly["layers"].append(effect_layer)
                implementation = "dynamic_material_parameter"
                colour_role = "cyan"
            assembly["effect_bindings"].append({
                "id": effect_id,
                "contract_effect": contract_effect,
                "machine_id": machine_ids[0],
                "authority_actor_label": authority_label,
                "state_source": "{}::AuthoritativeOperatingState".format(class_name),
                "implementation": implementation,
                "anchor_relative_cm": [float(effect_index * 5), 0.0, 30.0],
                "effect_anchor_tag": anchor_tag,
                "gameplay_state_driven": True,
                "decorative_loop": False,
                "baked_only": False,
                "colour_role": colour_role,
                "layer_id": layer_id,
            })
        assemblies.append(assembly)

    return {
        "schema": MODULE.RUNTIME_MANIFEST_SCHEMA,
        "status": MODULE.RUNTIME_MANIFEST_STATUS,
        "runtime_ready": True,
        "map_contract": {
            "source_map": MODULE.SOURCE_MAP,
            "target_map": MODULE.TARGET_MAP,
            "duplicate_source_while_unloaded": True,
        },
        "animation_contract": {
            "contract_id": MODULE.ANIMATION_CONTRACT_ID,
            "sha256": animation_hash,
            "all_assemblies_bound": True,
        },
        "view": {
            "projection": "orthographic",
            "view_mode": "TRUE_OVERHEAD",
            "rotation_deg": [-90.0, 0.0, 0.0],
            "location_cm": [8800.0, 1600.0, 21712.544],
            "ortho_width_cm": 17600.0,
            "aspect_ratio": 16.0 / 9.0,
            "camera_actor_label": "CAM | Press Shop 2126 true overhead playable",
        },
        "runtime_preservation": {
            "preserve_game_mode": True,
            "preserve_existing_runtime_actors": True,
            "spawn_duplicate_controllers": False,
            "required_authority_actors": authority_rows,
            "controller_class_names": controller_classes,
        },
        "presentation_hide": {
            "mode": "EXPLICIT_LABELS_ONLY",
            "presentation_only_confirmed": True,
            "disable_collision": True,
            "actor_labels": ["PRESENTATION | old 3D press shell"],
        },
        "assemblies": assemblies,
    }


class BuilderConstantsAndDiskSafetyTests(unittest.TestCase):
    def test_exact_source_target_and_protected_hashes(self):
        self.assertEqual(
            MODULE.SOURCE_MAP,
            "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001",
        )
        self.assertEqual(
            MODULE.TARGET_MAP,
            "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPlayable_v001/Maps/LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001",
        )
        self.assertEqual(MODULE.digest(MODULE.SOURCE_FILE), MODULE.SOURCE_FILE_SHA256)
        self.assertEqual(MODULE.SOURCE_FILE_SHA256, "f4e97b33cdfb1f242b2c606a16b4caa05b74b298fdf1b1263d4a4c46d50e8d5c")
        expected_hashes = {
            "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
            "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
            "0e1bc9ddbf753a790955375eba8d0b274eb7d48cb336a84a82df431f85aa9624",
            "37fc7af541675f4f38afd816d7d4552628d1deaf22b0abe01d6830907a62349f",
            MODULE.SOURCE_FILE_SHA256,
        }
        self.assertEqual(set(MODULE.PROTECTED_MAPS.values()), expected_hashes)
        for path, expected in MODULE.PROTECTED_MAPS.items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(MODULE.digest(path), expected, path)
        self.assertEqual(MODULE.digest(MODULE.DEFAULT_ENGINE_INI), MODULE.DEFAULT_ENGINE_INI_SHA256)
        for path, expected in MODULE.PROTECTED_NATIVE_BEACON_SOURCES.items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(MODULE.digest(path), expected, path)

    def test_target_is_absent_and_canonical_manifest_path_is_approved(self):
        self.assertFalse(MODULE.TARGET_FILE.exists())
        self.assertEqual(
            MODULE.RUNTIME_MANIFEST,
            Path(r"C:\Users\greg_\Documents\Codex\2026-08-22\ca\outputs\PressShop_OverheadRuntime_v001\PRESS_SHOP_OVERHEAD_RUNTIME_MANIFEST_v001.json"),
        )

    def test_missing_runtime_manifest_fails_before_unreal_map_work(self):
        old_path = MODULE.RUNTIME_MANIFEST
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                MODULE.RUNTIME_MANIFEST = Path(temp_dir) / "missing_runtime_manifest.json"
                with self.assertRaisesRegex(RuntimeError, "unified true-overhead runtime manifest is missing"):
                    MODULE.load_and_validate_inputs()
        finally:
            MODULE.RUNTIME_MANIFEST = old_path


class ManifestContractTests(unittest.TestCase):
    def test_current_animation_contract_hash_and_content(self):
        self.assertTrue(MODULE.ANIMATION_CONTRACT.is_file())
        self.assertEqual(MODULE.digest(MODULE.ANIMATION_CONTRACT), MODULE.ANIMATION_CONTRACT_SHA256)
        data = json.loads(MODULE.ANIMATION_CONTRACT.read_text(encoding="utf-8"))
        result = MODULE.validate_animation_contract_data(data)
        self.assertEqual(set(result["assemblies"]), MODULE.REQUIRED_ASSEMBLY_IDS)

    def test_valid_runtime_fixture_passes(self):
        result = MODULE.validate_runtime_manifest_data(
            valid_runtime_manifest(),
            MODULE.ANIMATION_CONTRACT_SHA256,
        )
        self.assertEqual(set(result["assemblies"]), MODULE.REQUIRED_ASSEMBLY_IDS)
        self.assertEqual(len(result["layers"]), 34)
        self.assertEqual(result["view"]["rotation"], (-90.0, 0.0, 0.0))

    def test_non_runtime_ready_and_wrong_camera_fail(self):
        data = valid_runtime_manifest()
        data["runtime_ready"] = False
        with self.assertRaisesRegex(RuntimeError, "runtime_ready"):
            MODULE.validate_runtime_manifest_data(data, MODULE.ANIMATION_CONTRACT_SHA256)
        data = valid_runtime_manifest()
        data["view"]["rotation_deg"] = [-60.0, 57.63, 0.0]
        with self.assertRaisesRegex(RuntimeError, "not exactly true-overhead"):
            MODULE.validate_runtime_manifest_data(data, MODULE.ANIMATION_CONTRACT_SHA256)

    def test_press_z_motion_cannot_use_screen_translation(self):
        data = valid_runtime_manifest()
        press = next(row for row in data["assemblies"] if row["id"] == "S02_TO_S06_PRESS_STATIONS")
        layer = next(row for row in press["layers"] if row.get("frame_state") == "descending")
        layer["runtime_binding"]["motion_channel"] = "world_z_screen_translation"
        with self.assertRaisesRegex(RuntimeError, "incorrectly uses screen translation"):
            MODULE.validate_runtime_manifest_data(data, MODULE.ANIMATION_CONTRACT_SHA256)

    def test_press_frame_states_require_exact_anchor_and_open_only_initial_state(self):
        data = valid_runtime_manifest()
        press = next(row for row in data["assemblies"] if row["id"] == "S02_TO_S06_PRESS_STATIONS")
        target = next(row for row in press["layers"] if row["id"] == "S02_contact")
        target["anchor_px"] = [1025, 1024]
        with self.assertRaisesRegex(RuntimeError, "do not preserve the exact anchor"):
            MODULE.validate_runtime_manifest_data(data, MODULE.ANIMATION_CONTRACT_SHA256)
        data = valid_runtime_manifest()
        press = next(row for row in data["assemblies"] if row["id"] == "S02_TO_S06_PRESS_STATIONS")
        target = next(row for row in press["layers"] if row["id"] == "S02_contact")
        target["initially_visible"] = True
        with self.assertRaisesRegex(RuntimeError, "only its open frame visible"):
            MODULE.validate_runtime_manifest_data(data, MODULE.ANIMATION_CONTRACT_SHA256)

    def test_runtime_authorities_and_duplicate_controller_policy_are_fail_closed(self):
        data = valid_runtime_manifest()
        data["runtime_preservation"]["spawn_duplicate_controllers"] = True
        with self.assertRaisesRegex(RuntimeError, "spawn_duplicate_controllers"):
            MODULE.validate_runtime_manifest_data(data, MODULE.ANIMATION_CONTRACT_SHA256)
        data = valid_runtime_manifest()
        data["runtime_preservation"]["required_authority_actors"].pop()
        with self.assertRaisesRegex(RuntimeError, "do not cover every animation assembly"):
            MODULE.validate_runtime_manifest_data(data, MODULE.ANIMATION_CONTRACT_SHA256)

    def test_every_machine_requires_native_beacon_and_every_effect_is_bound(self):
        data = valid_runtime_manifest()
        inbound = next(row for row in data["assemblies"] if row["id"] == "IN02_COIL_HANDLER_AGV")
        inbound["status_beacons"] = []
        with self.assertRaisesRegex(RuntimeError, "native status beacons"):
            MODULE.validate_runtime_manifest_data(data, MODULE.ANIMATION_CONTRACT_SHA256)
        data = valid_runtime_manifest()
        inbound = next(row for row in data["assemblies"] if row["id"] == "IN02_COIL_HANDLER_AGV")
        inbound["effect_bindings"].pop()
        with self.assertRaisesRegex(RuntimeError, "do not cover the authoritative animation contract"):
            MODULE.validate_runtime_manifest_data(data, MODULE.ANIMATION_CONTRACT_SHA256)

    def test_beacon_cannot_be_baked_only_and_cyan_requires_dynamic_anchor(self):
        data = valid_runtime_manifest()
        inbound = next(row for row in data["assemblies"] if row["id"] == "IN02_COIL_HANDLER_AGV")
        inbound["status_beacons"][0]["baked_colour_only"] = True
        with self.assertRaisesRegex(RuntimeError, "baked_colour_only"):
            MODULE.validate_runtime_manifest_data(data, MODULE.ANIMATION_CONTRACT_SHA256)
        data = valid_runtime_manifest()
        inbound = next(row for row in data["assemblies"] if row["id"] == "IN02_COIL_HANDLER_AGV")
        cyan = next(row for row in inbound["effect_bindings"] if row["contract_effect"] == "directional_route_strip")
        cyan["layer_id"] = None
        with self.assertRaisesRegex(RuntimeError, "explicit dynamic cyan visual layer anchor"):
            MODULE.validate_runtime_manifest_data(data, MODULE.ANIMATION_CONTRACT_SHA256)


class BuilderMutationSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = BUILDER.read_text(encoding="utf-8")

    def test_manifest_validation_precedes_target_creation_and_hiding(self):
        main_start = self.source.index("def main()")
        body = self.source[main_start:]
        validate_index = body.index("load_and_validate_inputs()")
        duplicate_index = body.index("duplicate_asset(SOURCE_MAP, TARGET_MAP)")
        load_target_index = body.index("load_map(TARGET_MAP)")
        hide_index = body.index("hide_presentation_actors(")
        self.assertLess(validate_index, duplicate_index)
        self.assertLess(duplicate_index, load_target_index)
        self.assertLess(load_target_index, hide_index)

    def test_source_unloaded_and_clean_unrelated_world_gates_are_present(self):
        self.assertIn("current_world_package in (SOURCE_MAP, TARGET_MAP)", self.source)
        self.assertIn("get_dirty_map_packages", self.source)
        self.assertIn("get_dirty_content_packages", self.source)
        self.assertIn("source_asset_data[0].is_asset_loaded()", self.source)
        self.assertIn("source_package_loaded_before_duplicate\": False", self.source)

    def test_builder_has_no_destructive_or_broad_save_operations(self):
        forbidden = (
            "delete_asset(",
            "delete_directory(",
            "rename_asset(",
            "destroy_actor(",
            "save_directory(",
            "save_loaded_assets(",
            "save_asset(",
            "AssetImportTask",
            "import_asset_tasks",
            "default_game_mode\",",
        )
        for token in forbidden:
            self.assertNotIn(token, self.source, token)
        self.assertEqual(self.source.count("save_current_level()"), 1)
        self.assertEqual(self.source.count("RECEIPT.write_text("), 1)
        self.assertEqual(self.source.count("duplicate_asset(SOURCE_MAP, TARGET_MAP)"), 1)

    def test_only_visual_layers_and_one_camera_are_spawned(self):
        self.assertEqual(self.source.count("spawn_actor_from_class("), 2)
        self.assertIn("unreal.StaticMeshActor", self.source)
        self.assertIn("unreal.CameraActor", self.source)
        self.assertNotIn("spawn_actor_from_object", self.source)
        self.assertIn("controller_counts_after != controller_counts_before", self.source)
        self.assertIn("game_mode_after != game_mode_before", self.source)


if __name__ == "__main__":
    unittest.main()
