"""Offline fail-closed tests for the v002 overhead playable-map builder.

These tests import the module with a stub ``unreal`` module.  They validate
disk/source contracts and pure builder logic only; they never execute main(),
launch Unreal, create a map, import an asset, or write a project receipt.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import math
import os
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
BUILDER = PROJECT / "Tools" / "build_pressshop_2126_overhead_playable_v002.py"
V001_BUILDER = PROJECT / "Tools" / "build_pressshop_2126_overhead_playable_v001.py"
UE_STUB = PROJECT / "Intermediate" / "PythonStub" / "unreal.py"


def load_builder_module():
    previous = sys.modules.get("unreal")
    sys.modules["unreal"] = types.ModuleType("unreal")
    try:
        spec = importlib.util.spec_from_file_location("pressshop_overhead_builder_v002_test_subject", BUILDER)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)
        return module
    finally:
        if previous is None:
            sys.modules.pop("unreal", None)
        else:
            sys.modules["unreal"] = previous


MODULE = load_builder_module()


def actual_manifest():
    return json.loads(MODULE.UNIFIED_MANIFEST.read_text(encoding="utf-8"))


def actual_anchor_registry():
    return json.loads(MODULE.SOURCE_ANCHOR_REGISTRY.read_text(encoding="utf-8"))


def validated_actual_source():
    return MODULE.validate_unified_manifest(actual_manifest())


def valid_import_receipt(manifest_hash, actor_hash, anchor_hash, expected_assets):
    return {
        "schema": MODULE.IMPORT_RECEIPT_SCHEMA,
        "result": MODULE.IMPORT_RECEIPT_RESULT,
        "manifest_sha256": manifest_hash,
        "candidate_content_root": MODULE.CANDIDATE_ASSET_ROOT,
        "created_asset_count": len(expected_assets),
        "created_assets": list(expected_assets),
        "actor_spawn_registry_file": MODULE.ACTOR_REGISTRY_NAME,
        "actor_spawn_registry_sha256": actor_hash,
        "actor_spawn_spec_count": MODULE.EXPECTED_SPAWN_SPEC_COUNT,
        "native_presentation_anchor_registry_file": MODULE.ANCHOR_REGISTRY_NAME,
        "native_presentation_anchor_registry_sha256": anchor_hash,
        "native_machine_beacon_count": MODULE.EXPECTED_MACHINE_BEACON_COUNT,
        "native_task_light_count": MODULE.EXPECTED_TASK_LIGHT_COUNT,
        "native_presentation_anchor_setters_configured": False,
        "actor_spawn_performed": False,
        "map_integration_performed": False,
        "runtime_ready": False,
    }


class ExactDiskAndSourceContractTests(unittest.TestCase):
    def test_v001_is_preserved_and_v002_is_separate(self):
        self.assertTrue(V001_BUILDER.is_file())
        self.assertTrue(BUILDER.is_file())
        self.assertNotEqual(V001_BUILDER.resolve(), BUILDER.resolve())
        self.assertIn("PressShop_OverheadRuntime_v001", V001_BUILDER.read_text(encoding="utf-8"))
        self.assertNotIn("PressShop_OverheadRuntime_v001", BUILDER.read_text(encoding="utf-8"))

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
        snapshot = MODULE.protected_snapshot()
        self.assertEqual(snapshot[MODULE.DEFAULT_ENGINE_INI.as_posix()], MODULE.DEFAULT_ENGINE_INI_SHA256)
        self.assertEqual(len(snapshot), len(MODULE.PROTECTED_MAPS) + len(MODULE.PROTECTED_NATIVE_SOURCES) + 1)

    def test_exact_pure_template_recovery_baseline_is_pinned(self):
        self.assertTrue(MODULE.TARGET_FILE.is_file())
        self.assertEqual(
            MODULE.RECOVERY_BASELINE_TARGET_SHA256,
            "0720d3590373ce0aae68aaf81ba5de8dee40f3d2ac59e89963a8faa8ea92b382",
        )
        self.assertEqual(MODULE.RECOVERY_BASELINE_TARGET_BYTES, 33456464)
        self.assertEqual(MODULE.RECOVERY_BASELINE_ACTOR_COUNT, 13702)
        self.assertEqual(MODULE.RECOVERY_ORIGINAL_WORLD, "/Engine/Maps/Entry")
        self.assertTrue(MODULE.RECOVERY_PRIOR_RUN_LOG.is_file())
        self.assertEqual(
            MODULE.RECOVERY_PRIOR_RUN_LOG_SHA256,
            "ddbb78167e170f3744d04eb1befebf16c60cebc63b062602e22ca22d36f002f8",
        )
        self.assertEqual(
            MODULE.digest(MODULE.RECOVERY_PRIOR_RUN_LOG),
            MODULE.RECOVERY_PRIOR_RUN_LOG_SHA256,
        )

        expected_recovery = {
            "used": True,
            "baseline_target_sha256": MODULE.RECOVERY_BASELINE_TARGET_SHA256,
            "baseline_target_bytes": MODULE.RECOVERY_BASELINE_TARGET_BYTES,
            "baseline_actor_count": MODULE.RECOVERY_BASELINE_ACTOR_COUNT,
            "prior_guarded_run_log": MODULE.RECOVERY_PRIOR_RUN_LOG.as_posix(),
            "prior_guarded_run_log_sha256": MODULE.RECOVERY_PRIOR_RUN_LOG_SHA256,
            "original_world_before_template_creation": MODULE.RECOVERY_ORIGINAL_WORLD,
            "reason": "PRIOR_RUN_CREATED_AND_SAVED_PURE_TEMPLATE_THEN_FAILED_BEFORE_EXPLICIT_STAGED_MAP_SAVE",
        }
        if MODULE.BUILD_RECEIPT.is_file():
            payload = MODULE.BUILD_RECEIPT.read_bytes()
            receipt = json.loads(payload.decode("utf-8"))
            self.assertEqual(payload, MODULE.canonical_json_bytes(receipt))
            self.assertEqual(receipt["guarded_recovery_resume"], expected_recovery)
            self.assertEqual(
                receipt["pre_existing_actor_count"],
                MODULE.RECOVERY_BASELINE_ACTOR_COUNT,
            )
            self.assertEqual(
                receipt["current_world_before_target_creation"],
                MODULE.RECOVERY_ORIGINAL_WORLD,
            )
            self.assertEqual(
                MODULE.TARGET_FILE.stat().st_size,
                receipt["target_map_bytes"],
            )
            self.assertEqual(
                MODULE.digest(MODULE.TARGET_FILE),
                receipt["target_map_sha256"],
            )
        else:
            self.assertEqual(
                MODULE.TARGET_FILE.stat().st_size,
                MODULE.RECOVERY_BASELINE_TARGET_BYTES,
            )
            self.assertEqual(
                MODULE.digest(MODULE.TARGET_FILE),
                MODULE.RECOVERY_BASELINE_TARGET_SHA256,
            )

    def test_current_manifest_and_anchor_locks_match(self):
        manifest_hash = MODULE.validate_lock(
            MODULE.UNIFIED_MANIFEST, MODULE.UNIFIED_MANIFEST_LOCK, "manifest",
        )
        anchor_hash = MODULE.validate_lock(
            MODULE.SOURCE_ANCHOR_REGISTRY, MODULE.SOURCE_ANCHOR_LOCK, "anchors",
        )
        self.assertEqual(manifest_hash, MODULE.digest(MODULE.UNIFIED_MANIFEST))
        self.assertEqual(
            anchor_hash,
            "b5ac5980f515f52b567bbe65edcd793f8bfa1c05be0d59c43de89d2bc7baae76",
        )

    def test_strict_unified_verifier_passes_source_only(self):
        result = MODULE._run_strict_verifier()
        self.assertFalse(result["runtime_ready"])
        self.assertFalse(result["unreal_executed"])
        self.assertEqual(result["manifest_sha256"], MODULE.digest(MODULE.UNIFIED_MANIFEST))

    def test_import_actor_registry_is_canonical_array_and_loader_accepts_it(self):
        registry_path = MODULE.IMPORT_RECEIPT_DIR / MODULE.ACTOR_REGISTRY_NAME
        registry, registry_hash, payload = MODULE.load_json_array(
            registry_path, "import actor registry"
        )
        self.assertIsInstance(registry, list)
        self.assertEqual(len(registry), MODULE.EXPECTED_SPAWN_SPEC_COUNT)
        self.assertEqual(payload, MODULE.canonical_json_bytes(registry))
        self.assertEqual(registry_hash, MODULE.digest(registry_path))

        with tempfile.TemporaryDirectory() as temp_dir:
            object_path = Path(temp_dir) / "object.json"
            object_path.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(MODULE.BuildGuardError, "root must be an array"):
                MODULE.load_json_array(object_path, "array fixture")

    def test_installed_ue58_stub_supports_selected_level_and_component_apis(self):
        self.assertTrue(UE_STUB.is_file())
        stub = UE_STUB.read_text(encoding="utf-8", errors="strict")
        self.assertIn(
            "def new_level_from_template(self, asset_path: str, template_asset_path: str) -> bool:",
            stub,
        )
        self.assertIn("static_mesh_component (StaticMeshComponent):", stub)
        self.assertIn("camera_component (CameraComponent):", stub)


class UnifiedRegistryValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = actual_manifest()
        cls.info = validated_actual_source()

    def test_current_unified_contract_counts_and_bounds(self):
        spawn = self.info["spawn"]
        self.assertEqual(len(spawn["specs"]), 120)
        self.assertEqual(len(spawn["texture_asset_ids"]), 112)
        self.assertEqual(len(self.info["expected_created_assets"]), 226)
        self.assertEqual(spawn["role_counts"], {
            "Base": 9,
            "ConveyorMotion": 76,
            "FrameState": 20,
            "MovingOverlay": 6,
            "RobotPose": 8,
            "Workpiece": 1,
        })
        self.assertTrue(MODULE._close_tuple(
            spawn["full_bounds"]["center_xy_cm"],
            (-7730.645880159617, 8840.218280826943),
            tolerance=0.00001,
        ))
        self.assertTrue(MODULE._close_tuple(
            spawn["full_bounds"]["span_xy_cm"],
            (4228.530043476583, 15327.612442141939),
            tolerance=0.00001,
        ))
        self.assertGreater(spawn["full_camera_margins"]["screen_horizontal_world_y_cm"], 1100.0)
        self.assertGreater(spawn["full_camera_margins"]["screen_vertical_world_x_cm"], 2800.0)

    def test_press_hero_bounds_and_true_overhead_axis_contract(self):
        spawn = self.info["spawn"]
        self.assertTrue(MODULE._close_tuple(
            spawn["hero_bounds"]["center_xy_cm"],
            (-8980.52275, 11745.762241412212),
            tolerance=0.00001,
        ))
        margins = MODULE.camera_margins(spawn["hero_bounds"], 10800.0)
        self.assertGreater(margins["screen_horizontal_world_y_cm"], 600.0)
        self.assertGreater(margins["screen_vertical_world_x_cm"], 2100.0)
        # The v001 camera is thousands of centimetres from the integrated lane.
        stale = (8800.0, 1600.0)
        current = spawn["full_bounds"]["center_xy_cm"]
        self.assertGreater(abs(stale[0] - current[0]), 16000.0)
        self.assertGreater(abs(stale[1] - current[1]), 7000.0)

    def test_duplicate_spawn_spec_fails(self):
        specs = copy.deepcopy(self.manifest["actor_spawn_specs"])
        specs[1]["spawn_spec_id"] = specs[0]["spawn_spec_id"]
        with self.assertRaisesRegex(MODULE.BuildGuardError, "duplicate spawn_spec_id"):
            MODULE.validate_spawn_specs(specs)

    def test_incomplete_sequence_fails(self):
        specs = copy.deepcopy(self.manifest["actor_spawn_specs"])
        target = next(
            row for row in specs
            if row["actor_metadata"]["SequenceFrameCount"] > 0
            and row["actor_metadata"]["SequenceFrameIndex"] == 7
        )
        specs.remove(target)
        specs.append(copy.deepcopy(next(row for row in specs if row["actor_metadata"]["SequenceFrameCount"] == 0)))
        specs[-1]["spawn_spec_id"] = "LAYER_TEST_REPLACEMENT"
        specs[-1]["texture_asset_id"] = target["texture_asset_id"]
        with self.assertRaisesRegex(MODULE.BuildGuardError, "sequence group is incomplete"):
            MODULE.validate_spawn_specs(specs)

    def test_false_motion_range_cannot_carry_endpoint(self):
        specs = copy.deepcopy(self.manifest["actor_spawn_specs"])
        specs[0]["actor_metadata"]["MotionStart"] = {
            "translation_cm": [0, 0, 0],
            "rotation_deg_pitch_yaw_roll": [0, 0, 0],
            "scale3d": [1, 1, 1],
        }
        with self.assertRaisesRegex(MODULE.BuildGuardError, "false motion range"):
            MODULE.validate_spawn_specs(specs)

    def test_source_only_flags_are_required(self):
        manifest = copy.deepcopy(self.manifest)
        manifest["runtime_ready"] = True
        with self.assertRaisesRegex(MODULE.BuildGuardError, "must remain source-only"):
            MODULE.validate_unified_manifest(manifest)

    def test_editor_preview_is_deterministic(self):
        by_role = {}
        for row in self.manifest["actor_spawn_specs"]:
            by_role.setdefault(row["actor_metadata"]["LayerRole"], []).append(row["actor_metadata"])
        self.assertTrue(MODULE.editor_preview_visible(by_role["Base"][0]))
        self.assertTrue(MODULE.editor_preview_visible(next(row for row in by_role["FrameState"] if row["StateId"] == "OPEN")))
        self.assertFalse(MODULE.editor_preview_visible(next(row for row in by_role["FrameState"] if row["StateId"] == "CONTACT")))
        self.assertTrue(MODULE.editor_preview_visible(next(row for row in by_role["RobotPose"] if row["StateId"] == "PARKED")))
        self.assertFalse(MODULE.editor_preview_visible(next(row for row in by_role["RobotPose"] if row["StateId"] == "PICK")))
        sequence = by_role["ConveyorMotion"]
        self.assertTrue(MODULE.editor_preview_visible(next(row for row in sequence if row["SequenceFrameIndex"] == 0)))
        self.assertFalse(MODULE.editor_preview_visible(next(row for row in sequence if row["SequenceFrameIndex"] == 1)))


class NativeAnchorAndReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.anchor = actual_anchor_registry()
        cls.source = validated_actual_source()

    def test_all_native_setters_are_ready_and_exact(self):
        info = MODULE.validate_anchor_registry(self.anchor)
        self.assertEqual(set(info["beacons"]), MODULE.EXPECTED_MACHINE_BEACONS)
        self.assertEqual(set(info["task_lights"]), MODULE.EXPECTED_TASK_LIGHTS)
        self.assertEqual(len(info["beacons"]), 14)
        self.assertEqual(len(info["task_lights"]), 4)
        self.assertEqual(info["beacons"]["S07_INSPECTION"]["world_anchor_cm"][2], 180.0)
        self.assertEqual(info["beacons"]["S07_PALLETISER"]["world_anchor_cm"][2], 220.0)
        self.assertEqual(info["task_lights"]["S07_PALLETISER_TASK"]["world_anchor_cm"][2], 360.0)

    def test_anchor_companion_is_canonical_and_embedded_identically(self):
        payload = MODULE.SOURCE_ANCHOR_REGISTRY.read_bytes()
        self.assertEqual(payload, MODULE.canonical_json_bytes(self.anchor))
        self.assertEqual(self.anchor, actual_manifest()["native_presentation_anchor_registry"])

    def test_unready_or_wrong_s07_z_anchor_fails(self):
        anchor = copy.deepcopy(self.anchor)
        target = next(row for row in anchor["machine_beacons"] if row["machine_id"] == "S07_INSPECTION")
        target["setter_ready"] = False
        with self.assertRaisesRegex(MODULE.BuildGuardError, "not setter-ready"):
            MODULE.validate_anchor_registry(anchor)
        anchor = copy.deepcopy(self.anchor)
        target = next(row for row in anchor["task_lights"] if row["task_light_id"] == "S07_PALLETISER_TASK")
        target["world_anchor_cm"][2] = 0.0
        with self.assertRaisesRegex(MODULE.BuildGuardError, "candidate Z changed"):
            MODULE.validate_anchor_registry(anchor)

    def test_import_receipt_exact_cross_links_pass(self):
        manifest_hash = MODULE.digest(MODULE.UNIFIED_MANIFEST)
        actor_payload = MODULE.canonical_json_bytes(self.source["spawn"]["specs"])
        anchor_payload = MODULE.canonical_json_bytes(self.anchor)
        actor_hash = __import__("hashlib").sha256(actor_payload).hexdigest()
        anchor_hash = __import__("hashlib").sha256(anchor_payload).hexdigest()
        self.assertEqual(actor_hash, "818c28b02dc8be0b59d742dcabb75a1d7fd2475b8dd6bb255378830257d5da1f")
        receipt = valid_import_receipt(
            manifest_hash, actor_hash, anchor_hash, self.source["expected_created_assets"],
        )
        MODULE.validate_import_receipt(
            receipt, manifest_hash, actor_hash, anchor_hash,
            self.source["expected_created_assets"],
        )

    def test_receipt_map_or_anchor_claim_fails(self):
        manifest_hash = MODULE.digest(MODULE.UNIFIED_MANIFEST)
        actor_hash = __import__("hashlib").sha256(
            MODULE.canonical_json_bytes(self.source["spawn"]["specs"]),
        ).hexdigest()
        anchor_hash = MODULE.digest(MODULE.SOURCE_ANCHOR_REGISTRY)
        receipt = valid_import_receipt(
            manifest_hash, actor_hash, anchor_hash, self.source["expected_created_assets"],
        )
        receipt["map_integration_performed"] = True
        with self.assertRaisesRegex(MODULE.BuildGuardError, "keep map_integration_performed false"):
            MODULE.validate_import_receipt(
                receipt, manifest_hash, actor_hash, anchor_hash,
                self.source["expected_created_assets"],
            )
        receipt = valid_import_receipt(
            manifest_hash, actor_hash, "0" * 64, self.source["expected_created_assets"],
        )
        with self.assertRaisesRegex(MODULE.BuildGuardError, "anchor registry cross-link"):
            MODULE.validate_import_receipt(
                receipt, manifest_hash, actor_hash, anchor_hash,
                self.source["expected_created_assets"],
            )

    def test_import_receipt_discovery_is_fail_closed(self):
        old = os.environ.pop(MODULE.IMPORT_RECEIPT_ENV, None)
        try:
            with tempfile.TemporaryDirectory() as temp:
                directory = Path(temp)
                with self.assertRaisesRegex(MODULE.BuildGuardError, "exactly one"):
                    MODULE.discover_import_receipt(directory)
                first = directory / "IMPORT_RECEIPT_20260823T120000_000001Z.json"
                first.write_text("{}", encoding="utf-8")
                self.assertEqual(MODULE.discover_import_receipt(directory), first)
                second = directory / "IMPORT_RECEIPT_20260823T120000_000002Z.json"
                second.write_text("{}", encoding="utf-8")
                with self.assertRaisesRegex(MODULE.BuildGuardError, "exactly one"):
                    MODULE.discover_import_receipt(directory)
        finally:
            if old is not None:
                os.environ[MODULE.IMPORT_RECEIPT_ENV] = old


class PureReflectionHelperTests(unittest.TestCase):
    def test_bool_b_prefix_property_fallback_is_explicit(self):
        class Fake:
            def get_editor_property(self, name):
                if name == "b_has_motion_range":
                    return False
                raise RuntimeError(name)

        self.assertEqual(
            MODULE.reflected_property_name(Fake(), "bHasMotionRange"),
            "b_has_motion_range",
        )

    def test_canonical_json_rejects_nan(self):
        with self.assertRaises(ValueError):
            MODULE.canonical_json_bytes({"bad": float("nan")})

    def test_orientation_comparison_uses_quaternion_angular_distance(self):
        class FakeQuaternion:
            def __init__(self, distance_radians):
                self.distance_radians = distance_radians
                self.compared_with = None

            def angular_distance(self, other):
                self.compared_with = other
                return self.distance_radians

        class FakeRotation:
            def __init__(self, quaternion):
                self.value = quaternion

            def quaternion(self):
                return self.value

        class FakeActor:
            def __init__(self, quaternion):
                self.rotation = FakeRotation(quaternion)

            def get_actor_rotation(self):
                return self.rotation

        expected_quaternion = object()
        equivalent = FakeQuaternion(0.0)
        different = FakeQuaternion(math.radians(MODULE.NUMERIC_TOLERANCE * 2.0))
        with mock.patch.object(
            MODULE,
            "_make_rotator",
            return_value=FakeRotation(expected_quaternion),
        ):
            self.assertTrue(MODULE.actor_rotation_equivalent(
                FakeActor(equivalent), (0.0, 180.0, 0.0),
            ))
            self.assertFalse(MODULE.actor_rotation_equivalent(
                FakeActor(different), (0.0, 180.0, 0.0),
            ))
        self.assertIs(equivalent.compared_with, expected_quaternion)
        self.assertIs(different.compared_with, expected_quaternion)

    def test_canonical_transform_records_registry_euler_after_orientation_proof(self):
        actor = object()
        readback = {
            "location_cm": [1.0, 2.0, 3.0],
            "rotation_deg_pitch_yaw_roll": [180.0, 0.0, 180.0],
            "scale3d": [1.0, 1.0, 1.0],
        }
        canonical_rotation = (0.0, 180.0, 0.0)
        with mock.patch.object(MODULE, "actor_rotation_equivalent", return_value=True), mock.patch.object(
            MODULE, "actor_transform_record", return_value=copy.deepcopy(readback),
        ):
            record = MODULE.canonical_transform_record(actor, canonical_rotation)
        self.assertEqual(
            record["rotation_deg_pitch_yaw_roll"],
            list(canonical_rotation),
        )


class MutationSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = BUILDER.read_text(encoding="utf-8")
        cls.main_body = cls.source[cls.source.index("def main()") :]

    def test_all_preflights_precede_target_template_creation(self):
        validate_index = self.main_body.index("load_and_validate_inputs()")
        assets_index = self.main_body.index("preflight_candidate_assets(inputs)")
        create_index = self.main_body.index("new_level_from_template(TARGET_MAP, SOURCE_MAP)")
        self.assertLess(validate_index, assets_index)
        self.assertLess(assets_index, create_index)

    def test_guarded_recovery_requires_exact_baseline_and_reviewed_provenance(self):
        baseline_size_index = self.main_body.index(
            "TARGET_FILE.stat().st_size != RECOVERY_BASELINE_TARGET_BYTES"
        )
        baseline_hash_index = self.main_body.index(
            "digest(TARGET_FILE) != RECOVERY_BASELINE_TARGET_SHA256"
        )
        prior_log_index = self.main_body.index(
            "digest(RECOVERY_PRIOR_RUN_LOG) != RECOVERY_PRIOR_RUN_LOG_SHA256"
        )
        asset_preflight_index = self.main_body.index("preflight_candidate_assets(inputs)")
        spawn_index = self.main_body.index("spawn_visual_layers(")
        for guard_index in (baseline_size_index, baseline_hash_index, prior_log_index):
            self.assertLess(guard_index, asset_preflight_index)
            self.assertLess(guard_index, spawn_index)

        for token in (
            "target_file_exists != target_asset_exists",
            "exact recovery target must be the current editor world",
            "recovery target actor count differs from the pinned pure-template baseline",
            '"baseline_target_sha256": RECOVERY_BASELINE_TARGET_SHA256',
            '"baseline_target_bytes": RECOVERY_BASELINE_TARGET_BYTES',
            '"baseline_actor_count": RECOVERY_BASELINE_ACTOR_COUNT',
            '"prior_guarded_run_log": RECOVERY_PRIOR_RUN_LOG.as_posix()',
            '"prior_guarded_run_log_sha256": RECOVERY_PRIOR_RUN_LOG_SHA256',
            '"original_world_before_template_creation": RECOVERY_ORIGINAL_WORLD',
            '"reason": "PRIOR_RUN_CREATED_AND_SAVED_PURE_TEMPLATE_THEN_FAILED_BEFORE_EXPLICIT_STAGED_MAP_SAVE"',
            '"guarded_recovery_resume": recovery_evidence',
        ):
            self.assertIn(token, self.main_body)

    def test_spawn_and_camera_readbacks_use_orientation_equivalence(self):
        helper_body = self.source[
            self.source.index("def actor_rotation_equivalent("):
            self.source.index("def canonical_transform_record(")
        ]
        self.assertGreaterEqual(helper_body.count(".quaternion()"), 2)
        self.assertIn("actual.angular_distance(expected)", helper_body)
        self.assertIn(
            'actor_rotation_equivalent(actor, transform["rotation_deg_pitch_yaw_roll"])',
            self.source,
        )
        self.assertIn("actor_rotation_equivalent(actor, CAMERA_ROTATION)", self.source)
        self.assertIn(
            'canonical_transform_record(\n            actor, transform["rotation_deg_pitch_yaw_roll"],',
            self.source,
        )
        self.assertIn("canonical_transform_record(actor, CAMERA_ROTATION)", self.source)

    def test_no_destructive_import_broad_save_or_config_write(self):
        forbidden = (
            "delete_asset(", "delete_directory(", "rename_asset(", "destroy_actor(",
            "save_directory(", "save_loaded_assets(", "save_asset(", "AssetImportTask",
            "import_asset_tasks", "set_actor_hidden_in_game(", "set_is_temporarily_hidden_in_editor(",
            "default_game_mode\",",
        )
        for token in forbidden:
            self.assertNotIn(token, self.source, token)
        self.assertEqual(self.source.count("new_level_from_template(TARGET_MAP, SOURCE_MAP)"), 1)
        self.assertNotIn("duplicate_asset(SOURCE_MAP, TARGET_MAP)", self.source)
        self.assertNotIn("load_map(TARGET_MAP)", self.source)
        self.assertEqual(self.source.count("save_current_level()"), 1)
        self.assertNotIn("PressShop_OverheadRuntime_v001", self.source)

    def test_spawns_only_native_presentation_classes_and_cameras(self):
        self.assertIn(MODULE.VISUAL_LAYER_CLASS_PATH, self.source)
        self.assertIn(MODULE.PRESENTATION_CLASS_PATH, self.source)
        self.assertIn(MODULE.CAMERA_CLASS_PATH, self.source)
        self.assertNotIn("unreal.StaticMeshActor", self.source)
        self.assertNotIn("spawn_actor_from_object", self.source)
        self.assertNotIn("spawn_duplicate_controllers", self.source)
        self.assertIn("duplicate_gameplay_controllers_spawned", self.source)

    def test_component_access_uses_ue58_reflected_properties(self):
        self.assertIn('get_editor_property("static_mesh_component")', self.source)
        self.assertIn('get_editor_property("camera_component")', self.source)
        self.assertNotIn("get_static_mesh_component()", self.source)
        self.assertNotIn("get_camera_component()", self.source)

    def test_presentation_hide_is_runtime_exact_tag_only(self):
        self.assertIn(MODULE.SUPERSEDED_PRESENTATION_TAG, self.source)
        self.assertIn("editor_hidden_existing_actor_count", self.source)
        self.assertIn("superseded runtime presentation is unexpectedly map-authored", self.source)
        self.assertNotIn("hide_presentation_actors", self.source)

    def test_receipt_is_exclusive_create_and_honest(self):
        self.assertIn('path.open("xb")', self.source)
        self.assertIn('"runtime_validated": False', self.source)
        self.assertIn('"runtime_ready": False', self.source)
        self.assertIn('"packaged_build_validated": False', self.source)
        self.assertIn('"steam_capture_validated": False', self.source)


if __name__ == "__main__":
    unittest.main()
