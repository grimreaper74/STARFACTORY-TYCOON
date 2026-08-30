"""Offline fail-closed tests for the v001 overhead validation/capture lane.

The subject is imported with a blank ``unreal`` module.  No Unreal process is
launched; no map, asset, configuration, Saved receipt, or capture is written.
Tests exercise pure receipt/registry/PNG guards and prove the native calls and
properties used by the script exist in UE 5.8's generated Python stub.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import struct
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SUBJECT = PROJECT / "Tools" / "validate_and_capture_pressshop_2126_overhead_v001.py"


def load_subject_module():
    previous = sys.modules.get("unreal")
    sys.modules["unreal"] = types.ModuleType("unreal")
    try:
        spec = importlib.util.spec_from_file_location(
            "pressshop_overhead_validation_capture_v001_test_subject", SUBJECT,
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        if previous is None:
            sys.modules.pop("unreal", None)
        else:
            sys.modules["unreal"] = previous


MODULE = load_subject_module()
ACTUAL_GUARD_BUILDER_SHA256 = MODULE.digest(MODULE.GUARD_BUILDER)
_previous_unreal = sys.modules.get("unreal")
sys.modules["unreal"] = types.ModuleType("unreal")
try:
    # Keep the remaining offline contract tests runnable while a reviewed
    # builder edit is awaiting its final pin.  The dedicated pin test below
    # still fails closed, with the exact replacement digest in its message.
    with mock.patch.object(
        MODULE, "GUARD_BUILDER_SHA256", ACTUAL_GUARD_BUILDER_SHA256,
    ):
        BUILDER = MODULE.load_guard_builder()
finally:
    if _previous_unreal is None:
        sys.modules.pop("unreal", None)
    else:
        sys.modules["unreal"] = _previous_unreal
MANIFEST = json.loads(BUILDER.UNIFIED_MANIFEST.read_text(encoding="utf-8"))
SOURCE_INFO = BUILDER.validate_unified_manifest(MANIFEST)


def camera_record(label):
    bounds, width = MODULE._expected_camera_contract(label, SOURCE_INFO["spawn"], BUILDER)
    center = bounds["center_xy_cm"]
    safe = label.replace(" | ", "_").replace(" ", "_")
    return {
        "actor_path": MODULE.TARGET_MAP + "." + MODULE.TARGET_MAP.rsplit("/", 1)[-1] + ":PersistentLevel." + safe,
        "actor_label": label,
        "transform": {
            "location_cm": [center[0], center[1], BUILDER.CAMERA_Z_CM],
            "rotation_deg_pitch_yaw_roll": list(BUILDER.CAMERA_ROTATION),
            "scale3d": [1.0, 1.0, 1.0],
        },
        "projection": "ORTHOGRAPHIC",
        "ortho_width_cm": width,
        "aspect_ratio": BUILDER.CAMERA_ASPECT,
        "camera_axis_contract": {"screen_right": "+Y", "screen_up": "+X", "view": "-Z"},
        "registry_bounds": bounds,
        "margins": BUILDER.camera_margins(bounds, width),
    }


def visual_record(index, spec):
    target_name = MODULE.TARGET_MAP.rsplit("/", 1)[-1]
    return {
        "spawn_spec_id": spec["spawn_spec_id"],
        "actor_path": MODULE.TARGET_MAP + "." + target_name + ":PersistentLevel.Visual_{:03d}".format(index),
        "actor_label": "VIS | " + spec["spawn_spec_id"],
        "class_path": MODULE.VISUAL_LAYER_CLASS_PATH,
        "transform": {
            "location_cm": list(spec["world_transform"]["translation_cm"]),
            "rotation_deg_pitch_yaw_roll": list(spec["world_transform"]["rotation_deg_pitch_yaw_roll"]),
            "scale3d": list(spec["world_transform"]["scale3d_for_100cm_unit_plane"]),
        },
        "plane_asset": spec["plane_asset"],
        "material_instance": spec["expected_material_instance"],
        "metadata_readback": MODULE.expected_metadata_readback(spec["actor_metadata"]),
        "editor_preview_visible": BUILDER.editor_preview_visible(spec["actor_metadata"]),
        "collision_enabled": False,
    }


def presentation_record():
    target_name = MODULE.TARGET_MAP.rsplit("/", 1)[-1]
    return {
        "actor_path": MODULE.TARGET_MAP + "." + target_name + ":PersistentLevel.Presentation",
        "actor_label": "VIS | Press Shop 2126 | Overhead runtime presentation",
        "class_path": MODULE.PRESENTATION_CLASS_PATH,
        "owns_production_state": False,
        "status_beacon_count": MODULE.EXPECTED_MACHINE_BEACON_COUNT,
        "task_light_count": MODULE.EXPECTED_TASK_LIGHT_COUNT,
        "machine_beacon_anchor_readbacks": [
            {
                "machine_id": item_id,
                "expected_world_cm": list(row["world_anchor_cm"]),
                "actual_world_cm": list(row["world_anchor_cm"]),
            }
            for item_id, row in sorted(SOURCE_INFO["anchors"]["beacons"].items())
        ],
        "task_light_anchor_readbacks": [
            {
                "task_light_id": item_id,
                "expected_world_cm": list(row["world_anchor_cm"]),
                "actual_world_cm": list(row["world_anchor_cm"]),
            }
            for item_id, row in sorted(SOURCE_INFO["anchors"]["task_lights"].items())
        ],
    }


def fake_inputs():
    manifest_hash = BUILDER.digest(BUILDER.UNIFIED_MANIFEST)
    return {
        "manifest_sha256": manifest_hash,
        "strict_verifier": {
            "manifest_sha256": manifest_hash,
            "runtime_ready": False,
            "unreal_executed": False,
        },
        "source": SOURCE_INFO,
        "import_receipt_path": Path(r"C:\Evidence\IMPORT_RECEIPT_20260823T220000_000001Z.json"),
        "import_receipt_sha256": "1" * 64,
        "actor_registry_path": Path(r"C:\Evidence\ACTOR_SPAWN_SPEC_REGISTRY_v001.json"),
        "actor_registry_sha256": "2" * 64,
        "anchor_registry_path": Path(r"C:\Evidence\NATIVE_PRESENTATION_ANCHOR_REGISTRY_v001.json"),
        "anchor_registry_sha256": "3" * 64,
    }


def guarded_recovery_record():
    return {
        "used": True,
        "baseline_target_sha256": BUILDER.RECOVERY_BASELINE_TARGET_SHA256,
        "baseline_target_bytes": BUILDER.RECOVERY_BASELINE_TARGET_BYTES,
        "baseline_actor_count": BUILDER.RECOVERY_BASELINE_ACTOR_COUNT,
        "prior_guarded_run_log": BUILDER.RECOVERY_PRIOR_RUN_LOG.as_posix(),
        "prior_guarded_run_log_sha256": BUILDER.RECOVERY_PRIOR_RUN_LOG_SHA256,
        "original_world_before_template_creation": BUILDER.RECOVERY_ORIGINAL_WORLD,
        "reason": "PRIOR_RUN_CREATED_AND_SAVED_PURE_TEMPLATE_THEN_FAILED_BEFORE_EXPLICIT_STAGED_MAP_SAVE",
    }


def valid_receipt(inputs, protected, target_sha="a" * 64, target_bytes=1234567):
    existing_path = MODULE.TARGET_MAP + "." + MODULE.TARGET_MAP.rsplit("/", 1)[-1] + ":PersistentLevel.Existing"
    existing = {
        existing_path: {
            "path": existing_path,
            "name": "Existing",
            "label": "Existing",
            "class_path": "/Script/Engine.Actor",
            "transform": {
                "location_cm": [0.0, 0.0, 0.0],
                "rotation_deg_pitch_yaw_roll": [0.0, 0.0, 0.0],
                "scale3d": [1.0, 1.0, 1.0],
            },
            "tags": [],
            "hidden": False,
            "collision_enabled": True,
        },
    }
    return {
        "schema": MODULE.BUILD_RECEIPT_SCHEMA,
        "status": MODULE.BUILD_RECEIPT_STATUS,
        "source_map": MODULE.SOURCE_MAP,
        "source_map_sha256": MODULE.SOURCE_FILE_SHA256,
        "source_package_loaded_before_template_creation": False,
        "target_creation_api": "LevelEditorSubsystem.new_level_from_template",
        "guarded_recovery_resume": guarded_recovery_record(),
        "target_map": MODULE.TARGET_MAP,
        "target_map_sha256": target_sha,
        "target_map_bytes": target_bytes,
        "unified_manifest_sha256": inputs["manifest_sha256"],
        "strict_unified_verifier": inputs["strict_verifier"],
        "animation_effects_contract": inputs["source"]["animation_contract_path"].as_posix(),
        "animation_effects_contract_sha256": inputs["source"]["animation_contract_sha256"],
        "import_receipt": inputs["import_receipt_path"].as_posix(),
        "import_receipt_sha256": inputs["import_receipt_sha256"],
        "actor_registry": inputs["actor_registry_path"].as_posix(),
        "actor_registry_sha256": inputs["actor_registry_sha256"],
        "native_anchor_registry": inputs["anchor_registry_path"].as_posix(),
        "native_anchor_registry_sha256": inputs["anchor_registry_sha256"],
        "protected_hashes_before": dict(protected),
        "protected_hashes_after": dict(protected),
        "current_world_before_target_creation": "/Engine/Maps/Entry",
        "dirty_packages_before": {"maps": [], "content": []},
        "dirty_packages_after_asset_preflight": {"maps": [], "content": []},
        "dirty_packages_before_save": {"maps": [MODULE.TARGET_MAP], "content": []},
        "dirty_packages_after_save": {"maps": [], "content": []},
        "game_mode_before": BUILDER.EXPECTED_GAME_MODE,
        "game_mode_after": BUILDER.EXPECTED_GAME_MODE,
        "pre_existing_actor_count": len(existing),
        "pre_existing_actor_fingerprints_before": existing,
        "pre_existing_actor_fingerprints_after": copy.deepcopy(existing),
        "pre_existing_actor_fingerprints_unchanged": True,
        "duplicate_gameplay_controllers_spawned": False,
        "editor_hidden_existing_actor_count": 0,
        "runtime_superseded_presentation_tag": BUILDER.SUPERSEDED_PRESENTATION_TAG,
        "spawned_visual_layer_count": MODULE.EXPECTED_VISUAL_LAYER_COUNT,
        "candidate_asset_preflight_count": BUILDER.EXPECTED_CREATED_ASSET_COUNT,
        "candidate_material_parent_and_sprite_texture_parameters_verified": True,
        "native_visual_layer_class": MODULE.VISUAL_LAYER_CLASS_PATH,
        "native_presentation_class": MODULE.PRESENTATION_CLASS_PATH,
        "editor_preview_policy": "BASE_WORKPIECE_MOVING_PLUS_OPEN_PRESSES_PARKED_ROBOTS_AND_SEQUENCE_FRAME_ZERO",
        "spawned_visual_layers": [
            visual_record(index, spec)
            for index, spec in enumerate(inputs["source"]["spawn"]["specs"])
        ],
        "presentation_adapter": presentation_record(),
        "cameras": [camera_record(MODULE.FULL_CAMERA_LABEL), camera_record(MODULE.HERO_CAMERA_LABEL)],
        "save_scope": {"save_current_level_calls": 1, "target_map_only": True},
        "map_integrated": True,
        "runtime_validated": False,
        "runtime_ready": False,
        "packaged_build_validated": False,
        "steam_capture_validated": False,
        "unresolved_source_rows": copy.deepcopy(
            inputs["source"]["manifest"].get("unresolved_rows", [])
        ),
    }


def validate(receipt, inputs, protected, target_sha="a" * 64, target_bytes=1234567, payload=None):
    payload = MODULE.canonical_json_bytes(receipt) if payload is None else payload
    return MODULE.validate_build_receipt(
        receipt, payload, hashlib.sha256(payload).hexdigest(), target_sha,
        target_bytes, protected, inputs, BUILDER,
    )


class ExactContractTests(unittest.TestCase):
    def setUp(self):
        self.inputs = fake_inputs()
        self.protected = {"C:/Protected.umap": "f" * 64}
        self.receipt = valid_receipt(self.inputs, self.protected)

    def test_reviewed_builder_and_exact_paths_are_pinned(self):
        self.assertEqual(
            MODULE.GUARD_BUILDER_SHA256,
            ACTUAL_GUARD_BUILDER_SHA256,
            "GUARD_BUILDER_SHA256 must be reviewed and updated to {}".format(
                ACTUAL_GUARD_BUILDER_SHA256,
            ),
        )
        self.assertEqual(MODULE.TARGET_MAP, BUILDER.TARGET_MAP)
        self.assertEqual(MODULE.SOURCE_MAP, BUILDER.SOURCE_MAP)
        self.assertEqual(MODULE.SOURCE_FILE_SHA256, BUILDER.SOURCE_FILE_SHA256)

    def test_complete_valid_build_receipt_passes(self):
        result = validate(self.receipt, self.inputs, self.protected)
        self.assertEqual(len(result["visual_records"]), 120)
        self.assertEqual(set(result["camera_records"]), set(MODULE.CAMERA_LABELS))

    def test_noncanonical_or_extra_field_receipt_fails(self):
        payload = MODULE.canonical_json_bytes(self.receipt) + b"\n"
        with self.assertRaisesRegex(MODULE.CaptureGuardError, "not canonical"):
            validate(self.receipt, self.inputs, self.protected, payload=payload)
        receipt = copy.deepcopy(self.receipt)
        receipt["unexpected"] = True
        with self.assertRaisesRegex(MODULE.CaptureGuardError, "field set changed"):
            validate(receipt, self.inputs, self.protected)

    def test_guarded_recovery_provenance_is_exact(self):
        self.assertEqual(
            self.receipt["guarded_recovery_resume"],
            guarded_recovery_record(),
        )
        for key, replacement in (
            ("baseline_target_sha256", "0" * 64),
            ("baseline_target_bytes", 1),
            ("baseline_actor_count", 1),
            ("prior_guarded_run_log_sha256", "0" * 64),
            ("original_world_before_template_creation", "/Game/Wrong"),
            ("reason", "UNREVIEWED_RECOVERY"),
        ):
            with self.subTest(key=key):
                receipt = copy.deepcopy(self.receipt)
                receipt["guarded_recovery_resume"][key] = replacement
                with self.assertRaisesRegex(
                    MODULE.CaptureGuardError, "recovery evidence changed",
                ):
                    validate(receipt, self.inputs, self.protected)

        receipt = copy.deepcopy(self.receipt)
        receipt["guarded_recovery_resume"] = {
            "used": False,
            "reason": "RECOVERY_FIELDS_MUST_NOT_LEAK_INTO_FRESH_BUILD",
        }
        with self.assertRaisesRegex(
            MODULE.CaptureGuardError, "fresh build receipt carries unexpected recovery evidence",
        ):
            validate(receipt, self.inputs, self.protected)

    def test_exact_target_hash_and_bytes_are_required(self):
        with self.assertRaisesRegex(MODULE.CaptureGuardError, "target map bytes"):
            validate(self.receipt, self.inputs, self.protected, target_sha="b" * 64)
        with self.assertRaisesRegex(MODULE.CaptureGuardError, "target map bytes"):
            validate(self.receipt, self.inputs, self.protected, target_bytes=1)

    def test_optional_external_hash_pins_fail_closed(self):
        with mock.patch.dict(os.environ, {MODULE.TARGET_MAP_SHA_ENV: "b" * 64}, clear=False):
            with self.assertRaisesRegex(MODULE.CaptureGuardError, "environment hash pin"):
                validate(self.receipt, self.inputs, self.protected)
        with mock.patch.dict(os.environ, {MODULE.BUILD_RECEIPT_SHA_ENV: "b" * 64}, clear=False):
            with self.assertRaisesRegex(MODULE.CaptureGuardError, "environment hash pin"):
                validate(self.receipt, self.inputs, self.protected)

    def test_protected_hash_drift_fails(self):
        current = {"C:/Protected.umap": "e" * 64}
        with self.assertRaisesRegex(MODULE.CaptureGuardError, "protected file hashes"):
            validate(self.receipt, self.inputs, current)

    def test_import_and_registry_cross_link_drift_fails(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["actor_registry_sha256"] = "9" * 64
        with self.assertRaisesRegex(MODULE.CaptureGuardError, "cross-link hash"):
            validate(receipt, self.inputs, self.protected)

    def test_visual_metadata_or_transform_drift_fails(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["spawned_visual_layers"][0]["metadata_readback"]["MachineId"] = "WRONG"
        with self.assertRaisesRegex(MODULE.CaptureGuardError, "metadata changed"):
            validate(receipt, self.inputs, self.protected)
        receipt = copy.deepcopy(self.receipt)
        receipt["spawned_visual_layers"][0]["transform"]["location_cm"][0] += 1.0
        with self.assertRaisesRegex(MODULE.CaptureGuardError, "transform changed"):
            validate(receipt, self.inputs, self.protected)

    def test_camera_angle_width_or_label_drift_fails(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["cameras"][0]["transform"]["rotation_deg_pitch_yaw_roll"][0] = -60.0
        with self.assertRaisesRegex(MODULE.CaptureGuardError, "true-overhead"):
            validate(receipt, self.inputs, self.protected)
        receipt = copy.deepcopy(self.receipt)
        receipt["cameras"][1]["ortho_width_cm"] += 1.0
        with self.assertRaisesRegex(MODULE.CaptureGuardError, "width changed"):
            validate(receipt, self.inputs, self.protected)

    def test_presentation_anchor_drift_fails(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["presentation_adapter"]["machine_beacon_anchor_readbacks"][0]["actual_world_cm"][2] += 5.0
        with self.assertRaisesRegex(MODULE.CaptureGuardError, "beacon anchor"):
            validate(receipt, self.inputs, self.protected)

    def test_pre_capture_release_flags_must_be_false(self):
        for key in ("runtime_validated", "runtime_ready", "packaged_build_validated", "steam_capture_validated"):
            receipt = copy.deepcopy(self.receipt)
            receipt[key] = True
            with self.assertRaisesRegex(MODULE.CaptureGuardError, key):
                validate(receipt, self.inputs, self.protected)

    def test_unresolved_source_rows_must_match_manifest_and_not_block_import(self):
        expected = self.inputs["source"]["manifest"].get("unresolved_rows", [])
        self.assertEqual(self.receipt["unresolved_source_rows"], expected)
        self.assertTrue(expected)
        self.assertFalse(any(row["blocks_candidate_import"] for row in expected))

        receipt = copy.deepcopy(self.receipt)
        receipt["unresolved_source_rows"] = []
        with self.assertRaisesRegex(
            MODULE.CaptureGuardError, "unresolved-source evidence differs",
        ):
            validate(receipt, self.inputs, self.protected)

        blocking_inputs = copy.deepcopy(self.inputs)
        blocking_inputs["source"]["manifest"]["unresolved_rows"][0][
            "blocks_candidate_import"
        ] = True
        receipt = valid_receipt(blocking_inputs, self.protected)
        with self.assertRaisesRegex(
            MODULE.CaptureGuardError, "blocks candidate import/capture",
        ):
            validate(receipt, blocking_inputs, self.protected)


class CaptureAndApiProofTests(unittest.TestCase):
    def test_saved_only_output_contract_and_fixed_resolution(self):
        self.assertTrue(str(MODULE.OUTPUT_DIR).startswith(str(PROJECT / "Saved")))
        self.assertEqual((MODULE.CAPTURE_WIDTH, MODULE.CAPTURE_HEIGHT), (1920, 1080))
        self.assertIn("SteamEvidence_v002", MODULE.OUTPUT_DIR.parts)
        self.assertEqual(
            MODULE.VALIDATION_SCHEMA,
            "cairnwell.press_shop.overhead_validation_capture_receipt.v002",
        )
        self.assertIn("PRESENTATION_LAYER_CAPTURE", MODULE.VALIDATION_STATUS)

    def test_png_guard_requires_exact_dimensions_and_minimum_payload(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "proof.png"
            header = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 1920, 1080)
            path.write_bytes(header + b"x" * MODULE.MIN_CAPTURE_BYTES)
            info = MODULE.validate_png(path, 1920, 1080)
            self.assertEqual((info["width"], info["height"]), (1920, 1080))
            with self.assertRaisesRegex(MODULE.CaptureGuardError, "dimensions changed"):
                MODULE.validate_png(path, 1280, 720)

    def test_subject_contains_no_project_save_or_destructive_content_api(self):
        text = SUBJECT.read_text(encoding="utf-8")
        forbidden = (
            "save_current_level(", "save_asset(", "save_loaded_asset(",
            "save_directory(", "save_dirty_packages(", "duplicate_asset(",
            "delete_asset(", "rename_asset(",
        )
        for token in forbidden:
            self.assertNotIn(token, text)
        self.assertIn("map_save_calls\": 0", text)
        self.assertIn("content_save_calls\": 0", text)

    def test_subject_uses_transient_synchronous_native_capture(self):
        text = SUBJECT.read_text(encoding="utf-8")
        for token in (
            "unreal.SceneCapture2D", "transient=True", "create_render_target2d(",
            "TextureRenderTargetFormat.RTF_RGBA8", "component.capture_scene()",
            "RenderingLibrary.export_render_target(",
            "SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST",
            "component.show_only_actor_components(actor, True)",
            '"show_only_actor_count": len(show_only_actors)',
        ):
            self.assertIn(token, text)
        self.assertNotIn("register_slate_post_tick_callback", text)
        self.assertNotIn("take_high_res_screenshot", text)
        self.assertNotIn("get_static_mesh_component()", text)
        self.assertNotIn("get_camera_component()", text)
        self.assertIn('get_editor_property("static_mesh_component")', text)
        self.assertIn('get_editor_property("camera_component")', text)
        self.assertEqual(text.count("EditorLoadingAndSavingUtils.load_map("), 1)
        self.assertIn("load_map(TARGET_MAP)", text)
        self.assertNotIn("load_map(SOURCE_MAP)", text)
        self.assertIn("builder.preflight_candidate_assets(inputs)", text)
        self.assertIn("candidate_material_parent_and_sprite_texture_parameters_verified\": True", text)

    def test_live_transform_validation_uses_builder_quaternion_equivalence(self):
        text = SUBJECT.read_text(encoding="utf-8")
        self.assertIn(
            'builder.actor_rotation_equivalent(actor, expected["rotation_deg_pitch_yaw_roll"])',
            text,
        )
        self.assertIn(
            "builder.actor_rotation_equivalent(actor, builder.CAMERA_ROTATION)",
            text,
        )

    def test_generated_ue58_stub_proves_every_capture_api(self):
        self.assertTrue(MODULE.UNREAL_STUB.is_file())
        evidence = MODULE.validate_unreal_stub_contract()
        self.assertEqual(evidence["sha256"], MODULE.digest(MODULE.UNREAL_STUB))
        self.assertEqual(
            evidence["required_api_token_count"],
            len(MODULE.UNREAL_STUB_REQUIRED_TOKENS),
        )
        stub = MODULE.UNREAL_STUB.read_text(encoding="utf-8", errors="strict")
        for token in MODULE.UNREAL_STUB_REQUIRED_TOKENS:
            self.assertIn(token, stub)


if __name__ == "__main__":
    unittest.main(verbosity=2)
