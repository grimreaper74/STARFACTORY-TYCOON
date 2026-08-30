"""Adversarial offline tests for the v006 saved-map visual capture lane."""

from __future__ import annotations

import ast
import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SUBJECT = PROJECT / "Tools/capture_pressshop_2126_overhead_presentation_v006.py"
MAP_SHA = "0123456789abcdef" * 4
RECEIPT_SHA = "fedcba9876543210" * 4
MAP_BYTES = 1_765_432


def load_module():
    spec = importlib.util.spec_from_file_location(
        "capture_pressshop_2126_overhead_presentation_v006_for_tests", SUBJECT
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load v006 saved-map capture subject")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def no_collision(module) -> dict:
    return {
        "actor_collision_enabled": False,
        "component_collision_enabled": "CollisionEnabled.NO_COLLISION",
        "generate_overlap_events": False,
        "can_ever_affect_navigation": False,
        "ignored_channels": list(module.COLLISION_CHANNEL_NAMES),
        "profile_acceptance": "NativeNoCollisionWithIgnoreAll",
    }


def exact_receipt(module, contract, map_sha: str = MAP_SHA,
                  map_bytes: int = MAP_BYTES) -> dict:
    correction = contract["module"]
    mutations = []
    for index, plan_row in enumerate(contract["plan"]["mutations"]):
        item_id = str(plan_row["id"])
        kind = str(plan_row["kind"])
        target = plan_row["target"]
        row = {
            "id": item_id,
            "kind": kind,
            "actor_path": (
                module.TARGET_MAP
                + ".LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v006:"
                  "PersistentLevel.Actor_{:03d}".format(index)
            ),
            "label": target["label"],
            "location_cm": list(target["location_cm"]),
        }
        if kind == "box":
            row.update({
                "dimensions_cm": list(target["dimensions_cm"]),
                "material": target["material"],
                "collision_readback": no_collision(module),
            })
        elif kind == "text":
            row.update({
                "world_size_cm": float(target["world_size_cm"]),
                "colour_rgba": list(target["colour_rgba"]),
                "collision_readback": no_collision(module),
            })
        else:
            row.update({
                "ortho_width_cm": float(target["ortho_width_cm"]),
                "role_tag": target["role_tag"],
            })
        mutations.append(row)

    material_rows = []
    material_packages = {}
    for index, (asset, spec) in enumerate(
            contract["candidate_material_specs"].items(), start=1):
        linear = list(correction._v005.srgb_hex_to_linear(spec["srgb_hex"]))
        sha = ("{:02x}".format(index) * 32)
        row = {
            "asset": asset,
            "role": spec["role"],
            "srgb_hex": spec["srgb_hex"],
            "linear_rgb": linear,
            "linear_rgb_readback": list(linear),
            "shading_model": "UNLIT",
            "sha256": sha,
            "bytes": 5000 + index,
        }
        material_rows.append(row)
        material_packages[asset] = {
            "role": spec["role"], "srgb_hex": spec["srgb_hex"],
            "sha256": sha, "bytes": 5000 + index,
        }

    semantic_hashes = {
        "visual": "12" * 32,
        "machinery": "23" * 32,
        "cargo": "34" * 32,
    }
    return {
        "schema": module.INSTALL_SCHEMA,
        "status": module.INSTALL_STATUS,
        "candidate_only": True,
        "source_map": correction.SOURCE_MAP,
        "source_map_sha256": correction.SOURCE_FILE_SHA256,
        "source_map_bytes": correction.SOURCE_FILE_BYTES,
        "source_receipt": correction.SOURCE_RECEIPT.as_posix(),
        "source_receipt_sha256": correction.SOURCE_RECEIPT_SHA256,
        "source_capture_receipt": correction.SOURCE_CAPTURE_RECEIPT.as_posix(),
        "source_capture_receipt_sha256": correction.SOURCE_CAPTURE_RECEIPT_SHA256,
        "target_map": module.TARGET_MAP,
        "target_map_sha256": map_sha,
        "target_map_bytes": map_bytes,
        "target_creation_api": "LevelEditorSubsystem.new_level_from_template",
        "source_actor_count": 302,
        "final_actor_count": 302,
        "source_presentation_actor_count": 140,
        "final_presentation_actor_count": 140,
        "combined_visual_layer_count": 146,
        "machinery_visual_layer_count": 120,
        "cargo_layer_count": 26,
        "source_path_keyed_visual_fingerprints_sha256":
            correction.EXPECTED_SOURCE_HASHES["combined_visual"],
        "source_path_keyed_machinery_fingerprints_sha256":
            correction.EXPECTED_SOURCE_HASHES["machinery_visual"],
        "source_path_keyed_cargo_fingerprints_sha256":
            correction.EXPECTED_SOURCE_HASHES["cargo_visual"],
        "visual_layer_actor_semantic_fingerprints_before_sha256":
            semantic_hashes["visual"],
        "visual_layer_actor_semantic_fingerprints_after_sha256":
            semantic_hashes["visual"],
        "machinery_actor_semantic_fingerprints_before_sha256":
            semantic_hashes["machinery"],
        "machinery_actor_semantic_fingerprints_after_sha256":
            semantic_hashes["machinery"],
        "cargo_actor_semantic_fingerprints_before_sha256": semantic_hashes["cargo"],
        "cargo_actor_semantic_fingerprints_after_sha256": semantic_hashes["cargo"],
        "machinery_actor_mutated_count": 0,
        "cargo_actor_mutated_count": 0,
        "source_actor_removed_count": 0,
        "source_actor_created_count": 0,
        "mutated_existing_presentation_actor_count": 83,
        "mutated_station_zone_actor_count": 36,
        "mutated_route_actor_count": 29,
        "created_presentation_box_count": 0,
        "presentation_mutations": mutations,
        "created_presentation_boxes": [],
        "plan_validation": copy.deepcopy(contract["validation"]),
        "protected_hashes_before": copy.deepcopy(contract["protected"]),
        "protected_hashes_after": copy.deepcopy(contract["protected"]),
        "reused_material_hashes_before": copy.deepcopy(contract["reused_materials"]),
        "reused_material_hashes_after": copy.deepcopy(contract["reused_materials"]),
        "candidate_materials": material_rows,
        "candidate_material_packages": material_packages,
        "presentation_style": {
            "station_zone_material": correction.ZONE_MUTED_MATERIAL,
            "station_zone_srgb_hex": correction.ZONE_MUTED_SRGB_HEX,
            "route_material": correction.ROUTE_MUTED_MATERIAL,
            "route_srgb_hex": correction.ROUTE_MUTED_SRGB_HEX,
            "station_text_rgba": list(correction.STATION_TEXT_RGBA),
            "flow_text_rgba": list(correction.FLOW_TEXT_RGBA),
            "text_depth_separation_cm": correction.TEXT_Z_CM,
            "lights_created": 0,
            "exposure_mutated": False,
            "external_textures": [],
        },
        "machine_or_cargo_transform_mutations": 0,
        "new_machinery_geometry": 0,
        "new_cargo_geometry": 0,
        "collision_enabled_on_created_presentation": False,
        "native_cpp_modified": False,
        "roof_created": False,
        "game_mode_before": module.EXPECTED_GAME_MODE,
        "game_mode_after": module.EXPECTED_GAME_MODE,
        "dirty_packages_before_save": {"content": [], "maps": [module.TARGET_MAP]},
        "dirty_packages_after_save": {"content": [], "maps": []},
        "runtime_validated": False,
        "pie_validated": False,
        "cook_validated": False,
        "packaged_build_validated": False,
        "visual_capture_validated": False,
        "steam_capture_validated": False,
        "steam_visual_quality_human_approved": False,
    }


class PresentationV006SavedMapCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_module()
        cls.contract = cls.module._installer_contract()
        cls.receipt = exact_receipt(cls.module, cls.contract)

    def validate(self, receipt: dict):
        return self.module.validate_install_receipt(
            receipt, MAP_SHA, MAP_BYTES, self.contract
        )

    def test_frozen_installer_plan_camera_and_route_contract(self) -> None:
        self.assertEqual(
            self.module.digest(self.module.INSTALLER), self.module.INSTALLER_SHA256
        )
        self.assertEqual(len(self.contract["plan"]["mutations"]), 83)
        self.assertEqual(self.contract["validation"]["station_port_count"], 12)
        self.assertEqual(
            self.contract["validation"]["station_connector_max_gap_cm"], 0.0
        )
        self.assertEqual(self.module.CAMERA_ROTATION, (-90.0, 0.0, 0.0))
        self.assertEqual(
            {
                item_id: (tuple(spec["location_cm"]), spec["ortho_width_cm"])
                for item_id, spec in self.module.CAMERA_SPECS.items()
            },
            {
                "overview": ((-7436.895880159617, 8840.218280826943, 21712.544), 16200.0),
                "press_spine": ((-8095.0, 11125.0, 21712.544), 11200.0),
                "steam_hero": ((-8855.75, 11092.0, 21712.544), 5700.0),
            },
        )

    def test_exact_synthetic_install_receipt_passes(self) -> None:
        value = self.validate(copy.deepcopy(self.receipt))
        self.assertEqual(len(value["mutations"]), 83)
        self.assertEqual(len(value["candidate_materials"]), 2)
        self.assertEqual(value["validation"]["station_port_count"], 12)

    def test_installed_disk_contract_passes_when_install_is_present(self) -> None:
        if not self.module.TARGET_FILE.is_file() or not self.module.INSTALL_RECEIPT.is_file():
            self.skipTest("v006 installation is intentionally still pending")
        map_sha = self.module.digest(self.module.TARGET_FILE)
        receipt_sha = self.module.digest(self.module.INSTALL_RECEIPT)
        receipt, value = self.module.load_guarded_install_receipt(map_sha, receipt_sha)
        self.assertEqual(receipt["target_map_sha256"], map_sha)
        self.assertEqual(len(value["mutations"]), 83)
        self.assertEqual(len(value["candidate_material_packages"]), 2)
        self.assertEqual(value["validation"]["station_connector_max_gap_cm"], 0.0)

    def test_both_independent_reviewed_hashes_are_mandatory(self) -> None:
        bad_environments = (
            {},
            {self.module.MAP_SHA_ENV: MAP_SHA},
            {self.module.MAP_SHA_ENV: MAP_SHA.upper(),
             self.module.RECEIPT_SHA_ENV: RECEIPT_SHA},
            {self.module.MAP_SHA_ENV: "0" * 64,
             self.module.RECEIPT_SHA_ENV: RECEIPT_SHA},
            {self.module.MAP_SHA_ENV: MAP_SHA,
             self.module.RECEIPT_SHA_ENV: "a" * 64},
            {self.module.MAP_SHA_ENV: MAP_SHA,
             self.module.RECEIPT_SHA_ENV: MAP_SHA},
        )
        for environment in bad_environments:
            with self.subTest(environment=environment):
                with self.assertRaises(self.module.CaptureGuardError):
                    self.module.required_guard_hashes(environment)
        self.assertEqual(
            self.module.required_guard_hashes({
                self.module.MAP_SHA_ENV: MAP_SHA,
                self.module.RECEIPT_SHA_ENV: RECEIPT_SHA,
            }),
            (MAP_SHA, RECEIPT_SHA),
        )

    def test_top_level_inventory_authority_and_pending_flags_fail_closed(self) -> None:
        cases = {
            "schema": "wrong",
            "status": "wrong",
            "candidate_only": False,
            "target_map": "/Game/Wrong",
            "target_map_sha256": "12" * 32,
            "target_map_bytes": MAP_BYTES + 1,
            "source_actor_count": 301,
            "final_actor_count": 301,
            "final_presentation_actor_count": 139,
            "combined_visual_layer_count": 145,
            "machinery_visual_layer_count": 119,
            "cargo_layer_count": 25,
            "machinery_actor_mutated_count": 1,
            "cargo_actor_mutated_count": 1,
            "source_actor_removed_count": 1,
            "source_actor_created_count": 1,
            "mutated_existing_presentation_actor_count": 82,
            "mutated_station_zone_actor_count": 35,
            "mutated_route_actor_count": 28,
            "created_presentation_box_count": 1,
            "machine_or_cargo_transform_mutations": 1,
            "new_machinery_geometry": 1,
            "new_cargo_geometry": 1,
            "native_cpp_modified": True,
            "roof_created": True,
            "game_mode_after": "/Script/Engine.GameModeBase",
            "runtime_validated": True,
            "pie_validated": True,
            "visual_capture_validated": True,
            "steam_visual_quality_human_approved": True,
        }
        for key, value in cases.items():
            with self.subTest(key=key):
                receipt = copy.deepcopy(self.receipt)
                receipt[key] = value
                with self.assertRaises(self.module.CaptureGuardError):
                    self.validate(receipt)

    def test_protected_reused_and_visual_fingerprints_fail_closed(self) -> None:
        for key in (
            "protected_hashes_after", "reused_material_hashes_after",
        ):
            with self.subTest(key=key):
                receipt = copy.deepcopy(self.receipt)
                receipt[key]["unexpected"] = "12" * 32
                with self.assertRaises(self.module.CaptureGuardError):
                    self.validate(receipt)
        for key in (
            "visual_layer_actor_semantic_fingerprints_after_sha256",
            "machinery_actor_semantic_fingerprints_after_sha256",
            "cargo_actor_semantic_fingerprints_after_sha256",
            "source_path_keyed_visual_fingerprints_sha256",
        ):
            with self.subTest(key=key):
                receipt = copy.deepcopy(self.receipt)
                receipt[key] = "45" * 32
                with self.assertRaises(self.module.CaptureGuardError):
                    self.validate(receipt)

    def test_mutation_order_identity_and_actor_path_set_fail_closed(self) -> None:
        receipt = copy.deepcopy(self.receipt)
        receipt["presentation_mutations"].pop()
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)
        receipt = copy.deepcopy(self.receipt)
        receipt["presentation_mutations"][0], receipt["presentation_mutations"][1] = (
            receipt["presentation_mutations"][1], receipt["presentation_mutations"][0]
        )
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)
        receipt = copy.deepcopy(self.receipt)
        receipt["presentation_mutations"][1]["actor_path"] = (
            receipt["presentation_mutations"][0]["actor_path"]
        )
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)

    def test_each_mutation_kind_is_exact_and_collision_is_fail_closed(self) -> None:
        by_kind = {
            kind: next(
                index for index, row in enumerate(self.receipt["presentation_mutations"])
                if row["kind"] == kind
            )
            for kind in ("box", "text", "camera")
        }
        drifts = (
            ("box", "dimensions_cm", [1.0, 2.0, 3.0]),
            ("box", "material", "/Game/Wrong"),
            ("text", "world_size_cm", 1.0),
            ("text", "colour_rgba", [0, 0, 0, 0]),
            ("camera", "ortho_width_cm", 1.0),
            ("camera", "role_tag", "LB.Wrong"),
            ("camera", "location_cm", [0.0, 0.0, 0.0]),
        )
        for kind, key, value in drifts:
            with self.subTest(kind=kind, key=key):
                receipt = copy.deepcopy(self.receipt)
                receipt["presentation_mutations"][by_kind[kind]][key] = value
                with self.assertRaises(self.module.CaptureGuardError):
                    self.validate(receipt)
        for kind in ("box", "text"):
            receipt = copy.deepcopy(self.receipt)
            row = receipt["presentation_mutations"][by_kind[kind]]
            row["collision_readback"]["actor_collision_enabled"] = True
            with self.assertRaises(self.module.CaptureGuardError):
                self.validate(receipt)

    def test_plan_route_and_candidate_material_drift_fail_closed(self) -> None:
        receipt = copy.deepcopy(self.receipt)
        receipt["plan_validation"]["station_port_count"] = 11
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)
        for key, value in (
            ("role", "wrong"), ("srgb_hex", "#000000"),
            ("shading_model", "DEFAULT_LIT"),
            ("linear_rgb_readback", [0.0, 0.0, 0.0]),
            ("sha256", "a" * 64), ("bytes", 0),
        ):
            with self.subTest(key=key):
                receipt = copy.deepcopy(self.receipt)
                receipt["candidate_materials"][0][key] = value
                with self.assertRaises(self.module.CaptureGuardError):
                    self.validate(receipt)
        receipt = copy.deepcopy(self.receipt)
        first_asset = receipt["candidate_materials"][0]["asset"]
        receipt["candidate_material_packages"][first_asset]["bytes"] += 1
        with self.assertRaises(self.module.CaptureGuardError):
            self.validate(receipt)

    def test_hash_mismatch_fails_before_receipt_or_unreal_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "candidate.umap"
            install = root / "receipt.json"
            target.write_bytes(b"candidate")
            install.write_bytes(self.module.canonical_json_bytes({"bad": True}))
            actual_map = self.module.digest(target)
            with mock.patch.object(self.module, "TARGET_FILE", target), \
                    mock.patch.object(self.module, "INSTALL_RECEIPT", install):
                with self.assertRaises(self.module.CaptureGuardError):
                    self.module.load_guarded_install_receipt("12" * 32, RECEIPT_SHA)
                with self.assertRaises(self.module.CaptureGuardError):
                    self.module.load_guarded_install_receipt(actual_map, RECEIPT_SHA)

    def test_append_only_evidence_and_capture_record_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            receipt_path = root / "receipt.json"
            with mock.patch.object(self.module, "CAPTURE_RECEIPT", receipt_path):
                self.module._write_new_receipt({"status": "FIRST"})
                self.assertEqual(
                    receipt_path.read_bytes(),
                    self.module.canonical_json_bytes({"status": "FIRST"}),
                )
                with self.assertRaises(self.module.CaptureGuardError):
                    self.module._write_new_receipt({"status": "SECOND"})

            output = root / "captures"
            output.mkdir()
            rows = []
            for item_id in ("overview", "press_spine", "steam_hero"):
                spec = self.module.CAMERA_SPECS[item_id]
                path = output / spec["filename"]
                path.write_bytes((item_id.encode("ascii") + b"\0") * 20)
                rows.append({
                    "path": path.as_posix(), "sha256": self.module.digest(path),
                    "bytes": path.stat().st_size, "width": 1920, "height": 1080,
                    "camera_id": item_id, "source_camera_label": spec["label"],
                    "projection": "ORTHOGRAPHIC",
                    "ortho_width_cm": spec["ortho_width_cm"],
                })
            with mock.patch.object(self.module, "OUTPUT_DIR", output):
                self.assertEqual(len(self.module.validate_capture_records(rows)), 3)
                drift = copy.deepcopy(rows)
                drift[1]["width"] = 1919
                with self.assertRaises(self.module.CaptureGuardError):
                    self.module.validate_capture_records(drift)
                with self.assertRaises(self.module.CaptureGuardError):
                    self.module.validate_capture_records(rows[:2])

    def test_output_and_asset_paths_are_confined(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            existing = root / "existing"
            existing.mkdir()
            with self.assertRaises(self.module.CaptureGuardError):
                self.module.ensure_output_absent(existing)
            self.module.ensure_output_absent(root / "new")
        self.assertTrue(
            self.module.virtual_to_uasset("/Game/LineBoss/Test").is_relative_to(
                (self.module.PROJECT / "Content").resolve()
            )
        )
        for path in ("/Engine/Test", "/Game/../../escape"):
            with self.assertRaises(self.module.CaptureGuardError):
                self.module.virtual_to_uasset(path)

    def test_source_has_no_content_write_save_import_or_saved_actor_mutator(self) -> None:
        tree = ast.parse(SUBJECT.read_text(encoding="utf-8"))
        attributes = {
            node.func.attr for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        forbidden = {
            "save_current_level", "save_loaded_asset", "save_asset", "save_directory",
            "import_asset_tasks", "create_asset", "new_level_from_template",
            "duplicate_asset", "set_actor_location", "set_actor_rotation",
            "set_actor_scale3d", "set_material", "set_static_mesh",
            "build_light_maps", "cook_content",
        }
        self.assertFalse(forbidden.intersection(attributes))
        open_modes = [
            node.args[0].value for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "open" and node.args
            and isinstance(node.args[0], ast.Constant)
        ]
        self.assertEqual(sorted(open_modes), ["rb", "xb"])
        source = SUBJECT.read_text(encoding="utf-8")
        self.assertIn('"map_save_calls": 0', source)
        self.assertIn('"content_save_calls": 0', source)
        self.assertIn('"content_import_calls": 0', source)

    def test_locked_helper_is_native_scene_capture_to_saved_only(self) -> None:
        self.assertEqual(
            self.module.digest(self.module.BASE_CAPTURE), self.module.BASE_CAPTURE_SHA256
        )
        tree = ast.parse(self.module.BASE_CAPTURE.read_text(encoding="utf-8"))
        function = next(
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_capture_saved_cameras"
        )
        identifiers = {
            node.id for node in ast.walk(function) if isinstance(node, ast.Name)
        }
        identifiers.update(
            node.attr for node in ast.walk(function) if isinstance(node, ast.Attribute)
        )
        for required in (
            "SceneCapture2D", "spawn_actor_from_class", "export_render_target",
            "destroy_actor", "capture_scene",
        ):
            self.assertIn(required, identifiers)
        for forbidden in (
            "save_current_level", "save_loaded_asset", "import_asset_tasks",
            "create_asset",
        ):
            self.assertNotIn(forbidden, identifiers)

    def test_evidence_scope_is_explicitly_not_pie_or_steam(self) -> None:
        self.assertIn("SAVED_MAP", self.module.CAPTURE_STATUS)
        self.assertIn("PIE_AND_STEAM_NOT_VALIDATED", self.module.CAPTURE_STATUS)
        self.assertEqual(self.module.CAPTURE_WIDTH, 1920)
        self.assertEqual(self.module.CAPTURE_HEIGHT, 1080)
        self.assertEqual(len(self.module.CAMERA_SPECS), 3)
        self.assertEqual(len(self.module.SELECTED_SOURCE_IDS), 28)
        self.assertEqual(len(self.module.SELECTED_CARGO_IDS), 11)


if __name__ == "__main__":
    unittest.main(verbosity=2)
