"""Read-only validation and synchronous Steam-evidence capture for Press Shop 2126.

This lane is deliberately a consumer of the guarded v002 map build.  It does
not author, import, duplicate, save, rename, or delete project content.  It
validates the complete source/import/build receipt chain, loads only the
isolated target map, proves the exact 120-layer registry/native adapter/two
camera contract, and captures the two authored orthographic cameras through a
transient native ``SceneCapture2D`` and transient ``TextureRenderTarget2D``.

The PNGs and validation receipt are written beneath ``Saved`` only.  A PASS is
in-engine editor evidence, not packaged-build or human Steam-art approval.
Run from an unrelated clean world (normally ``/Engine/Maps/Entry``) with a
rendering RHI; do not use ``-NullRHI``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
import struct
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
TARGET_MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPlayable_v001/Maps/LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_OverheadPlayable_v001" / "Maps" / "LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001.umap"
SOURCE_MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Factory" / "OneFactory" / "v001" / "Maps" / "LB_MoorcrossWorks_OneFactory_v001.umap"
SOURCE_FILE_SHA256 = "f4e97b33cdfb1f242b2c606a16b4caa05b74b298fdf1b1263d4a4c46d50e8d5c"

GUARD_BUILDER = PROJECT / "Tools" / "build_pressshop_2126_overhead_playable_v002.py"
GUARD_BUILDER_SHA256 = "2fc775a81bd79158c63ae4cb0d733bcf37066bfb4e0b730ebf41b578c50e0372"
BUILD_RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "OverheadPlayable_v001" / "build_receipt_v002.json"
BUILD_RECEIPT_SCHEMA = "cairnwell.press_shop.overhead_playable_map_build_receipt.v002"
BUILD_RECEIPT_STATUS = "PASS_CANDIDATE_MAP_INTEGRATION__NOT_RUNTIME_READY"

OUTPUT_DIR = PROJECT / "Saved" / "PressShop2126" / "SteamEvidence_v002"
OVERVIEW_FILE = OUTPUT_DIR / "PressShop2126_TrueOverhead_Overview_1920x1080_v002.png"
HERO_FILE = OUTPUT_DIR / "PressShop2126_TrueOverhead_PressTrainHero_1920x1080_v002.png"
VALIDATION_RECEIPT = OUTPUT_DIR / "validation_capture_receipt_v002.json"
VALIDATION_SCHEMA = "cairnwell.press_shop.overhead_validation_capture_receipt.v002"
VALIDATION_STATUS = "PASS_IN_ENGINE_SYNCHRONOUS_1920X1080_PRESENTATION_LAYER_CAPTURE__NOT_PACKAGED_BUILD_EVIDENCE"

FULL_CAMERA_LABEL = "CAM | Press Shop 2126 | true-overhead full overview"
HERO_CAMERA_LABEL = "CAM | Press Shop 2126 | true-overhead press-train hero"
CAMERA_LABELS = (FULL_CAMERA_LABEL, HERO_CAMERA_LABEL)
CAPTURE_WIDTH = 1920
CAPTURE_HEIGHT = 1080
MIN_CAPTURE_BYTES = 32768

VISUAL_LAYER_CLASS_PATH = "/Script/LineBossCarFactory.LBPressShopOverheadVisualLayerActor"
PRESENTATION_CLASS_PATH = "/Script/LineBossCarFactory.LBPressShopOverheadPresentationActor"
CAMERA_CLASS_PATH = "/Script/Engine.CameraActor"
VISUAL_LAYER_TAG = "LB.PressShop.Overhead.VisualLayer.v001"
PRESENTATION_TAG = "LB.PressShop.OverheadPresentation.v001"
CAMERA_TAG = "LB.PressShop.Overhead.Camera.v001"
VISUAL_ONLY_TAG = "LB.Environment.VisualOnly"
NOT_WIP_TAG = "LB.NotProcessWIP"
EXPECTED_VISUAL_LAYER_COUNT = 120
EXPECTED_PRESENTATION_COUNT = 1
EXPECTED_CAMERA_COUNT = 2
EXPECTED_MACHINE_BEACON_COUNT = 14
EXPECTED_TASK_LIGHT_COUNT = 4
NUMERIC_TOLERANCE = 0.001
ROLE_ENUM_VALUES = {
    "BASE": 0,
    "FRAME_STATE": 1,
    "WORKPIECE": 2,
    "MOVING_OVERLAY": 3,
    "CONTACT_EFFECT": 4,
    "CYAN_TRANSFER": 5,
    "BEACON_GLOW": 6,
    "TASK_LIGHT_GLOW": 7,
    "CONVEYOR_MOTION": 8,
    "ROBOT_POSE": 9,
}

BUILD_RECEIPT_SHA_ENV = "LB_PRESSSHOP_OVERHEAD_BUILD_RECEIPT_SHA256"
TARGET_MAP_SHA_ENV = "LB_PRESSSHOP_OVERHEAD_TARGET_MAP_SHA256"

UNREAL_STUB = PROJECT / "Intermediate" / "PythonStub" / "unreal.py"
UNREAL_STUB_REQUIRED_TOKENS = (
    "class SceneCapture2D(SceneCapture):",
    "class SceneCaptureComponent2D(SceneCaptureComponent):",
    "def capture_scene(self) -> None:",
    "PRM_USE_SHOW_ONLY_LIST: SceneCapturePrimitiveRenderMode",
    "def show_only_actor_components(self, actor: Actor, include_from_child_actors: bool = False) -> None:",
    "def create_render_target2d(cls, world_context_object: Object, width: int = 256, height: int = 256",
    "def export_render_target(cls, world_context_object: Object, texture_render_target: TextureRenderTarget2D",
    "RTF_RGBA8: TextureRenderTargetFormat",
    "SCS_FINAL_COLOR_LDR: SceneCaptureSource",
    "def spawn_actor_from_class(self, actor_class: Class, location: Vector, rotation: Rotator = [0.000000, 0.000000, 0.000000], transient: bool = False)",
    "- ``projection_type`` (CameraProjectionMode):  [Read-Write]",
    "- ``ortho_width`` (float):  [Read-Write]",
    "- ``texture_target`` (TextureRenderTarget2D):  [Read-Write]",
    "- ``camera_component`` (CameraComponent):  [Read-Only] The camera component for this camera",
    "- ``static_mesh_component`` (StaticMeshComponent):  [Read-Only] Holds the mesh.",
)

EXPECTED_BUILD_RECEIPT_KEYS = {
    "schema", "status", "source_map", "source_map_sha256",
    "source_package_loaded_before_template_creation", "target_creation_api",
    "guarded_recovery_resume",
    "target_map",
    "target_map_sha256", "target_map_bytes", "unified_manifest_sha256",
    "strict_unified_verifier", "animation_effects_contract",
    "animation_effects_contract_sha256", "import_receipt",
    "import_receipt_sha256", "actor_registry", "actor_registry_sha256",
    "native_anchor_registry", "native_anchor_registry_sha256",
    "protected_hashes_before", "protected_hashes_after",
    "current_world_before_target_creation", "dirty_packages_before",
    "dirty_packages_after_asset_preflight", "dirty_packages_before_save",
    "dirty_packages_after_save", "game_mode_before", "game_mode_after",
    "pre_existing_actor_count", "pre_existing_actor_fingerprints_before",
    "pre_existing_actor_fingerprints_after",
    "pre_existing_actor_fingerprints_unchanged",
    "duplicate_gameplay_controllers_spawned",
    "editor_hidden_existing_actor_count", "runtime_superseded_presentation_tag",
    "spawned_visual_layer_count", "candidate_asset_preflight_count",
    "candidate_material_parent_and_sprite_texture_parameters_verified",
    "native_visual_layer_class", "native_presentation_class",
    "editor_preview_policy", "spawned_visual_layers", "presentation_adapter",
    "cameras", "save_scope", "map_integrated", "runtime_validated",
    "runtime_ready", "packaged_build_validated", "steam_capture_validated",
    "unresolved_source_rows",
}


class CaptureGuardError(RuntimeError):
    """The read-only validation/capture lane rejected the current state."""


def fail(message: str) -> None:
    raise CaptureGuardError(
        "PRESSSHOP_2126_OVERHEAD_VALIDATION_CAPTURE_V001_FAIL: " + message
    )


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(
        value, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True,
    ) + "\n").encode("utf-8")


def load_canonical_json(path: Path, context: str) -> Tuple[Dict[str, Any], str, bytes]:
    if not path.is_file():
        fail("{} is missing: {}".format(context, path))
    payload = path.read_bytes()
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail("{} is not valid UTF-8 JSON: {}".format(context, error))
    if not isinstance(value, dict):
        fail(context + " root must be an object")
    if payload != canonical_json_bytes(value):
        fail(context + " is not canonical JSON")
    return value, hashlib.sha256(payload).hexdigest(), payload


def _require_sha(value: Any, context: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        fail(context + " is not a lower-case SHA-256")
    return value


def _close(left: Sequence[float], right: Sequence[float], tolerance: float = NUMERIC_TOLERANCE) -> bool:
    return len(left) == len(right) and all(
        math.isfinite(float(a)) and math.isfinite(float(b))
        and abs(float(a) - float(b)) <= tolerance
        for a, b in zip(left, right)
    )


def _normalise_asset_path(value: Any) -> str:
    text = str(value or "")
    if text.startswith("Class'") and text.endswith("'"):
        text = text[6:-1]
    if "." in text and text.startswith("/Game/"):
        text = text.split(".", 1)[0]
    return text


def _as_path(value: Any, context: str) -> Path:
    if not isinstance(value, str) or not value:
        fail(context + " must be a non-empty path string")
    return Path(value).resolve()


def load_guard_builder() -> Any:
    if not GUARD_BUILDER.is_file() or digest(GUARD_BUILDER) != GUARD_BUILDER_SHA256:
        fail("guard builder is missing or differs from its reviewed hash")
    spec = importlib.util.spec_from_file_location(
        "pressshop_overhead_guard_builder_v002_for_capture_v001", GUARD_BUILDER,
    )
    if spec is None or spec.loader is None:
        fail("could not load the reviewed guard builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    exact = {
        "TARGET_MAP": TARGET_MAP,
        "SOURCE_MAP": SOURCE_MAP,
        "SOURCE_FILE_SHA256": SOURCE_FILE_SHA256,
        "BUILD_RECEIPT_SCHEMA": BUILD_RECEIPT_SCHEMA,
        "BUILD_RECEIPT_STATUS": BUILD_RECEIPT_STATUS,
        "EXPECTED_SPAWN_SPEC_COUNT": EXPECTED_VISUAL_LAYER_COUNT,
        "VISUAL_LAYER_CLASS_PATH": VISUAL_LAYER_CLASS_PATH,
        "PRESENTATION_CLASS_PATH": PRESENTATION_CLASS_PATH,
        "FULL_CAMERA_LABEL": FULL_CAMERA_LABEL,
        "HERO_CAMERA_LABEL": HERO_CAMERA_LABEL,
    }
    for name, expected in exact.items():
        if getattr(module, name, None) != expected:
            fail("reviewed builder contract changed: " + name)
    if Path(module.TARGET_FILE).resolve() != TARGET_FILE.resolve():
        fail("reviewed builder target file changed")
    if Path(module.BUILD_RECEIPT).resolve() != BUILD_RECEIPT.resolve():
        fail("reviewed builder receipt path changed")
    return module


def validate_unreal_stub_contract() -> Dict[str, Any]:
    if not UNREAL_STUB.is_file():
        fail("generated UE 5.8 Python stub is missing")
    text = UNREAL_STUB.read_text(encoding="utf-8", errors="strict")
    missing = [token for token in UNREAL_STUB_REQUIRED_TOKENS if token not in text]
    if missing:
        fail("generated UE 5.8 Python stub lacks required capture APIs: {}".format(missing))
    return {
        "path": UNREAL_STUB.as_posix(),
        "sha256": digest(UNREAL_STUB),
        "required_api_token_count": len(UNREAL_STUB_REQUIRED_TOKENS),
    }


def expected_metadata_readback(metadata: Mapping[str, Any]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for name in (
        "LayerId", "AssemblyId", "MachineId", "LayerRole", "StateId",
        "MotionChannel", "bHasMotionRange", "SequenceFrameIndex",
        "SequenceFrameCount", "bSequenceLoops",
    ):
        value = metadata[name]
        if name == "LayerRole":
            enum_name = re.sub(r"(?<!^)(?=[A-Z])", "_", str(value)).upper()
            if enum_name not in ROLE_ENUM_VALUES:
                fail("unexpected layer-role enum in receipt expectation: " + enum_name)
            result[name] = "<LBPressShopOverheadLayerRole.{}: {}>".format(
                enum_name, ROLE_ENUM_VALUES[enum_name],
            )
        elif name in {"LayerId", "AssemblyId", "MachineId", "StateId", "MotionChannel"}:
            result[name] = "None" if value is None else str(value)
        else:
            result[name] = value
    return result


def _validate_visual_receipt_records(
    records: Any, specs: Sequence[Mapping[str, Any]], builder: Any,
) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(records, list) or len(records) != EXPECTED_VISUAL_LAYER_COUNT:
        fail("build receipt visual-layer record count changed")
    by_id: Dict[str, Mapping[str, Any]] = {}
    expected_by_id = {row["spawn_spec_id"]: row for row in specs}
    for row in records:
        if not isinstance(row, Mapping):
            fail("build receipt visual-layer record is not an object")
        spec_id = row.get("spawn_spec_id")
        if spec_id not in expected_by_id or spec_id in by_id:
            fail("build receipt visual-layer ID set changed")
        spec = expected_by_id[spec_id]
        if row.get("actor_label") != "VIS | " + spec_id:
            fail(spec_id + " build receipt label changed")
        if row.get("class_path") != VISUAL_LAYER_CLASS_PATH:
            fail(spec_id + " build receipt class changed")
        if row.get("plane_asset") != spec["plane_asset"]:
            fail(spec_id + " build receipt plane changed")
        if row.get("material_instance") != spec["expected_material_instance"]:
            fail(spec_id + " build receipt material changed")
        if row.get("collision_enabled") is not False:
            fail(spec_id + " build receipt collision changed")
        if row.get("editor_preview_visible") is not builder.editor_preview_visible(spec["actor_metadata"]):
            fail(spec_id + " build receipt visibility policy changed")
        if row.get("metadata_readback") != expected_metadata_readback(spec["actor_metadata"]):
            fail(spec_id + " build receipt metadata changed")
        transform = row.get("transform")
        expected_transform = spec["world_transform"]
        if not isinstance(transform, Mapping):
            fail(spec_id + " build receipt transform is missing")
        for actual_key, expected_key in (
            ("location_cm", "translation_cm"),
            ("rotation_deg_pitch_yaw_roll", "rotation_deg_pitch_yaw_roll"),
            ("scale3d", "scale3d_for_100cm_unit_plane"),
        ):
            if not _close(transform.get(actual_key, []), expected_transform[expected_key]):
                fail(spec_id + " build receipt transform changed")
        if not isinstance(row.get("actor_path"), str) or TARGET_MAP not in row["actor_path"]:
            fail(spec_id + " build receipt actor path escaped the target map")
        by_id[spec_id] = row
    if set(by_id) != set(expected_by_id):
        fail("build receipt visual-layer registry is incomplete")
    return by_id


def _validate_presentation_receipt(
    record: Any, anchors: Mapping[str, Any],
) -> None:
    if not isinstance(record, Mapping):
        fail("build receipt presentation adapter is missing")
    if record.get("actor_label") != "VIS | Press Shop 2126 | Overhead runtime presentation":
        fail("build receipt presentation label changed")
    if record.get("class_path") != PRESENTATION_CLASS_PATH:
        fail("build receipt presentation class changed")
    if record.get("owns_production_state") is not False:
        fail("build receipt presentation ownership became unsafe")
    if record.get("status_beacon_count") != EXPECTED_MACHINE_BEACON_COUNT:
        fail("build receipt beacon count changed")
    if record.get("task_light_count") != EXPECTED_TASK_LIGHT_COUNT:
        fail("build receipt task-light count changed")
    if not isinstance(record.get("actor_path"), str) or TARGET_MAP not in record["actor_path"]:
        fail("build receipt presentation path escaped the target map")
    expected_beacons = {
        machine_id: list(row["world_anchor_cm"])
        for machine_id, row in anchors["beacons"].items()
    }
    expected_tasks = {
        task_id: list(row["world_anchor_cm"])
        for task_id, row in anchors["task_lights"].items()
    }
    beacon_rows = record.get("machine_beacon_anchor_readbacks")
    task_rows = record.get("task_light_anchor_readbacks")
    if not isinstance(beacon_rows, list) or len(beacon_rows) != EXPECTED_MACHINE_BEACON_COUNT:
        fail("build receipt beacon anchor rows changed")
    if not isinstance(task_rows, list) or len(task_rows) != EXPECTED_TASK_LIGHT_COUNT:
        fail("build receipt task-light anchor rows changed")
    actual_beacons = {
        row.get("machine_id"): row.get("actual_world_cm")
        for row in beacon_rows
        if isinstance(row, Mapping)
    }
    actual_tasks = {
        row.get("task_light_id"): row.get("actual_world_cm")
        for row in task_rows
        if isinstance(row, Mapping)
    }
    if set(actual_beacons) != set(expected_beacons) or set(actual_tasks) != set(expected_tasks):
        fail("build receipt native anchor ID set changed")
    for item_id, expected in expected_beacons.items():
        if not _close(actual_beacons[item_id], expected):
            fail("build receipt beacon anchor changed: " + item_id)
        source_row = next(row for row in beacon_rows if row.get("machine_id") == item_id)
        if not _close(source_row.get("expected_world_cm", []), expected):
            fail("build receipt expected beacon anchor changed: " + item_id)
    for item_id, expected in expected_tasks.items():
        if not _close(actual_tasks[item_id], expected):
            fail("build receipt task-light anchor changed: " + item_id)
        source_row = next(row for row in task_rows if row.get("task_light_id") == item_id)
        if not _close(source_row.get("expected_world_cm", []), expected):
            fail("build receipt expected task-light anchor changed: " + item_id)


def _expected_camera_contract(
    label: str, spawn_info: Mapping[str, Any], builder: Any,
) -> Tuple[Mapping[str, Any], float]:
    if label == FULL_CAMERA_LABEL:
        return spawn_info["full_bounds"], float(builder.FULL_CAMERA_ORTHO_WIDTH_CM)
    if label == HERO_CAMERA_LABEL:
        return spawn_info["hero_bounds"], float(builder.HERO_CAMERA_ORTHO_WIDTH_CM)
    fail("unexpected camera label: " + label)


def _validate_camera_receipt_records(
    records: Any, spawn_info: Mapping[str, Any], builder: Any,
) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(records, list) or len(records) != EXPECTED_CAMERA_COUNT:
        fail("build receipt camera count changed")
    by_label: Dict[str, Mapping[str, Any]] = {}
    for row in records:
        if not isinstance(row, Mapping):
            fail("build receipt camera record is not an object")
        label = row.get("actor_label")
        if label not in CAMERA_LABELS or label in by_label:
            fail("build receipt camera label set changed")
        bounds, width = _expected_camera_contract(label, spawn_info, builder)
        center = bounds["center_xy_cm"]
        expected_location = [center[0], center[1], builder.CAMERA_Z_CM]
        transform = row.get("transform")
        if not isinstance(transform, Mapping):
            fail(label + " build receipt transform is missing")
        if not _close(transform.get("location_cm", []), expected_location):
            fail(label + " build receipt location changed")
        if not _close(transform.get("rotation_deg_pitch_yaw_roll", []), builder.CAMERA_ROTATION):
            fail(label + " build receipt is not true-overhead")
        if not _close(transform.get("scale3d", []), [1.0, 1.0, 1.0]):
            fail(label + " build receipt camera scale changed")
        if row.get("projection") != "ORTHOGRAPHIC":
            fail(label + " build receipt projection changed")
        if not _close([row.get("ortho_width_cm")], [width]):
            fail(label + " build receipt width changed")
        if not _close([row.get("aspect_ratio")], [builder.CAMERA_ASPECT]):
            fail(label + " build receipt aspect changed")
        if row.get("camera_axis_contract") != {
            "screen_right": "+Y", "screen_up": "+X", "view": "-Z",
        }:
            fail(label + " build receipt axis contract changed")
        if row.get("registry_bounds") != bounds:
            fail(label + " build receipt registry bounds changed")
        expected_margins = builder.camera_margins(bounds, width)
        if row.get("margins") != expected_margins:
            fail(label + " build receipt margins changed")
        if not isinstance(row.get("actor_path"), str) or TARGET_MAP not in row["actor_path"]:
            fail(label + " build receipt path escaped the target map")
        by_label[label] = row
    if set(by_label) != set(CAMERA_LABELS):
        fail("build receipt camera registry is incomplete")
    return by_label


def validate_build_receipt(
    receipt: Mapping[str, Any], payload: bytes, receipt_sha256: str,
    target_sha256: str, target_bytes: int, protected_current: Mapping[str, str],
    inputs: Mapping[str, Any], builder: Any,
) -> Dict[str, Any]:
    if payload != canonical_json_bytes(receipt):
        fail("build receipt is not canonical JSON")
    _require_sha(receipt_sha256, "build receipt hash")
    if set(receipt) != EXPECTED_BUILD_RECEIPT_KEYS:
        fail("build receipt field set changed")
    if receipt.get("schema") != BUILD_RECEIPT_SCHEMA or receipt.get("status") != BUILD_RECEIPT_STATUS:
        fail("build receipt schema/status changed")
    if receipt.get("source_map") != SOURCE_MAP or receipt.get("source_map_sha256") != SOURCE_FILE_SHA256:
        fail("build receipt source map contract changed")
    if receipt.get("source_package_loaded_before_template_creation") is not False:
        fail("build receipt says the protected source package was loaded")
    if receipt.get("target_creation_api") != "LevelEditorSubsystem.new_level_from_template":
        fail("build receipt target creation API changed")
    recovery = receipt.get("guarded_recovery_resume")
    if not isinstance(recovery, Mapping) or not isinstance(recovery.get("used"), bool):
        fail("build receipt recovery evidence is missing")
    if recovery["used"]:
        expected_recovery = {
            "used": True,
            "baseline_target_sha256": builder.RECOVERY_BASELINE_TARGET_SHA256,
            "baseline_target_bytes": builder.RECOVERY_BASELINE_TARGET_BYTES,
            "baseline_actor_count": builder.RECOVERY_BASELINE_ACTOR_COUNT,
            "prior_guarded_run_log": builder.RECOVERY_PRIOR_RUN_LOG.as_posix(),
            "prior_guarded_run_log_sha256": builder.RECOVERY_PRIOR_RUN_LOG_SHA256,
            "original_world_before_template_creation": builder.RECOVERY_ORIGINAL_WORLD,
            "reason": "PRIOR_RUN_CREATED_AND_SAVED_PURE_TEMPLATE_THEN_FAILED_BEFORE_EXPLICIT_STAGED_MAP_SAVE",
        }
        if recovery != expected_recovery:
            fail("build receipt recovery evidence changed")
    elif recovery != {"used": False}:
        fail("fresh build receipt carries unexpected recovery evidence")
    if receipt.get("target_map") != TARGET_MAP:
        fail("build receipt target map changed")
    if receipt.get("target_map_sha256") != target_sha256 or receipt.get("target_map_bytes") != target_bytes:
        fail("target map bytes differ from the exact build receipt")
    _require_sha(target_sha256, "target map hash")
    target_pin = os.environ.get(TARGET_MAP_SHA_ENV, "").strip().lower()
    if target_pin and (_require_sha(target_pin, TARGET_MAP_SHA_ENV) != target_sha256):
        fail("target map differs from the explicit environment hash pin")
    receipt_pin = os.environ.get(BUILD_RECEIPT_SHA_ENV, "").strip().lower()
    if receipt_pin and (_require_sha(receipt_pin, BUILD_RECEIPT_SHA_ENV) != receipt_sha256):
        fail("build receipt differs from the explicit environment hash pin")

    if receipt.get("unified_manifest_sha256") != inputs["manifest_sha256"]:
        fail("build receipt unified-manifest link changed")
    if receipt.get("strict_unified_verifier") != inputs["strict_verifier"]:
        fail("build receipt strict-verifier evidence changed")
    if _as_path(receipt.get("animation_effects_contract"), "animation contract").resolve() != inputs["source"]["animation_contract_path"].resolve():
        fail("build receipt animation-contract path changed")
    if receipt.get("animation_effects_contract_sha256") != inputs["source"]["animation_contract_sha256"]:
        fail("build receipt animation-contract hash changed")
    for receipt_path_key, receipt_hash_key, expected_path_key, expected_hash_key in (
        ("import_receipt", "import_receipt_sha256", "import_receipt_path", "import_receipt_sha256"),
        ("actor_registry", "actor_registry_sha256", "actor_registry_path", "actor_registry_sha256"),
        ("native_anchor_registry", "native_anchor_registry_sha256", "anchor_registry_path", "anchor_registry_sha256"),
    ):
        if _as_path(receipt.get(receipt_path_key), receipt_path_key) != Path(inputs[expected_path_key]).resolve():
            fail("build receipt cross-link path changed: " + receipt_path_key)
        if receipt.get(receipt_hash_key) != inputs[expected_hash_key]:
            fail("build receipt cross-link hash changed: " + receipt_hash_key)

    if receipt.get("protected_hashes_before") != protected_current or receipt.get("protected_hashes_after") != protected_current:
        fail("protected file hashes differ from the map-build receipt")
    clean = {"maps": [], "content": []}
    if receipt.get("dirty_packages_before") != clean or receipt.get("dirty_packages_after_asset_preflight") != clean or receipt.get("dirty_packages_after_save") != clean:
        fail("build receipt does not prove a clean preflight/final editor state")
    dirty_pre_save = receipt.get("dirty_packages_before_save")
    if not isinstance(dirty_pre_save, Mapping) or dirty_pre_save.get("content") != []:
        fail("build receipt pre-save dirty-package evidence changed")
    dirty_maps = dirty_pre_save.get("maps")
    if not isinstance(dirty_maps, list) or not dirty_maps or any(
        _normalise_asset_path(value) != TARGET_MAP for value in dirty_maps
    ):
        fail("build receipt did not limit its one save to the target map")
    if _normalise_asset_path(receipt.get("game_mode_before")) != builder.EXPECTED_GAME_MODE or receipt.get("game_mode_after") != receipt.get("game_mode_before"):
        fail("build receipt GameMode evidence changed")

    fingerprints_before = receipt.get("pre_existing_actor_fingerprints_before")
    fingerprints_after = receipt.get("pre_existing_actor_fingerprints_after")
    if not isinstance(fingerprints_before, Mapping) or fingerprints_before != fingerprints_after:
        fail("build receipt pre-existing actor fingerprints changed")
    if receipt.get("pre_existing_actor_count") != len(fingerprints_before) or receipt.get("pre_existing_actor_fingerprints_unchanged") is not True:
        fail("build receipt pre-existing actor count/invariance changed")
    if receipt.get("duplicate_gameplay_controllers_spawned") is not False or receipt.get("editor_hidden_existing_actor_count") != 0:
        fail("build receipt gameplay/visibility safety evidence changed")
    if receipt.get("runtime_superseded_presentation_tag") != builder.SUPERSEDED_PRESENTATION_TAG:
        fail("build receipt superseded-presentation tag changed")

    if receipt.get("spawned_visual_layer_count") != EXPECTED_VISUAL_LAYER_COUNT:
        fail("build receipt visual layer count changed")
    if receipt.get("candidate_asset_preflight_count") != builder.EXPECTED_CREATED_ASSET_COUNT:
        fail("build receipt candidate asset count changed")
    if receipt.get("candidate_material_parent_and_sprite_texture_parameters_verified") is not True:
        fail("build receipt candidate material verification is absent")
    if receipt.get("native_visual_layer_class") != VISUAL_LAYER_CLASS_PATH or receipt.get("native_presentation_class") != PRESENTATION_CLASS_PATH:
        fail("build receipt native class paths changed")
    if receipt.get("editor_preview_policy") != "BASE_WORKPIECE_MOVING_PLUS_OPEN_PRESSES_PARKED_ROBOTS_AND_SEQUENCE_FRAME_ZERO":
        fail("build receipt editor preview policy changed")

    visual_records = _validate_visual_receipt_records(
        receipt.get("spawned_visual_layers"), inputs["source"]["spawn"]["specs"], builder,
    )
    _validate_presentation_receipt(receipt.get("presentation_adapter"), inputs["source"]["anchors"])
    camera_records = _validate_camera_receipt_records(
        receipt.get("cameras"), inputs["source"]["spawn"], builder,
    )
    if receipt.get("save_scope") != {"save_current_level_calls": 1, "target_map_only": True}:
        fail("build receipt save scope changed")
    if receipt.get("map_integrated") is not True:
        fail("build receipt does not mark the candidate map integrated")
    for key in ("runtime_validated", "runtime_ready", "packaged_build_validated", "steam_capture_validated"):
        if receipt.get(key) is not False:
            fail("pre-capture build receipt must keep {} false".format(key))
    unresolved = inputs["source"]["manifest"].get("unresolved_rows", [])
    if receipt.get("unresolved_source_rows") != unresolved:
        fail("build receipt unresolved-source evidence differs from the unified manifest")
    if any(bool(row.get("blocks_candidate_import")) for row in unresolved):
        fail("an unresolved source row blocks candidate import/capture")
    return {
        "visual_records": visual_records,
        "camera_records": camera_records,
        "presentation_record": receipt["presentation_adapter"],
        "pre_existing_fingerprints": dict(fingerprints_before),
    }


def dirty_package_paths() -> Dict[str, List[str]]:
    def normalise(values: Iterable[Any]) -> List[str]:
        result = []
        for value in values or []:
            result.append(str(value.get_name()) if hasattr(value, "get_name") else str(value))
        return sorted(result)
    return {
        "maps": normalise(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
        "content": normalise(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
    }


def _editor_world() -> Any:
    subsystem_type = getattr(unreal, "UnrealEditorSubsystem", None)
    if subsystem_type is None:
        fail("UnrealEditorSubsystem is unavailable")
    subsystem = unreal.get_editor_subsystem(subsystem_type)
    world = subsystem.get_editor_world() if subsystem is not None else None
    if world is None:
        fail("could not resolve the editor world")
    return world


def _actor_subsystem() -> Any:
    subsystem_type = getattr(unreal, "EditorActorSubsystem", None)
    if subsystem_type is None:
        fail("EditorActorSubsystem is unavailable")
    subsystem = unreal.get_editor_subsystem(subsystem_type)
    if subsystem is None:
        fail("could not resolve EditorActorSubsystem")
    return subsystem


def _world_package_name(world: Any) -> str:
    return str(world.get_path_name()).split(".", 1)[0]


def source_world_is_loaded(builder: Any) -> bool:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.scan_paths_synchronous([SOURCE_MAP.rsplit("/", 1)[0]], True, False)
    rows = list(registry.get_assets_by_package_name(unreal.Name(SOURCE_MAP), True) or [])
    world_rows = [
        row for row in rows
        if str(getattr(getattr(row, "asset_class_path", None), "asset_name", "")) == "World"
        or str(getattr(row, "asset_class", "")) == "World"
    ]
    if len(world_rows) != 1:
        fail("protected source World asset did not resolve exactly once")
    return bool(world_rows[0].is_asset_loaded())


def _actor_class_path(actor: Any) -> str:
    cls = actor.get_class()
    return str(cls.get_path_name()) if cls is not None else ""


def _actor_tags(actor: Any) -> set[str]:
    return {str(value) for value in list(actor.get_editor_property("tags") or [])}


def _validate_actor_transform(actor: Any, spec: Mapping[str, Any], builder: Any, context: str) -> None:
    actual = builder.actor_transform_record(actor)
    expected = spec["world_transform"]
    if not _close(actual["location_cm"], expected["translation_cm"]):
        fail(context + " location changed")
    if not builder.actor_rotation_equivalent(actor, expected["rotation_deg_pitch_yaw_roll"]):
        fail(context + " rotation changed")
    if not _close(actual["scale3d"], expected["scale3d_for_100cm_unit_plane"]):
        fail(context + " scale changed")


def _validate_actual_metadata(actor: Any, metadata: Mapping[str, Any], builder: Any, context: str) -> None:
    for source_name in (
        "LayerId", "AssemblyId", "MachineId", "LayerRole", "StateId",
        "MotionChannel", "bHasMotionRange", "SequenceFrameIndex",
        "SequenceFrameCount", "bSequenceLoops",
    ):
        property_name = builder.reflected_property_name(actor, source_name)
        actual = actor.get_editor_property(property_name)
        expected = builder._metadata_value(source_name, metadata[source_name])
        if source_name in {"LayerId", "AssemblyId", "MachineId", "StateId", "MotionChannel"}:
            if str(actual) != ("None" if metadata[source_name] is None else str(metadata[source_name])):
                fail(context + " metadata changed: " + source_name)
        elif actual != expected:
            fail(context + " metadata changed: " + source_name)
    if metadata["bHasMotionRange"] is not False:
        fail(context + " unexpectedly requires a map-authored motion transform")


def _validate_visual_actor(
    actor: Any, spec: Mapping[str, Any], receipt_row: Mapping[str, Any],
    builder: Any,
) -> Dict[str, Any]:
    spec_id = spec["spawn_spec_id"]
    context = "visual layer " + spec_id
    if str(actor.get_actor_label()) != "VIS | " + spec_id:
        fail(context + " label changed")
    if str(actor.get_path_name()) != receipt_row["actor_path"]:
        fail(context + " path differs from the build receipt")
    if _actor_class_path(actor) != VISUAL_LAYER_CLASS_PATH:
        fail(context + " native class changed")
    if _actor_tags(actor) != {VISUAL_LAYER_TAG, VISUAL_ONLY_TAG, NOT_WIP_TAG}:
        fail(context + " tag set changed")
    if bool(actor.get_actor_enable_collision()):
        fail(context + " actor collision is enabled")
    _validate_actor_transform(actor, spec, builder, context)
    _validate_actual_metadata(actor, spec["actor_metadata"], builder, context)
    component = actor.get_editor_property("static_mesh_component")
    if component is None:
        fail(context + " has no static mesh component")
    mesh = component.get_editor_property("static_mesh")
    material = component.get_material(0)
    if mesh is None or _normalise_asset_path(mesh.get_path_name()) != spec["plane_asset"]:
        fail(context + " unit plane changed")
    if material is None or _normalise_asset_path(material.get_path_name()) != spec["expected_material_instance"]:
        fail(context + " material instance changed")
    for property_name, expected in (
        ("generate_overlap_events", False),
        ("can_ever_affect_navigation", False),
        ("cast_shadow", False),
        ("receives_decals", False),
    ):
        if bool(component.get_editor_property(property_name)) is not expected:
            fail(context + " presentation-only component contract changed: " + property_name)
    visible = bool(builder.editor_preview_visible(spec["actor_metadata"]))
    if bool(component.get_editor_property("visible")) is not visible:
        fail(context + " saved component visibility changed")
    if bool(component.get_editor_property("hidden_in_game")) is visible:
        fail(context + " saved hidden-in-game state changed")
    if bool(actor.get_editor_property("hidden")) is visible:
        fail(context + " saved actor hidden state changed")
    return {
        "spawn_spec_id": spec_id,
        "actor_path": str(actor.get_path_name()),
        "editor_preview_visible": visible,
        "metadata_sha256": hashlib.sha256(canonical_json_bytes(spec["actor_metadata"])).hexdigest(),
    }


def _validate_presentation_actor(
    actor: Any, receipt_row: Mapping[str, Any], anchors: Mapping[str, Any],
    builder: Any,
) -> Dict[str, Any]:
    if str(actor.get_actor_label()) != receipt_row["actor_label"] or str(actor.get_path_name()) != receipt_row["actor_path"]:
        fail("native presentation adapter identity changed")
    if _actor_class_path(actor) != PRESENTATION_CLASS_PATH:
        fail("native presentation adapter class changed")
    if _actor_tags(actor) != {PRESENTATION_TAG, VISUAL_ONLY_TAG, NOT_WIP_TAG}:
        fail("native presentation adapter tag set changed")
    if bool(actor.get_actor_enable_collision()):
        fail("native presentation adapter collision is enabled")
    if int(actor.get_status_beacon_count()) != EXPECTED_MACHINE_BEACON_COUNT or int(actor.get_task_light_count()) != EXPECTED_TASK_LIGHT_COUNT:
        fail("native presentation adapter component counts changed")
    owns = getattr(actor, "owns_production_state", None)
    if owns is None:
        reflected = getattr(unreal, "LBPressShopOverheadPresentationActor", None)
        owns = getattr(reflected, "owns_production_state", None) if reflected is not None else None
    if owns is None or bool(owns()):
        fail("native presentation adapter ownership contract is missing or unsafe")
    if not bool(actor.is_presentation_enabled()):
        fail("native presentation adapter is disabled in the saved map")
    beacon_rows = []
    for machine_id, row in sorted(anchors["beacons"].items()):
        component = actor.get_status_beacon(unreal.Name(machine_id))
        if component is None:
            fail("native beacon getter failed: " + machine_id)
        actual = builder._vector_tuple(component.get_world_location())
        if not _close(actual, row["world_anchor_cm"]):
            fail("native beacon anchor changed: " + machine_id)
        beacon_rows.append({"machine_id": machine_id, "world_anchor_cm": list(actual)})
    task_rows = []
    for task_id, row in sorted(anchors["task_lights"].items()):
        component = actor.get_task_light(unreal.Name(task_id))
        if component is None:
            fail("native task-light getter failed: " + task_id)
        actual = builder._vector_tuple(component.get_world_location())
        if not _close(actual, row["world_anchor_cm"]):
            fail("native task-light anchor changed: " + task_id)
        task_rows.append({"task_light_id": task_id, "world_anchor_cm": list(actual)})
    return {
        "actor_path": str(actor.get_path_name()),
        "owns_production_state": False,
        "status_beacon_count": EXPECTED_MACHINE_BEACON_COUNT,
        "task_light_count": EXPECTED_TASK_LIGHT_COUNT,
        "machine_beacons": beacon_rows,
        "task_lights": task_rows,
    }


def _validate_camera_actor(
    actor: Any, receipt_row: Mapping[str, Any], spawn_info: Mapping[str, Any],
    builder: Any,
) -> Dict[str, Any]:
    label = str(actor.get_actor_label())
    if label not in CAMERA_LABELS or label != receipt_row["actor_label"]:
        fail("authored camera identity changed")
    if str(actor.get_path_name()) != receipt_row["actor_path"]:
        fail(label + " path differs from build receipt")
    if _actor_class_path(actor) != CAMERA_CLASS_PATH:
        fail(label + " class changed")
    if _actor_tags(actor) != {CAMERA_TAG, VISUAL_ONLY_TAG, NOT_WIP_TAG}:
        fail(label + " tag set changed")
    bounds, expected_width = _expected_camera_contract(label, spawn_info, builder)
    transform = builder.actor_transform_record(actor)
    expected_location = [bounds["center_xy_cm"][0], bounds["center_xy_cm"][1], builder.CAMERA_Z_CM]
    if not _close(transform["location_cm"], expected_location):
        fail(label + " location changed")
    if not builder.actor_rotation_equivalent(actor, builder.CAMERA_ROTATION):
        fail(label + " is no longer exactly true-overhead")
    if not _close(transform["scale3d"], [1.0, 1.0, 1.0]):
        fail(label + " scale changed")
    component = actor.get_editor_property("camera_component")
    if component is None:
        fail(label + " has no camera component")
    if component.get_editor_property("projection_mode") != unreal.CameraProjectionMode.ORTHOGRAPHIC:
        fail(label + " is not orthographic")
    if not _close([component.get_editor_property("ortho_width")], [expected_width]):
        fail(label + " orthographic width changed")
    if not bool(component.get_editor_property("constrain_aspect_ratio")):
        fail(label + " no longer constrains aspect ratio")
    if not _close([component.get_editor_property("aspect_ratio")], [builder.CAMERA_ASPECT]):
        fail(label + " aspect ratio changed")
    return {
        "actor_path": str(actor.get_path_name()),
        "actor_label": label,
        "transform": transform,
        "projection": "ORTHOGRAPHIC",
        "ortho_width_cm": float(expected_width),
        "aspect_ratio": float(builder.CAMERA_ASPECT),
    }


def validate_loaded_world(
    world: Any, actors: Sequence[Any], receipt: Mapping[str, Any],
    receipt_contract: Mapping[str, Any], inputs: Mapping[str, Any], builder: Any,
) -> Dict[str, Any]:
    if _world_package_name(world) != TARGET_MAP:
        fail("the exact target map is not the current editor world")
    if _normalise_asset_path(builder.world_game_mode_path(world)) != builder.EXPECTED_GAME_MODE:
        fail("target map GameMode changed")
    expected_total = int(receipt["pre_existing_actor_count"]) + EXPECTED_VISUAL_LAYER_COUNT + EXPECTED_PRESENTATION_COUNT + EXPECTED_CAMERA_COUNT
    if len(actors) != expected_total:
        fail("target map actor count changed ({} != {})".format(len(actors), expected_total))

    by_path = {str(actor.get_path_name()): actor for actor in actors}
    if len(by_path) != len(actors):
        fail("target map has duplicate actor paths")
    current_existing: Dict[str, Any] = {}
    for path in receipt_contract["pre_existing_fingerprints"]:
        actor = by_path.get(path)
        if actor is None:
            fail("pre-existing target actor is missing: " + path)
        current_existing[path] = builder.actor_fingerprint(actor)
    if current_existing != receipt_contract["pre_existing_fingerprints"]:
        fail("a pre-existing target actor differs from the map-build receipt")

    visual = [actor for actor in actors if _actor_class_path(actor) == VISUAL_LAYER_CLASS_PATH]
    presentation = [actor for actor in actors if _actor_class_path(actor) == PRESENTATION_CLASS_PATH]
    tagged_cameras = [actor for actor in actors if CAMERA_TAG in _actor_tags(actor)]
    if len(visual) != EXPECTED_VISUAL_LAYER_COUNT:
        fail("target map does not contain exactly 120 native visual-layer actors")
    if len(presentation) != EXPECTED_PRESENTATION_COUNT:
        fail("target map does not contain exactly one native presentation adapter")
    if len(tagged_cameras) != EXPECTED_CAMERA_COUNT:
        fail("target map does not contain exactly two tagged evidence cameras")

    visual_by_label = {str(actor.get_actor_label()): actor for actor in visual}
    visual_records = []
    for spec in inputs["source"]["spawn"]["specs"]:
        label = "VIS | " + spec["spawn_spec_id"]
        actor = visual_by_label.get(label)
        if actor is None:
            fail("registered visual-layer actor is missing: " + label)
        visual_records.append(_validate_visual_actor(
            actor, spec, receipt_contract["visual_records"][spec["spawn_spec_id"]], builder,
        ))
    if len(visual_by_label) != EXPECTED_VISUAL_LAYER_COUNT:
        fail("target map has duplicate visual-layer labels")

    presentation_record = _validate_presentation_actor(
        presentation[0], receipt_contract["presentation_record"],
        inputs["source"]["anchors"], builder,
    )
    cameras_by_label = {str(actor.get_actor_label()): actor for actor in tagged_cameras}
    if set(cameras_by_label) != set(CAMERA_LABELS):
        fail("target map tagged camera label set changed")
    camera_records = {}
    for label in CAMERA_LABELS:
        camera_records[label] = _validate_camera_actor(
            cameras_by_label[label], receipt_contract["camera_records"][label],
            inputs["source"]["spawn"], builder,
        )
    return {
        "all_actors_by_path": by_path,
        "all_actor_fingerprints": {
            path: builder.actor_fingerprint(actor) for path, actor in sorted(by_path.items())
        },
        "visual_records": visual_records,
        "presentation_record": presentation_record,
        "camera_records": camera_records,
        "camera_actors": cameras_by_label,
        "visual_actors": visual,
        "presentation_actor": presentation[0],
    }


def validate_png(path: Path, expected_width: int, expected_height: int) -> Dict[str, Any]:
    if not path.is_file() or path.stat().st_size < MIN_CAPTURE_BYTES:
        fail("capture is missing or implausibly small: " + str(path))
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        fail("capture is not a valid PNG header: " + str(path))
    width, height = struct.unpack(">II", header[16:24])
    if (width, height) != (expected_width, expected_height):
        fail("capture dimensions changed: {}x{}".format(width, height))
    return {
        "path": path.as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
        "width": width,
        "height": height,
    }


def _capture_two_cameras(
    world: Any, actor_subsystem: Any, camera_actors: Mapping[str, Any],
    visual_actors: Sequence[Any], presentation_actor: Any, builder: Any,
) -> List[Dict[str, Any]]:
    for path in (OVERVIEW_FILE, HERO_FILE, VALIDATION_RECEIPT):
        if path.exists():
            fail("refusing to overwrite evidence artifact: " + str(path))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for command in (
        "viewmode lit",
        "r.Streaming.FullyLoadUsedTextures 1",
        "sg.AntiAliasingQuality 4",
        "sg.ShadowQuality 3",
        "r.ScreenPercentage 100",
    ):
        unreal.SystemLibrary.execute_console_command(world, command)
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()

    target = unreal.RenderingLibrary.create_render_target2d(
        world, CAPTURE_WIDTH, CAPTURE_HEIGHT,
        unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.015, 0.015, 0.015, 1.0), False, False,
    )
    if target is None:
        fail("native transient render target creation failed")
    target.set_editor_property("target_gamma", 2.2)
    first_camera = camera_actors[FULL_CAMERA_LABEL]
    capture_actor = actor_subsystem.spawn_actor_from_class(
        unreal.SceneCapture2D, first_camera.get_actor_location(),
        first_camera.get_actor_rotation(), transient=True,
    )
    if capture_actor is None or _actor_class_path(capture_actor) != "/Script/Engine.SceneCapture2D":
        fail("native transient SceneCapture2D creation failed")
    component = capture_actor.get_editor_property("capture_component2d")
    if component is None:
        fail("transient SceneCapture2D has no capture component")
    component.set_editor_property("texture_target", target)
    component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    component.set_editor_property("projection_type", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    component.set_editor_property("capture_every_frame", False)
    component.set_editor_property("capture_on_movement", False)
    component.set_editor_property("post_process_blend_weight", 0.0)
    component.set_editor_property("ignore_screen_percentage", True)
    component.set_editor_property(
        "primitive_render_mode",
        unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST,
    )
    show_only_actors = list(visual_actors) + [presentation_actor]
    if len(show_only_actors) != EXPECTED_VISUAL_LAYER_COUNT + EXPECTED_PRESENTATION_COUNT:
        fail("presentation-only capture actor set changed")
    for actor in show_only_actors:
        component.show_only_actor_components(actor, True)
    capture_plan = (
        (FULL_CAMERA_LABEL, OVERVIEW_FILE),
        (HERO_CAMERA_LABEL, HERO_FILE),
    )
    results: List[Dict[str, Any]] = []
    try:
        for label, output in capture_plan:
            camera = camera_actors[label]
            camera_component = camera.get_editor_property("camera_component")
            capture_actor.set_actor_location(camera.get_actor_location(), False, False)
            capture_actor.set_actor_rotation(camera.get_actor_rotation(), False)
            component.set_editor_property(
                "ortho_width", float(camera_component.get_editor_property("ortho_width")),
            )
            component.capture_scene()
            unreal.RenderingLibrary.export_render_target(
                world, target, str(OUTPUT_DIR), output.name,
            )
            record = validate_png(output, CAPTURE_WIDTH, CAPTURE_HEIGHT)
            record.update({
                "source_camera_label": label,
                "source_camera_path": str(camera.get_path_name()),
                "projection": "ORTHOGRAPHIC",
                "ortho_width_cm": float(camera_component.get_editor_property("ortho_width")),
                "capture_source": "SCS_FINAL_COLOR_LDR",
                "primitive_render_mode": "PRM_USE_SHOW_ONLY_LIST",
                "show_only_actor_count": len(show_only_actors),
            })
            results.append(record)
    finally:
        if capture_actor is not None and not actor_subsystem.destroy_actor(capture_actor):
            fail("failed to destroy transient SceneCapture2D")
    return results


def _write_new_receipt(value: Mapping[str, Any]) -> None:
    try:
        with VALIDATION_RECEIPT.open("xb") as handle:
            handle.write(canonical_json_bytes(value))
    except FileExistsError as error:
        raise CaptureGuardError(
            "refusing to overwrite validation receipt: {}".format(VALIDATION_RECEIPT)
        ) from error


def main() -> None:
    # All disk/source/receipt guards run before the one permitted map load.
    builder = load_guard_builder()
    unreal_stub_evidence = validate_unreal_stub_contract()
    inputs = builder.load_and_validate_inputs()
    protected_before = builder.protected_snapshot()
    if not TARGET_FILE.is_file():
        fail("exact target map file is missing")
    target_sha_before = digest(TARGET_FILE)
    target_bytes = TARGET_FILE.stat().st_size
    build_receipt, build_receipt_sha, build_receipt_payload = load_canonical_json(
        BUILD_RECEIPT, "guarded map-build receipt",
    )
    receipt_contract = validate_build_receipt(
        build_receipt, build_receipt_payload, build_receipt_sha,
        target_sha_before, target_bytes, protected_before, inputs, builder,
    )
    for evidence_path in (OVERVIEW_FILE, HERO_FILE, VALIDATION_RECEIPT):
        if evidence_path.exists():
            fail("refusing to overwrite evidence artifact: " + str(evidence_path))
    if digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
        fail("protected source map hash changed")
    if dirty_package_paths() != {"maps": [], "content": []}:
        fail("editor has dirty packages before validation")
    current_world = _editor_world()
    current_package = _world_package_name(current_world)
    if current_package in {SOURCE_MAP, TARGET_MAP}:
        fail("run from an unrelated clean world; source and target must start unloaded")
    if source_world_is_loaded(builder):
        fail("protected source map package is already loaded")

    candidate_assets = builder.preflight_candidate_assets(inputs)
    if len(candidate_assets) != builder.EXPECTED_CREATED_ASSET_COUNT:
        fail("candidate asset preflight count changed")
    if dirty_package_paths() != {"maps": [], "content": []}:
        fail("candidate asset preflight dirtied a package")
    if source_world_is_loaded(builder):
        fail("candidate asset preflight loaded the protected source map")
    if digest(TARGET_FILE) != target_sha_before:
        fail("candidate asset preflight changed target map bytes")

    # This is the script's only map-loading call.  It never loads the source.
    loaded = unreal.EditorLoadingAndSavingUtils.load_map(TARGET_MAP)
    if not loaded:
        fail("could not load the exact isolated target map")
    world = _editor_world()
    if _world_package_name(world) != TARGET_MAP:
        fail("target map did not become the current editor world")
    if source_world_is_loaded(builder):
        fail("loading the target unexpectedly loaded the protected source package")
    if dirty_package_paths() != {"maps": [], "content": []}:
        fail("target map load dirtied a package")
    if digest(TARGET_FILE) != target_sha_before:
        fail("target map bytes changed during load")

    actor_subsystem = _actor_subsystem()
    actors_before = list(actor_subsystem.get_all_level_actors() or [])
    world_validation = validate_loaded_world(
        world, actors_before, build_receipt, receipt_contract, inputs, builder,
    )
    fingerprints_before = world_validation["all_actor_fingerprints"]
    dirty_before_capture = dirty_package_paths()
    protected_pre_capture = builder.protected_snapshot()
    if protected_pre_capture != protected_before:
        fail("protected files changed before capture")

    captures = _capture_two_cameras(
        world, actor_subsystem, world_validation["camera_actors"],
        world_validation["visual_actors"], world_validation["presentation_actor"],
        builder,
    )

    dirty_after_capture = dirty_package_paths()
    actors_after = list(actor_subsystem.get_all_level_actors() or [])
    fingerprints_after = {
        str(actor.get_path_name()): builder.actor_fingerprint(actor)
        for actor in actors_after
    }
    if fingerprints_after != fingerprints_before:
        fail("target-map actors changed during transient capture")
    allowed_transient_dirty = {
        "maps": [TARGET_MAP],
        "content": [],
    }
    if dirty_before_capture != {"maps": [], "content": []}:
        fail("target map was dirty before transient capture")
    if dirty_after_capture not in ({"maps": [], "content": []}, allowed_transient_dirty):
        fail("transient capture dirtied anything outside the current target package")
    if source_world_is_loaded(builder):
        fail("protected source package became loaded during capture")
    target_sha_after = digest(TARGET_FILE)
    if target_sha_after != target_sha_before:
        fail("target map bytes changed during capture")
    protected_after = builder.protected_snapshot()
    if protected_after != protected_before:
        fail("a protected map/config/native source changed during capture")

    actor_registry_fingerprint = hashlib.sha256(canonical_json_bytes(
        sorted(world_validation["visual_records"], key=lambda row: row["spawn_spec_id"])
    )).hexdigest()
    world_fingerprint = hashlib.sha256(canonical_json_bytes(fingerprints_after)).hexdigest()
    receipt = {
        "schema": VALIDATION_SCHEMA,
        "status": VALIDATION_STATUS,
        "target_map": TARGET_MAP,
        "target_map_sha256_before": target_sha_before,
        "target_map_sha256_after": target_sha_after,
        "target_map_bytes": target_bytes,
        "source_map": SOURCE_MAP,
        "source_map_sha256": SOURCE_FILE_SHA256,
        "source_package_loaded_before_target_load": False,
        "source_package_loaded_after_target_load": False,
        "source_package_loaded_after_capture": False,
        "guard_builder": GUARD_BUILDER.as_posix(),
        "guard_builder_sha256": GUARD_BUILDER_SHA256,
        "unreal_python_stub": unreal_stub_evidence["path"],
        "unreal_python_stub_sha256": unreal_stub_evidence["sha256"],
        "unreal_python_stub_required_api_token_count": unreal_stub_evidence["required_api_token_count"],
        "build_receipt": BUILD_RECEIPT.as_posix(),
        "build_receipt_sha256": build_receipt_sha,
        "import_receipt": Path(inputs["import_receipt_path"]).as_posix(),
        "import_receipt_sha256": inputs["import_receipt_sha256"],
        "actor_registry": Path(inputs["actor_registry_path"]).as_posix(),
        "actor_registry_sha256": inputs["actor_registry_sha256"],
        "native_anchor_registry": Path(inputs["anchor_registry_path"]).as_posix(),
        "native_anchor_registry_sha256": inputs["anchor_registry_sha256"],
        "unified_manifest_sha256": inputs["manifest_sha256"],
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "dirty_packages_before_capture": dirty_before_capture,
        "dirty_packages_after_capture": dirty_after_capture,
        "transient_capture_package_dirty_only": dirty_after_capture == allowed_transient_dirty,
        "actor_count": len(actors_after),
        "candidate_asset_preflight_count": len(candidate_assets),
        "candidate_material_parent_and_sprite_texture_parameters_verified": True,
        "visual_layer_count": EXPECTED_VISUAL_LAYER_COUNT,
        "native_presentation_adapter_count": EXPECTED_PRESENTATION_COUNT,
        "tagged_orthographic_camera_count": EXPECTED_CAMERA_COUNT,
        "visual_layer_registry_fingerprint_sha256": actor_registry_fingerprint,
        "loaded_world_actor_fingerprint_sha256": world_fingerprint,
        "native_presentation_validation": world_validation["presentation_record"],
        "authored_camera_validation": [
            world_validation["camera_records"][label] for label in CAMERA_LABELS
        ],
        "captures": captures,
        "capture_method": "SYNCHRONOUS_NATIVE_SCENECAPTURE2D_SHOW_ONLY_PRESENTATION_LAYERS_TO_TRANSIENT_RTF_RGBA8_THEN_RENDERINGLIBRARY_EXPORT",
        "capture_resolution": [CAPTURE_WIDTH, CAPTURE_HEIGHT],
        "map_load_calls": 1,
        "loaded_map": TARGET_MAP,
        "map_save_calls": 0,
        "content_save_calls": 0,
        "project_content_mutated": False,
        "map_mutated": False,
        "runtime_adapter_structure_validated": True,
        "runtime_simulation_validated": False,
        "runtime_ready": False,
        "in_engine_capture_validated": True,
        "packaged_build_validated": False,
        "steam_visual_quality_human_approved": False,
    }
    _write_new_receipt(receipt)
    unreal.log(
        "PRESSSHOP_2126_OVERHEAD_VALIDATION_CAPTURE_V001_PASS: {} | {}".format(
            OVERVIEW_FILE, HERO_FILE,
        )
    )


if __name__ == "__main__":
    main()
