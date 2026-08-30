"""Guarded v002 builder for the isolated 2126 true-overhead Press Shop.

The builder is deliberately a consumer.  The source-manifest lane authors and
hash-locks registration data; the import lane creates candidate content assets
and immutable receipts.  This script creates an isolated level from the
unopened OneFactory template, stages native presentation actors in that
candidate, and saves that map once.  It never imports assets, changes
configuration, creates gameplay
authorities, or edits a protected/source map.

Run only from Unreal Python after the guarded import receipt exists.  The
editor must be on an unrelated clean world.  Every disk/data/asset/class gate
runs before the target package is created.  A failure after creation leaves
the target in place for human review; this script never performs destructive
rollback and never overwrites a target or receipt.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CODEX_OUTPUTS = Path(r"C:\Users\greg_\Documents\Codex\2026-08-22\ca\outputs")

SOURCE_MAP = "/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001"
TARGET_MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPlayable_v001/Maps/LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Factory" / "OneFactory" / "v001" / "Maps" / "LB_MoorcrossWorks_OneFactory_v001.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_OverheadPlayable_v001" / "Maps" / "LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001.umap"
SOURCE_FILE_SHA256 = "f4e97b33cdfb1f242b2c606a16b4caa05b74b298fdf1b1263d4a4c46d50e8d5c"
RECOVERY_BASELINE_TARGET_SHA256 = "0720d3590373ce0aae68aaf81ba5de8dee40f3d2ac59e89963a8faa8ea92b382"
RECOVERY_BASELINE_TARGET_BYTES = 33456464
RECOVERY_BASELINE_ACTOR_COUNT = 13702
RECOVERY_PRIOR_RUN_LOG = PROJECT / "Saved" / "Logs" / "PressShop2126_OverheadPlayable_Build_v002_templatefix.log"
RECOVERY_PRIOR_RUN_LOG_SHA256 = "ddbb78167e170f3744d04eb1befebf16c60cebc63b062602e22ca22d36f002f8"
RECOVERY_ORIGINAL_WORLD = "/Engine/Maps/Entry"

SOURCE_PACKAGE = CODEX_OUTPUTS / "PressShop_OverheadSourceManifest_v001"
UNIFIED_MANIFEST = SOURCE_PACKAGE / "PRESS_SHOP_OVERHEAD_SOURCE_MANIFEST_v001.json"
UNIFIED_MANIFEST_LOCK = SOURCE_PACKAGE / "PRESS_SHOP_OVERHEAD_SOURCE_MANIFEST_v001.sha256"
UNIFIED_STRICT_VERIFIER = SOURCE_PACKAGE / "verify_unified_source_manifest_v001.py"
SOURCE_ANCHOR_REGISTRY = SOURCE_PACKAGE / "NATIVE_PRESENTATION_ANCHOR_REGISTRY_v001.json"
SOURCE_ANCHOR_LOCK = SOURCE_PACKAGE / "NATIVE_PRESENTATION_ANCHOR_REGISTRY_v001.sha256"

UNIFIED_SCHEMA = "cairnwell.press_shop.unified_overhead_source_manifest.v001"
UNIFIED_STATUS = "SOURCE_ONLY_HASH_LOCKED__NOT_UNREAL_IMPORTED__NOT_RUNTIME_READY"
ANCHOR_SCHEMA = "cairnwell.press_shop.native_presentation_anchor_registry.v001"
ANCHOR_STATUS = "DATA_ONLY_EXACT_ANCHOR_REGISTRY__ALL_SETTERS_READY__NOT_RUNTIME_PROVEN"
IMPORT_RECEIPT_SCHEMA = "cairnwell.press_shop.unreal_candidate_import_receipt.v001"
IMPORT_RECEIPT_RESULT = "CANDIDATE_CONTENT_ASSETS_CREATED__NO_ACTORS_OR_LEVELS_TOUCHED"
BUILD_RECEIPT_SCHEMA = "cairnwell.press_shop.overhead_playable_map_build_receipt.v002"
BUILD_RECEIPT_STATUS = "PASS_CANDIDATE_MAP_INTEGRATION__NOT_RUNTIME_READY"

CANDIDATE_ASSET_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadAssets_v001"
IMPORT_RECEIPT_DIR = PROJECT / "Saved" / "Audits" / "PressShop2126" / "OverheadAssets_v001"
ACTOR_REGISTRY_NAME = "ACTOR_SPAWN_SPEC_REGISTRY_v001.json"
ANCHOR_REGISTRY_NAME = "NATIVE_PRESENTATION_ANCHOR_REGISTRY_v001.json"
IMPORT_RECEIPT_GLOB = "IMPORT_RECEIPT_*.json"
IMPORT_RECEIPT_ENV = "LB_PRESSSHOP_OVERHEAD_IMPORT_RECEIPT"
BUILD_RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "OverheadPlayable_v001" / "build_receipt_v002.json"

VISUAL_LAYER_CLASS_PATH = "/Script/LineBossCarFactory.LBPressShopOverheadVisualLayerActor"
PRESENTATION_CLASS_PATH = "/Script/LineBossCarFactory.LBPressShopOverheadPresentationActor"
CAMERA_CLASS_PATH = "/Script/Engine.CameraActor"
EXPECTED_GAME_MODE = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
BOOTSTRAP_CLASS_NAME = "LBOneFactoryBootstrap"
BUILD_AUTHORITY_CLASS_NAME = "LBPressShopBuildAuthority"
VISUAL_LAYER_TAG = "LB.PressShop.Overhead.VisualLayer.v001"
PRESENTATION_TAG = "LB.PressShop.OverheadPresentation.v001"
SUPERSEDED_PRESENTATION_TAG = "LB.OneFactory.PressStarter.Presentation.v001"
CAMERA_TAG = "LB.PressShop.Overhead.Camera.v001"
VISUAL_ONLY_TAG = "LB.Environment.VisualOnly"
NOT_WIP_TAG = "LB.NotProcessWIP"

EXPECTED_SPAWN_SPEC_COUNT = 120
EXPECTED_TEXTURE_COUNT = 112
EXPECTED_CREATED_ASSET_COUNT = 226
EXPECTED_MACHINE_BEACON_COUNT = 14
EXPECTED_TASK_LIGHT_COUNT = 4

ALLOWED_MACHINE_IDS = {
    "IN01_ARTICULATED_CARRIER", "IN02_COIL_HANDLER_AGV", "IN03_COIL_STORAGE",
    "IN04_DEPACK", "IN05_COIL_PREP", "S01_DESTACK_LOAD", "S02_DEEP_DRAW",
    "S03_FORM", "S04_TRIM", "S05_PIERCE", "S06_FLANGE", "S07_INSPECTION",
    "S07_PALLETISER", "SUPPORT_FLEET",
}
ALLOWED_LAYER_ROLES = {
    "Base", "FrameState", "Workpiece", "MovingOverlay", "ContactEffect",
    "CyanTransfer", "BeaconGlow", "TaskLightGlow", "ConveyorMotion", "RobotPose",
}
ALLOWED_METADATA_FIELDS = {
    "LayerId", "AssemblyId", "MachineId", "LayerRole", "StateId",
    "MotionChannel", "bHasMotionRange", "MotionStart", "MotionEnd",
    "SequenceFrameIndex", "SequenceFrameCount", "bSequenceLoops",
}
ALLOWED_SPAWN_SPEC_STATUSES = {
    "SOURCE_REGISTRATION_ONLY__MAP_BUILDER_MUST_REVALIDATE",
    "CANDIDATE_AUTHORED_REUSE__MAP_BUILDER_MUST_REVALIDATE",
}
EXPECTED_MACHINE_BEACONS = set(ALLOWED_MACHINE_IDS)
EXPECTED_TASK_LIGHTS = {
    "IN04_DEPACK_TASK", "S07_INSPECTION_TASK_A", "S07_INSPECTION_TASK_B",
    "S07_PALLETISER_TASK",
}
EXPECTED_S07_CANDIDATE_Z = {
    "S07_INSPECTION": 180.0,
    "S07_PALLETISER": 220.0,
    "S07_INSPECTION_TASK_A": 320.0,
    "S07_INSPECTION_TASK_B": 320.0,
    "S07_PALLETISER_TASK": 360.0,
}
S07_CANDIDATE_Z_AUTHORITY = "CODEX_CANDIDATE_INTEGRATION_Z_V001"

FULL_CAMERA_LABEL = "CAM | Press Shop 2126 | true-overhead full overview"
HERO_CAMERA_LABEL = "CAM | Press Shop 2126 | true-overhead press-train hero"
CAMERA_Z_CM = 21712.544
FULL_CAMERA_ORTHO_WIDTH_CM = 17600.0
HERO_CAMERA_ORTHO_WIDTH_CM = 10800.0
CAMERA_ASPECT = 16.0 / 9.0
CAMERA_ROTATION = (-90.0, 0.0, 0.0)  # pitch, yaw, roll
CAMERA_MIN_MARGIN_CM = 500.0
NUMERIC_TOLERANCE = 0.001

PRESS_HERO_MACHINE_IDS = {
    "S02_DEEP_DRAW", "S03_FORM", "S04_TRIM", "S05_PIERCE", "S06_FLANGE",
    "S07_INSPECTION", "S07_PALLETISER",
}

DEFAULT_ENGINE_INI = PROJECT / "Config" / "DefaultEngine.ini"
DEFAULT_ENGINE_INI_SHA256 = "b5bbc12da59d06f2ed5958ce06b70963ad991d8a8747a98c6102a771d30a0827"
PROTECTED_MAPS = {
    SOURCE_FILE: SOURCE_FILE_SHA256,
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap":
        "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap":
        "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_IndividualSprites_v007" / "Maps" / "LB_PressShop_Factorio2p5D_IndividualSprites_v007.umap":
        "0e1bc9ddbf753a790955375eba8d0b274eb7d48cb336a84a82df431f85aa9624",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_FullHall_v001" / "Maps" / "LB_PressShop_2126_FullHall_v001.umap":
        "37fc7af541675f4f38afd816d7d4552628d1deaf22b0abe01d6830907a62349f",
}
PROTECTED_NATIVE_SOURCES = {
    PROJECT / "Source" / "LineBossCarFactory" / "LBStatusBeaconComponent.h":
        "5ab9fb4245de1a9981201d555c310ceb4fdf793419171856f3503aa246c744b7",
    PROJECT / "Source" / "LineBossCarFactory" / "LBStatusBeaconComponent.cpp":
        "c80e7a096b3f91fa927db16469267cacdeea397664498c16f0bf211debc10a2d",
    PROJECT / "Source" / "LineBossCarFactory" / "LBPressShopOverheadVisualLayerActor.h":
        "e0d1ea8291ed20a5ff6b996892602286f8ffc742769125bf6dcbfb781f447a92",
    PROJECT / "Source" / "LineBossCarFactory" / "LBPressShopOverheadVisualLayerActor.cpp":
        "735860bf93df43782a103f412da9e882997f37b6c08a9461c8b5282c60f99f60",
    PROJECT / "Source" / "LineBossCarFactory" / "LBPressShopOverheadPresentationActor.h":
        "13cd628c5c44a93aa61badafd965f78e944ddb3a0b1b75f122d5321ef6090205",
    PROJECT / "Source" / "LineBossCarFactory" / "LBPressShopOverheadPresentationActor.cpp":
        "cd14c5cb6c894a739b28f8ca312d429d00e6eb0c7d0e9ef04093f0cd1e866dc0",
    PROJECT / "Source" / "LineBossCarFactory" / "LBOneFactoryWIPPresentationActor.cpp":
        "48c9c57dd53e080a761ae241ab3bd5e7a186cbcf4ac825976a5130177926f72c",
}


class BuildGuardError(RuntimeError):
    """A fail-closed v002 guard rejected the requested operation."""


def fail(message: str) -> None:
    raise BuildGuardError("PRESSSHOP_2126_OVERHEAD_PLAYABLE_V002_BUILD_FAIL: " + message)


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


def require_mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        fail(context + " must be an object")
    return value


def require_list(value: Any, context: str, *, nonempty: bool = True) -> List[Any]:
    if not isinstance(value, list) or (nonempty and not value):
        fail(context + " must be {}array".format("a non-empty " if nonempty else "an "))
    return value


def require_string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(context + " must be a non-empty string")
    return value


def finite_tuple(value: Any, size: int, context: str) -> Tuple[float, ...]:
    if not isinstance(value, list) or len(value) != size:
        fail("{} must contain {} numbers".format(context, size))
    result: List[float] = []
    for raw in value:
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            fail(context + " contains a non-number")
        number = float(raw)
        if not math.isfinite(number):
            fail(context + " contains a non-finite number")
        result.append(number)
    return tuple(result)


def _load_json_value(path: Path, context: str) -> Tuple[Any, str, bytes]:
    if not path.is_file():
        fail("{} is missing: {}".format(context, path))
    payload = path.read_bytes()
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail("{} is not valid UTF-8 JSON: {}".format(context, error))
    return value, hashlib.sha256(payload).hexdigest(), payload


def load_json(path: Path, context: str) -> Tuple[Dict[str, Any], str, bytes]:
    value, payload_hash, payload = _load_json_value(path, context)
    if not isinstance(value, dict):
        fail(context + " root must be an object")
    return value, payload_hash, payload


def load_json_array(path: Path, context: str) -> Tuple[List[Any], str, bytes]:
    value, payload_hash, payload = _load_json_value(path, context)
    if not isinstance(value, list):
        fail(context + " root must be an array")
    return value, payload_hash, payload


def validate_lock(path: Path, locked_path: Path, context: str) -> str:
    if not locked_path.is_file():
        fail("{} lock is missing: {}".format(context, locked_path))
    match = re.fullmatch(
        r"([0-9a-f]{64})\s+([^\r\n]+)\s*",
        locked_path.read_text(encoding="utf-8"),
    )
    if not match or match.group(2) != path.name:
        fail(context + " lock format or filename changed")
    actual = digest(path)
    if actual != match.group(1):
        fail("{} hash differs from its lock".format(context))
    return actual


def _normalise_asset_path(value: Any) -> str:
    text = str(value or "")
    if text.startswith("Class'") and text.endswith("'"):
        text = text[6:-1]
    if "." in text and text.startswith("/Game/"):
        text = text.split(".", 1)[0]
    return text


def _class_name(actor: Any) -> str:
    cls = actor.get_class()
    return str(cls.get_name()) if cls is not None else ""


def _vector_tuple(value: Any) -> Tuple[float, float, float]:
    return (float(value.x), float(value.y), float(value.z))


def _rotator_tuple(value: Any) -> Tuple[float, float, float]:
    return (float(value.pitch), float(value.yaw), float(value.roll))


def _close_tuple(left: Sequence[float], right: Sequence[float], tolerance: float = NUMERIC_TOLERANCE) -> bool:
    return len(left) == len(right) and all(
        abs(float(a) - float(b)) <= tolerance for a, b in zip(left, right)
    )


def actor_rotation_equivalent(actor: Any, expected_pitch_yaw_roll: Sequence[float]) -> bool:
    """Compare orientation, not one non-unique Euler representation.

    Unreal can read an orientation authored as ``(0, 180, 0)`` back as the
    mathematically identical ``(180, 0, 180)``.  Quaternion angular distance
    is invariant to that representation (and to q versus -q).
    """
    actual = actor.get_actor_rotation().quaternion()
    expected = _make_rotator(expected_pitch_yaw_roll).quaternion()
    distance_radians = float(actual.angular_distance(expected))
    return math.isfinite(distance_radians) and distance_radians <= math.radians(NUMERIC_TOLERANCE)


def canonical_transform_record(actor: Any, expected_pitch_yaw_roll: Sequence[float]) -> Dict[str, List[float]]:
    """Record a verified orientation in the registry's canonical Euler form."""
    if not actor_rotation_equivalent(actor, expected_pitch_yaw_roll):
        fail("actor orientation differs from its canonical registry rotation")
    record = actor_transform_record(actor)
    record["rotation_deg_pitch_yaw_roll"] = [float(value) for value in expected_pitch_yaw_roll]
    return record


def _spawn_aabb(spec: Mapping[str, Any]) -> Tuple[float, float, float, float]:
    transform = require_mapping(spec.get("world_transform"), "spawn world_transform")
    x, y, _ = finite_tuple(transform.get("translation_cm"), 3, "spawn translation")
    pitch, yaw, roll = finite_tuple(
        transform.get("rotation_deg_pitch_yaw_roll"), 3, "spawn rotation",
    )
    if abs(pitch) > NUMERIC_TOLERANCE or abs(roll) > NUMERIC_TOLERANCE:
        fail("sprite plane rotation must remain planar")
    sx, sy, sz = finite_tuple(
        transform.get("scale3d_for_100cm_unit_plane"), 3, "spawn scale",
    )
    if sx <= 0.0 or sy <= 0.0 or sz <= 0.0:
        fail("sprite plane scale must be positive")
    angle = math.radians(yaw)
    half_x = 50.0 * sx
    half_y = 50.0 * sy
    extent_x = abs(math.cos(angle)) * half_x + abs(math.sin(angle)) * half_y
    extent_y = abs(math.sin(angle)) * half_x + abs(math.cos(angle)) * half_y
    return x - extent_x, x + extent_x, y - extent_y, y + extent_y


def compute_registry_bounds(
    specs: Sequence[Mapping[str, Any]],
    machine_ids: set[str] | None = None,
) -> Dict[str, Any]:
    selected = [
        row for row in specs
        if machine_ids is None or row["actor_metadata"]["MachineId"] in machine_ids
    ]
    if not selected:
        fail("camera bounds selection is empty")
    min_x = min(_spawn_aabb(row)[0] for row in selected)
    max_x = max(_spawn_aabb(row)[1] for row in selected)
    min_y = min(_spawn_aabb(row)[2] for row in selected)
    max_y = max(_spawn_aabb(row)[3] for row in selected)
    return {
        "record_count": len(selected),
        "min_xy_cm": [min_x, min_y],
        "max_xy_cm": [max_x, max_y],
        "center_xy_cm": [(min_x + max_x) * 0.5, (min_y + max_y) * 0.5],
        "span_xy_cm": [max_x - min_x, max_y - min_y],
    }


def camera_margins(bounds: Mapping[str, Any], ortho_width_cm: float) -> Dict[str, float]:
    span_x, span_y = finite_tuple(bounds.get("span_xy_cm"), 2, "camera span")
    visible_height = float(ortho_width_cm) / CAMERA_ASPECT
    # At Rotator(-90,0,0), screen-right is world +Y and screen-up is world +X.
    return {
        "screen_horizontal_world_y_cm": (float(ortho_width_cm) - span_y) * 0.5,
        "screen_vertical_world_x_cm": (visible_height - span_x) * 0.5,
        "visible_width_cm": float(ortho_width_cm),
        "visible_height_cm": visible_height,
    }


def validate_spawn_specs(raw_specs: Any) -> Dict[str, Any]:
    specs = require_list(raw_specs, "actor spawn specs")
    if len(specs) != EXPECTED_SPAWN_SPEC_COUNT:
        fail("actor spawn spec count changed")
    seen_ids: set[str] = set()
    texture_ids: set[str] = set()
    sequence_groups: Dict[Tuple[str, str, str, str], List[Mapping[str, Any]]] = {}
    role_counts: Dict[str, int] = {}
    for index, raw in enumerate(specs):
        row = require_mapping(raw, "spawn spec {}".format(index))
        spec_id = require_string(row.get("spawn_spec_id"), "spawn_spec_id")
        if spec_id in seen_ids:
            fail("duplicate spawn_spec_id: " + spec_id)
        seen_ids.add(spec_id)
        if row.get("status") not in ALLOWED_SPAWN_SPEC_STATUSES:
            fail(spec_id + " status changed")
        if row.get("actor_class") != VISUAL_LAYER_CLASS_PATH:
            fail(spec_id + " native actor class changed")
        if row.get("collision_enabled") is not False or row.get("runtime_ready") is not False:
            fail(spec_id + " must remain collision-free and source-only")
        if row.get("plane_asset") != CANDIDATE_ASSET_ROOT + "/Geometry/SM_CA_MW_PS_OverheadUnitPlane_v001":
            fail(spec_id + " unit plane path changed")
        material = require_string(row.get("expected_material_instance"), spec_id + " material")
        if not material.startswith(CANDIDATE_ASSET_ROOT + "/Materials/"):
            fail(spec_id + " material escapes candidate root")
        texture_ids.add(require_string(row.get("texture_asset_id"), spec_id + " texture id"))
        metadata = require_mapping(row.get("actor_metadata"), spec_id + " actor_metadata")
        if set(metadata) != ALLOWED_METADATA_FIELDS:
            fail(spec_id + " metadata field set changed")
        role = require_string(metadata.get("LayerRole"), spec_id + " LayerRole")
        machine_id = require_string(metadata.get("MachineId"), spec_id + " MachineId")
        if role not in ALLOWED_LAYER_ROLES or machine_id not in ALLOWED_MACHINE_IDS:
            fail(spec_id + " role or machine ID is outside the native contract")
        require_string(metadata.get("LayerId"), spec_id + " LayerId")
        require_string(metadata.get("AssemblyId"), spec_id + " AssemblyId")
        role_counts[role] = role_counts.get(role, 0) + 1
        has_motion = metadata.get("bHasMotionRange")
        if not isinstance(has_motion, bool):
            fail(spec_id + " bHasMotionRange is not bool")
        if not has_motion and (metadata.get("MotionStart") is not None or metadata.get("MotionEnd") is not None):
            fail(spec_id + " false motion range must retain null endpoints")
        if has_motion:
            for endpoint in ("MotionStart", "MotionEnd"):
                motion = require_mapping(metadata.get(endpoint), spec_id + " " + endpoint)
                finite_tuple(motion.get("translation_cm"), 3, endpoint + " translation")
                finite_tuple(motion.get("rotation_deg_pitch_yaw_roll"), 3, endpoint + " rotation")
                scale = finite_tuple(motion.get("scale3d"), 3, endpoint + " scale")
                if min(scale) <= 0.0:
                    fail(spec_id + " motion endpoint scale must be positive")
        frame_index = metadata.get("SequenceFrameIndex")
        frame_count = metadata.get("SequenceFrameCount")
        loops = metadata.get("bSequenceLoops")
        if isinstance(frame_index, bool) or not isinstance(frame_index, int):
            fail(spec_id + " sequence index must be int")
        if isinstance(frame_count, bool) or not isinstance(frame_count, int):
            fail(spec_id + " sequence count must be int")
        if not isinstance(loops, bool):
            fail(spec_id + " sequence loops must be bool")
        if frame_count == 0:
            if frame_index != -1 or loops:
                fail(spec_id + " non-sequence metadata is not canonical")
        else:
            if not 0 <= frame_index < frame_count:
                fail(spec_id + " sequence index is invalid")
            channel = require_string(metadata.get("MotionChannel"), spec_id + " sequence channel")
            key = (machine_id, role, str(metadata.get("StateId") or ""), channel)
            sequence_groups.setdefault(key, []).append(row)
        _spawn_aabb(row)
        z_offset = row.get("integration_z_offset_cm")
        if isinstance(z_offset, bool) or not isinstance(z_offset, (int, float)) or not math.isfinite(float(z_offset)):
            fail(spec_id + " integration Z offset is invalid")
    for key, rows in sequence_groups.items():
        count_values = {row["actor_metadata"]["SequenceFrameCount"] for row in rows}
        loop_values = {row["actor_metadata"]["bSequenceLoops"] for row in rows}
        if len(count_values) != 1 or len(loop_values) != 1:
            fail("sequence group metadata differs: {}".format(key))
        count = next(iter(count_values))
        indices = sorted(row["actor_metadata"]["SequenceFrameIndex"] for row in rows)
        if indices != list(range(count)):
            fail("sequence group is incomplete: {}".format(key))
    if len(texture_ids) != EXPECTED_TEXTURE_COUNT:
        fail("unique spawn-referenced texture count changed")
    full_bounds = compute_registry_bounds(specs)
    hero_bounds = compute_registry_bounds(specs, PRESS_HERO_MACHINE_IDS)
    full_margins = camera_margins(full_bounds, FULL_CAMERA_ORTHO_WIDTH_CM)
    hero_margins = camera_margins(hero_bounds, HERO_CAMERA_ORTHO_WIDTH_CM)
    if min(full_margins["screen_horizontal_world_y_cm"], full_margins["screen_vertical_world_x_cm"]) < CAMERA_MIN_MARGIN_CM:
        fail("full overview camera no longer frames the registry")
    if min(hero_margins["screen_horizontal_world_y_cm"], hero_margins["screen_vertical_world_x_cm"]) < CAMERA_MIN_MARGIN_CM:
        fail("press-train hero camera no longer frames the selected registry")
    return {
        "specs": specs,
        "spawn_spec_ids": sorted(seen_ids),
        "texture_asset_ids": sorted(texture_ids),
        "role_counts": dict(sorted(role_counts.items())),
        "sequence_group_count": len(sequence_groups),
        "full_bounds": full_bounds,
        "hero_bounds": hero_bounds,
        "full_camera_margins": full_margins,
        "hero_camera_margins": hero_margins,
    }


def validate_anchor_registry(raw: Mapping[str, Any]) -> Dict[str, Any]:
    registry = require_mapping(raw, "native presentation anchor registry")
    if registry.get("schema") != ANCHOR_SCHEMA or registry.get("status") != ANCHOR_STATUS:
        fail("native anchor registry schema/status changed")
    if registry.get("runtime_ready") is not False or registry.get("map_integrated") is not False:
        fail("native anchor registry must remain pre-integration evidence")
    if registry.get("machine_beacon_setter") != "SetMachineBeaconAnchor" or registry.get("task_light_setter") != "SetTaskLightAnchor":
        fail("native adapter setter contract changed")
    if registry.get("unresolved_setter_rows") != []:
        fail("native anchor registry still has unresolved setter rows")
    beacon_rows = require_list(registry.get("machine_beacons"), "machine beacon anchors")
    task_rows = require_list(registry.get("task_lights"), "task-light anchors")
    if len(beacon_rows) != EXPECTED_MACHINE_BEACON_COUNT or registry.get("setter_ready_machine_beacon_count") != EXPECTED_MACHINE_BEACON_COUNT:
        fail("native machine beacon cardinality changed")
    if len(task_rows) != EXPECTED_TASK_LIGHT_COUNT or registry.get("setter_ready_task_light_count") != EXPECTED_TASK_LIGHT_COUNT:
        fail("native task-light cardinality changed")
    beacons: Dict[str, Mapping[str, Any]] = {}
    tasks: Dict[str, Mapping[str, Any]] = {}
    for kind, rows, id_field, target in (
        ("beacon", beacon_rows, "machine_id", beacons),
        ("task light", task_rows, "task_light_id", tasks),
    ):
        for row in rows:
            item = require_mapping(row, kind + " anchor")
            item_id = require_string(item.get(id_field), kind + " ID")
            if item_id in target:
                fail("duplicate {} anchor: {}".format(kind, item_id))
            if item.get("setter_ready") is not True:
                fail("{} {} is not setter-ready".format(kind, item_id))
            world = finite_tuple(item.get("world_anchor_cm"), 3, kind + " world anchor")
            xy = item.get("world_anchor_xy_cm")
            if xy is not None and not _close_tuple(finite_tuple(xy, 2, kind + " world XY"), world[:2]):
                fail("{} {} exact XY differs from world anchor".format(kind, item_id))
            target[item_id] = item
    if set(beacons) != EXPECTED_MACHINE_BEACONS or set(tasks) != EXPECTED_TASK_LIGHTS:
        fail("native anchor IDs do not match the presentation adapter")
    decision = require_mapping(registry.get("candidate_integration_z_decision"), "candidate S07 Z decision")
    if decision.get("authority") != S07_CANDIDATE_Z_AUTHORITY or decision.get("source_authored") is not False:
        fail("S07 candidate integration Z authority changed")
    for item_id, expected_z in EXPECTED_S07_CANDIDATE_Z.items():
        item = tasks[item_id] if item_id in tasks else beacons[item_id]
        if item.get("authority", "").find(S07_CANDIDATE_Z_AUTHORITY) < 0:
            fail(item_id + " lost candidate-Z provenance")
        if not _close_tuple([item["world_anchor_cm"][2]], [expected_z]):
            fail(item_id + " candidate Z changed")
        if item.get("candidate_z_source_authored") is not False:
            fail(item_id + " candidate Z was mislabeled as source-authored")
    return {"registry": registry, "beacons": beacons, "task_lights": tasks}


def expected_created_assets(manifest: Mapping[str, Any], texture_ids: Sequence[str]) -> List[str]:
    contract = require_mapping(manifest.get("candidate_asset_contract"), "candidate asset contract")
    result = [
        require_string(require_mapping(contract.get("master_material"), "master material").get("path"), "master material path"),
        require_string(require_mapping(contract.get("unit_plane"), "unit plane").get("path"), "unit plane path"),
    ]
    by_id = {
        require_string(row.get("asset_id"), "texture asset id"): row
        for row in require_list(manifest.get("texture_assets"), "texture asset catalogue")
    }
    for asset_id in texture_ids:
        if asset_id not in by_id:
            fail("spawn-referenced texture is missing from catalogue: " + asset_id)
        expected = require_mapping(by_id[asset_id].get("expected_unreal_assets"), asset_id + " Unreal targets")
        result.extend([
            require_string(expected.get("texture"), asset_id + " texture target"),
            require_string(expected.get("material_instance"), asset_id + " material target"),
        ])
    if len(result) != EXPECTED_CREATED_ASSET_COUNT or len(set(result)) != len(result):
        fail("expected candidate content target set changed")
    return sorted(result)


def validate_unified_manifest(manifest: Mapping[str, Any]) -> Dict[str, Any]:
    if manifest.get("schema") != UNIFIED_SCHEMA or manifest.get("status") != UNIFIED_STATUS:
        fail("unified source manifest schema/status changed")
    if any(manifest.get(key) is not False for key in ("runtime_ready", "unreal_imported", "map_integrated")):
        fail("unified source manifest must remain source-only")
    path_contract = require_mapping(manifest.get("path_contract"), "path contract")
    if path_contract.get("candidate_content_root") != CANDIDATE_ASSET_ROOT:
        fail("candidate content root changed")
    if path_contract.get("maps_may_be_modified") is not False or path_contract.get("config_may_be_modified") is not False:
        fail("source/import lane mutation policy changed")
    spawn_info = validate_spawn_specs(manifest.get("actor_spawn_specs"))
    anchor_info = validate_anchor_registry(
        require_mapping(manifest.get("native_presentation_anchor_registry"), "embedded anchor registry")
    )
    animation = require_mapping(manifest.get("animation_effects_contract"), "animation/effects contract")
    animation_path = CODEX_OUTPUTS / require_string(animation.get("path"), "animation contract path")
    animation_hash = require_string(animation.get("sha256"), "animation contract hash")
    if not animation_path.is_file() or digest(animation_path) != animation_hash:
        fail("animation/effects contract is missing or changed")
    created_assets = expected_created_assets(manifest, spawn_info["texture_asset_ids"])
    return {
        "manifest": manifest,
        "spawn": spawn_info,
        "anchors": anchor_info,
        "animation_contract_path": animation_path,
        "animation_contract_sha256": animation_hash,
        "expected_created_assets": created_assets,
    }


def discover_import_receipt(receipt_dir: Path = IMPORT_RECEIPT_DIR) -> Path:
    override = os.environ.get(IMPORT_RECEIPT_ENV, "").strip()
    if override:
        path = Path(override).resolve()
        try:
            path.relative_to(receipt_dir.resolve())
        except ValueError:
            fail("explicit import receipt escapes the approved receipt directory")
        if not re.fullmatch(r"IMPORT_RECEIPT_[0-9]{8}T[0-9]{6}_[0-9]{6}Z\.json", path.name):
            fail("explicit import receipt filename is invalid")
        if not path.is_file():
            fail("explicit import receipt is missing")
        return path
    receipts = sorted(receipt_dir.glob(IMPORT_RECEIPT_GLOB)) if receipt_dir.is_dir() else []
    if len(receipts) != 1:
        fail("expected exactly one guarded import receipt (found {})".format(len(receipts)))
    return receipts[0]


def validate_import_receipt(
    receipt: Mapping[str, Any],
    manifest_sha256: str,
    actor_registry_sha256: str,
    anchor_registry_sha256: str,
    expected_assets: Sequence[str],
) -> None:
    if receipt.get("schema") != IMPORT_RECEIPT_SCHEMA or receipt.get("result") != IMPORT_RECEIPT_RESULT:
        fail("candidate import receipt schema/result changed")
    if receipt.get("manifest_sha256") != manifest_sha256 or receipt.get("candidate_content_root") != CANDIDATE_ASSET_ROOT:
        fail("candidate import receipt does not identify this source manifest/root")
    if receipt.get("actor_spawn_registry_file") != ACTOR_REGISTRY_NAME or receipt.get("actor_spawn_registry_sha256") != actor_registry_sha256:
        fail("candidate import receipt actor registry cross-link changed")
    if receipt.get("actor_spawn_spec_count") != EXPECTED_SPAWN_SPEC_COUNT:
        fail("candidate import receipt actor count changed")
    if receipt.get("native_presentation_anchor_registry_file") != ANCHOR_REGISTRY_NAME or receipt.get("native_presentation_anchor_registry_sha256") != anchor_registry_sha256:
        fail("candidate import receipt anchor registry cross-link changed")
    if receipt.get("native_machine_beacon_count") != EXPECTED_MACHINE_BEACON_COUNT or receipt.get("native_task_light_count") != EXPECTED_TASK_LIGHT_COUNT:
        fail("candidate import receipt native-anchor counts changed")
    for key in ("actor_spawn_performed", "map_integration_performed", "runtime_ready", "native_presentation_anchor_setters_configured"):
        if receipt.get(key) is not False:
            fail("candidate import receipt must keep {} false".format(key))
    created = require_list(receipt.get("created_assets"), "candidate import created assets")
    if receipt.get("created_asset_count") != EXPECTED_CREATED_ASSET_COUNT or sorted(created) != sorted(expected_assets):
        fail("candidate import receipt created-asset set changed")


def _run_strict_verifier() -> Mapping[str, Any]:
    if not UNIFIED_STRICT_VERIFIER.is_file():
        fail("strict unified verifier is missing")
    spec = importlib.util.spec_from_file_location("pressshop_unified_strict_v001_for_map_v002", UNIFIED_STRICT_VERIFIER)
    if spec is None or spec.loader is None:
        fail("could not load strict unified verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.verify()
    if not isinstance(result, Mapping) or result.get("runtime_ready") is not False or result.get("unreal_executed") is not False:
        fail("strict unified verifier returned an unexpected result")
    return result


def protected_snapshot() -> Dict[str, str]:
    expected = dict(PROTECTED_MAPS)
    expected[DEFAULT_ENGINE_INI] = DEFAULT_ENGINE_INI_SHA256
    expected.update(PROTECTED_NATIVE_SOURCES)
    result: Dict[str, str] = {}
    for path, required_hash in expected.items():
        if not path.is_file():
            fail("protected file is missing: {}".format(path))
        actual = digest(path)
        if actual != required_hash:
            fail("protected file hash changed: {}".format(path))
        result[path.as_posix()] = actual
    return dict(sorted(result.items()))


def load_and_validate_inputs() -> Dict[str, Any]:
    manifest_hash = validate_lock(UNIFIED_MANIFEST, UNIFIED_MANIFEST_LOCK, "unified manifest")
    anchor_source_hash = validate_lock(SOURCE_ANCHOR_REGISTRY, SOURCE_ANCHOR_LOCK, "source anchor registry")
    manifest, actual_manifest_hash, _ = load_json(UNIFIED_MANIFEST, "unified manifest")
    if actual_manifest_hash != manifest_hash:
        fail("unified manifest changed after lock validation")
    source_info = validate_unified_manifest(manifest)
    strict_result = _run_strict_verifier()
    if strict_result.get("manifest_sha256") != manifest_hash:
        fail("strict verifier manifest hash differs")
    source_anchor, actual_anchor_hash, source_anchor_payload = load_json(SOURCE_ANCHOR_REGISTRY, "source anchor registry")
    if actual_anchor_hash != anchor_source_hash or source_anchor != source_info["anchors"]["registry"]:
        fail("source anchor companion differs from embedded registry")
    if source_anchor_payload != canonical_json_bytes(source_anchor):
        fail("source anchor companion is not canonical")

    receipt_path = discover_import_receipt()
    receipt, receipt_hash, _ = load_json(receipt_path, "candidate import receipt")
    actor_registry_path = IMPORT_RECEIPT_DIR / ACTOR_REGISTRY_NAME
    anchor_registry_path = IMPORT_RECEIPT_DIR / ANCHOR_REGISTRY_NAME
    actor_registry, actor_registry_hash, actor_payload = load_json_array(
        actor_registry_path, "import actor registry"
    )
    anchor_registry, anchor_registry_hash, anchor_payload = load_json(anchor_registry_path, "import anchor registry")
    if actor_registry != source_info["spawn"]["specs"] or actor_payload != canonical_json_bytes(actor_registry):
        fail("import actor registry differs from canonical unified spawn specs")
    if anchor_registry != source_anchor or anchor_payload != source_anchor_payload:
        fail("import anchor registry differs from canonical source anchor companion")
    validate_import_receipt(
        receipt, manifest_hash, actor_registry_hash, anchor_registry_hash,
        source_info["expected_created_assets"],
    )
    return {
        "manifest_sha256": manifest_hash,
        "source": source_info,
        "strict_verifier": dict(strict_result),
        "import_receipt_path": receipt_path,
        "import_receipt_sha256": receipt_hash,
        "import_receipt": receipt,
        "actor_registry_path": actor_registry_path,
        "actor_registry_sha256": actor_registry_hash,
        "anchor_registry_path": anchor_registry_path,
        "anchor_registry_sha256": anchor_registry_hash,
    }


def _unreal_name(value: Any) -> Any:
    return unreal.Name("None" if value is None else str(value))


def _make_vector(values: Sequence[float]) -> Any:
    return unreal.Vector(x=float(values[0]), y=float(values[1]), z=float(values[2]))


def _make_rotator(values: Sequence[float]) -> Any:
    return unreal.Rotator(pitch=float(values[0]), yaw=float(values[1]), roll=float(values[2]))


def _role_enum(role: str) -> Any:
    enum_type = getattr(unreal, "LBPressShopOverheadLayerRole", None)
    if enum_type is None:
        fail("native layer role enum is not reflected to Python")
    enum_name = re.sub(r"(?<!^)(?=[A-Z])", "_", role).upper()
    value = getattr(enum_type, enum_name, None)
    if value is None:
        fail("native layer role enum entry is missing: " + enum_name)
    return value


PROPERTY_CANDIDATES = {
    "LayerId": ("layer_id",),
    "AssemblyId": ("assembly_id",),
    "MachineId": ("machine_id",),
    "LayerRole": ("layer_role",),
    "StateId": ("state_id",),
    "MotionChannel": ("motion_channel",),
    "bHasMotionRange": ("has_motion_range", "b_has_motion_range"),
    "MotionStart": ("motion_start",),
    "MotionEnd": ("motion_end",),
    "SequenceFrameIndex": ("sequence_frame_index",),
    "SequenceFrameCount": ("sequence_frame_count",),
    "bSequenceLoops": ("sequence_loops", "b_sequence_loops"),
}


def reflected_property_name(obj: Any, source_name: str) -> str:
    for candidate in PROPERTY_CANDIDATES[source_name]:
        try:
            obj.get_editor_property(candidate)
            return candidate
        except Exception:
            continue
    fail("native reflected property is missing: " + source_name)


def _metadata_value(source_name: str, value: Any) -> Any:
    if source_name in {"LayerId", "AssemblyId", "MachineId", "StateId", "MotionChannel"}:
        return _unreal_name(value)
    if source_name == "LayerRole":
        return _role_enum(str(value))
    return value


def _set_and_verify_metadata(actor: Any, metadata: Mapping[str, Any]) -> Dict[str, Any]:
    readback: Dict[str, Any] = {}
    for source_name in (
        "LayerId", "AssemblyId", "MachineId", "LayerRole", "StateId",
        "MotionChannel", "bHasMotionRange", "SequenceFrameIndex",
        "SequenceFrameCount", "bSequenceLoops",
    ):
        property_name = reflected_property_name(actor, source_name)
        value = _metadata_value(source_name, metadata[source_name])
        actor.set_editor_property(property_name, value)
        actual = actor.get_editor_property(property_name)
        if source_name in {"bHasMotionRange", "bSequenceLoops", "SequenceFrameIndex", "SequenceFrameCount"}:
            if actual != value:
                fail("metadata readback differs for " + source_name)
        elif source_name == "LayerRole":
            if actual != value:
                fail("role enum readback differs")
        else:
            expected_text = "None" if metadata[source_name] is None else str(metadata[source_name])
            if str(actual) != expected_text:
                fail("FName metadata readback differs for " + source_name)
        readback[source_name] = str(actual) if source_name not in {"bHasMotionRange", "bSequenceLoops", "SequenceFrameIndex", "SequenceFrameCount"} else actual
    if metadata["bHasMotionRange"]:
        fail("v002 registry unexpectedly requires runtime transform construction")
    return readback


def editor_preview_visible(metadata: Mapping[str, Any]) -> bool:
    role = metadata["LayerRole"]
    frame_count = metadata["SequenceFrameCount"]
    if frame_count > 0:
        return metadata["SequenceFrameIndex"] == 0
    if role == "FrameState":
        return metadata["StateId"] == "OPEN"
    if role == "RobotPose":
        return metadata["StateId"] == "PARKED"
    return role in {"Base", "Workpiece", "MovingOverlay"}


def actor_transform_record(actor: Any) -> Dict[str, List[float]]:
    return {
        "location_cm": list(_vector_tuple(actor.get_actor_location())),
        "rotation_deg_pitch_yaw_roll": list(_rotator_tuple(actor.get_actor_rotation())),
        "scale3d": list(_vector_tuple(actor.get_actor_scale3d())),
    }


def actor_fingerprint(actor: Any) -> Dict[str, Any]:
    tags = sorted(str(value) for value in list(actor.get_editor_property("tags") or []))
    hidden = bool(actor.is_hidden()) if hasattr(actor, "is_hidden") else False
    collision = bool(actor.get_actor_enable_collision()) if hasattr(actor, "get_actor_enable_collision") else None
    return {
        "path": str(actor.get_path_name()),
        "name": str(actor.get_name()),
        "label": str(actor.get_actor_label()),
        "class_path": str(actor.get_class().get_path_name()),
        "transform": actor_transform_record(actor),
        "tags": tags,
        "hidden": hidden,
        "collision_enabled": collision,
    }


def world_package_name(world: Any) -> str:
    path = str(world.get_path_name())
    return path.split(".", 1)[0]


def world_game_mode_path(world: Any) -> str | None:
    settings = world.get_world_settings()
    game_mode = settings.get_editor_property("default_game_mode")
    return str(game_mode.get_path_name()) if game_mode is not None else None


def dirty_package_paths() -> Dict[str, List[str]]:
    def normalise(values: Iterable[Any]) -> List[str]:
        result = []
        for value in values or []:
            if hasattr(value, "get_name"):
                result.append(str(value.get_name()))
            else:
                result.append(str(value))
        return sorted(result)
    return {
        "maps": normalise(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
        "content": normalise(unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
    }


def _editor_world() -> Any:
    subsystem_class = getattr(unreal, "UnrealEditorSubsystem", None)
    if subsystem_class is None:
        fail("UnrealEditorSubsystem is unavailable")
    subsystem = unreal.get_editor_subsystem(subsystem_class)
    world = subsystem.get_editor_world() if subsystem is not None else None
    if world is None:
        fail("could not resolve the current editor world")
    return world


def _actor_subsystem() -> Any:
    subsystem_class = getattr(unreal, "EditorActorSubsystem", None)
    if subsystem_class is None:
        fail("EditorActorSubsystem is unavailable")
    subsystem = unreal.get_editor_subsystem(subsystem_class)
    if subsystem is None:
        fail("could not resolve EditorActorSubsystem")
    return subsystem


def _level_editor_subsystem() -> Any:
    subsystem_class = getattr(unreal, "LevelEditorSubsystem", None)
    if subsystem_class is None:
        fail("LevelEditorSubsystem is unavailable")
    subsystem = unreal.get_editor_subsystem(subsystem_class)
    if subsystem is None:
        fail("could not resolve LevelEditorSubsystem")
    return subsystem


def _load_class(path: str) -> Any:
    cls = unreal.load_class(None, path)
    if cls is None:
        fail("native class is unavailable (compile/relaunch required): " + path)
    return cls


def _asset_class_name(asset: Any) -> str:
    return str(asset.get_class().get_name()) if asset is not None else ""


def preflight_candidate_assets(inputs: Mapping[str, Any]) -> Dict[str, Any]:
    loaded: Dict[str, Any] = {}
    for path in inputs["source"]["expected_created_assets"]:
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            fail("candidate asset is missing: " + path)
        asset = unreal.load_asset(path)
        if asset is None:
            fail("candidate asset failed to load: " + path)
        loaded[path] = asset
    contract = inputs["source"]["manifest"]["candidate_asset_contract"]
    plane_path = contract["unit_plane"]["path"]
    master_path = contract["master_material"]["path"]
    if _asset_class_name(loaded[plane_path]) != "StaticMesh":
        fail("candidate unit plane is not a StaticMesh")
    if _asset_class_name(loaded[master_path]) != "Material":
        fail("candidate master material class changed")
    for path, asset in loaded.items():
        if "/Textures/" in path and _asset_class_name(asset) != "Texture2D":
            fail("candidate texture class changed: " + path)
    texture_target_by_id = {
        row["asset_id"]: row["expected_unreal_assets"]["texture"]
        for row in inputs["source"]["manifest"]["texture_assets"]
        if row["asset_id"] in inputs["source"]["spawn"]["texture_asset_ids"]
    }
    checked_materials: set[str] = set()
    for spec in inputs["source"]["spawn"]["specs"]:
        material_path = spec["expected_material_instance"]
        if "MaterialInstance" not in _asset_class_name(loaded[material_path]):
            fail("candidate material instance class changed")
        if material_path in checked_materials:
            continue
        checked_materials.add(material_path)
        instance = loaded[material_path]
        if str(instance.get_base_material().get_path_name()) != str(loaded[master_path].get_path_name()):
            fail("candidate material instance has the wrong master: " + material_path)
        texture = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
            instance, "SpriteTexture",
        )
        expected_texture_path = texture_target_by_id[spec["texture_asset_id"]]
        if texture is None or str(texture.get_path_name()) != str(loaded[expected_texture_path].get_path_name()):
            fail("candidate material instance has the wrong SpriteTexture: " + material_path)
    return loaded


def _spawn_actor(actor_subsystem: Any, cls: Any, location: Sequence[float], rotation: Sequence[float], label: str) -> Any:
    actor = actor_subsystem.spawn_actor_from_class(
        cls, _make_vector(location), _make_rotator(rotation), transient=False,
    )
    if actor is None:
        fail("failed to spawn actor: " + label)
    actor.set_actor_label(label)
    return actor


def spawn_visual_layers(
    actor_subsystem: Any,
    visual_class: Any,
    specs: Sequence[Mapping[str, Any]],
    loaded_assets: Mapping[str, Any],
) -> Tuple[List[Any], List[Dict[str, Any]]]:
    actors: List[Any] = []
    records: List[Dict[str, Any]] = []
    for spec in specs:
        transform = spec["world_transform"]
        label = "VIS | " + spec["spawn_spec_id"]
        actor = _spawn_actor(
            actor_subsystem, visual_class, transform["translation_cm"],
            transform["rotation_deg_pitch_yaw_roll"], label,
        )
        actor.set_actor_scale3d(_make_vector(transform["scale3d_for_100cm_unit_plane"]))
        actor.set_actor_enable_collision(False)
        mesh_component = actor.get_editor_property("static_mesh_component")
        if mesh_component is None:
            fail(label + " has no static mesh component")
        if not mesh_component.set_static_mesh(loaded_assets[spec["plane_asset"]]):
            # Some UE bindings return None on success; only explicit False fails.
            assigned_mesh = mesh_component.get_editor_property("static_mesh")
            if assigned_mesh is None or str(assigned_mesh.get_path_name()) != str(loaded_assets[spec["plane_asset"]].get_path_name()):
                fail(label + " rejected the unit plane")
        mesh_component.set_material(0, loaded_assets[spec["expected_material_instance"]])
        metadata_readback = _set_and_verify_metadata(actor, spec["actor_metadata"])
        visible = editor_preview_visible(spec["actor_metadata"])
        actor.apply_presentation_state(visible, 0.0)
        if not actor_rotation_equivalent(actor, transform["rotation_deg_pitch_yaw_roll"]):
            fail(label + " orientation readback differs")
        actual_transform = canonical_transform_record(
            actor, transform["rotation_deg_pitch_yaw_roll"],
        )
        if not _close_tuple(actual_transform["location_cm"], transform["translation_cm"]):
            fail(label + " location readback differs")
        if not _close_tuple(actual_transform["scale3d"], transform["scale3d_for_100cm_unit_plane"]):
            fail(label + " scale readback differs")
        tags = {str(value) for value in list(actor.get_editor_property("tags") or [])}
        if not {VISUAL_LAYER_TAG, VISUAL_ONLY_TAG, NOT_WIP_TAG}.issubset(tags):
            fail(label + " native constructor tags are missing")
        if actor.get_actor_enable_collision():
            fail(label + " collision was enabled")
        assigned_material = mesh_component.get_material(0)
        if assigned_material is None or str(assigned_material.get_path_name()) != str(loaded_assets[spec["expected_material_instance"]].get_path_name()):
            fail(label + " material readback differs")
        actors.append(actor)
        records.append({
            "spawn_spec_id": spec["spawn_spec_id"],
            "actor_path": str(actor.get_path_name()),
            "actor_label": label,
            "class_path": str(actor.get_class().get_path_name()),
            "transform": actual_transform,
            "plane_asset": spec["plane_asset"],
            "material_instance": spec["expected_material_instance"],
            "metadata_readback": metadata_readback,
            "editor_preview_visible": visible,
            "collision_enabled": False,
        })
    return actors, records


def spawn_presentation_adapter(
    actor_subsystem: Any,
    presentation_class: Any,
    anchor_info: Mapping[str, Any],
) -> Tuple[Any, Dict[str, Any]]:
    label = "VIS | Press Shop 2126 | Overhead runtime presentation"
    actor = _spawn_actor(actor_subsystem, presentation_class, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), label)
    actor.set_actor_enable_collision(False)
    tags = {str(value) for value in list(actor.get_editor_property("tags") or [])}
    if not {PRESENTATION_TAG, VISUAL_ONLY_TAG, NOT_WIP_TAG}.issubset(tags):
        fail("native presentation adapter tags are missing")
    if int(actor.get_status_beacon_count()) != EXPECTED_MACHINE_BEACON_COUNT:
        fail("native presentation adapter beacon count changed")
    if int(actor.get_task_light_count()) != EXPECTED_TASK_LIGHT_COUNT:
        fail("native presentation adapter task-light count changed")
    owns = getattr(actor, "owns_production_state", None)
    if owns is None:
        reflected_type = getattr(unreal, "LBPressShopOverheadPresentationActor", None)
        owns = getattr(reflected_type, "owns_production_state", None) if reflected_type is not None else None
    if owns is None or bool(owns()):
        fail("presentation adapter ownership contract is missing or unsafe")

    beacon_records = []
    for machine_id, row in sorted(anchor_info["beacons"].items()):
        expected = finite_tuple(row["world_anchor_cm"], 3, machine_id + " anchor")
        if not actor.set_machine_beacon_anchor(_unreal_name(machine_id), _make_vector(expected)):
            fail("native beacon setter rejected " + machine_id)
        component = actor.get_status_beacon(_unreal_name(machine_id))
        if component is None:
            fail("native beacon getter failed for " + machine_id)
        actual = _vector_tuple(component.get_world_location())
        if not _close_tuple(actual, expected):
            fail("native beacon anchor readback differs for " + machine_id)
        beacon_records.append({"machine_id": machine_id, "expected_world_cm": list(expected), "actual_world_cm": list(actual)})

    task_records = []
    for task_id, row in sorted(anchor_info["task_lights"].items()):
        expected = finite_tuple(row["world_anchor_cm"], 3, task_id + " anchor")
        if not actor.set_task_light_anchor(_unreal_name(task_id), _make_vector(expected)):
            fail("native task-light setter rejected " + task_id)
        component = actor.get_task_light(_unreal_name(task_id))
        if component is None:
            fail("native task-light getter failed for " + task_id)
        actual = _vector_tuple(component.get_world_location())
        if not _close_tuple(actual, expected):
            fail("native task-light anchor readback differs for " + task_id)
        task_records.append({"task_light_id": task_id, "expected_world_cm": list(expected), "actual_world_cm": list(actual)})
    return actor, {
        "actor_path": str(actor.get_path_name()),
        "actor_label": label,
        "class_path": str(actor.get_class().get_path_name()),
        "owns_production_state": False,
        "status_beacon_count": EXPECTED_MACHINE_BEACON_COUNT,
        "task_light_count": EXPECTED_TASK_LIGHT_COUNT,
        "machine_beacon_anchor_readbacks": beacon_records,
        "task_light_anchor_readbacks": task_records,
    }


def spawn_camera(
    actor_subsystem: Any,
    camera_class: Any,
    label: str,
    bounds: Mapping[str, Any],
    ortho_width_cm: float,
) -> Tuple[Any, Dict[str, Any]]:
    center = finite_tuple(bounds["center_xy_cm"], 2, label + " center")
    actor = _spawn_actor(
        actor_subsystem, camera_class, (center[0], center[1], CAMERA_Z_CM),
        CAMERA_ROTATION, label,
    )
    actor.set_editor_property("tags", [
        _unreal_name(CAMERA_TAG), _unreal_name(VISUAL_ONLY_TAG), _unreal_name(NOT_WIP_TAG),
    ])
    component = actor.get_editor_property("camera_component")
    if component is None:
        fail(label + " has no camera component")
    component.set_editor_property("projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC)
    component.set_editor_property("ortho_width", float(ortho_width_cm))
    component.set_editor_property("constrain_aspect_ratio", True)
    component.set_editor_property("aspect_ratio", CAMERA_ASPECT)
    if not actor_rotation_equivalent(actor, CAMERA_ROTATION):
        fail(label + " is not exactly true-overhead")
    transform = canonical_transform_record(actor, CAMERA_ROTATION)
    margins = camera_margins(bounds, ortho_width_cm)
    if min(margins["screen_horizontal_world_y_cm"], margins["screen_vertical_world_x_cm"]) < CAMERA_MIN_MARGIN_CM:
        fail(label + " framing margin is too small")
    return actor, {
        "actor_path": str(actor.get_path_name()),
        "actor_label": label,
        "transform": transform,
        "projection": "ORTHOGRAPHIC",
        "ortho_width_cm": float(ortho_width_cm),
        "aspect_ratio": CAMERA_ASPECT,
        "camera_axis_contract": {"screen_right": "+Y", "screen_up": "+X", "view": "-Z"},
        "registry_bounds": dict(bounds),
        "margins": margins,
    }


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(canonical_json_bytes(value))
    except FileExistsError as error:
        raise BuildGuardError("refusing to overwrite build receipt: {}".format(path)) from error


def main() -> None:
    # Disk/data verification must precede every Unreal mutation.
    inputs = load_and_validate_inputs()
    protected_before = protected_snapshot()
    target_file_exists = TARGET_FILE.exists()
    target_asset_exists = bool(unreal.EditorAssetLibrary.does_asset_exist(TARGET_MAP))
    if target_file_exists != target_asset_exists:
        fail("target map disk/asset-registry existence differs")
    recovery_resume = target_file_exists and target_asset_exists
    recovery_evidence: Dict[str, Any] = {"used": False}
    if recovery_resume:
        if TARGET_FILE.stat().st_size != RECOVERY_BASELINE_TARGET_BYTES:
            fail("existing recovery target byte count differs from the pinned pure-template baseline")
        if digest(TARGET_FILE) != RECOVERY_BASELINE_TARGET_SHA256:
            fail("existing recovery target hash differs from the pinned pure-template baseline")
        if not RECOVERY_PRIOR_RUN_LOG.is_file() or digest(RECOVERY_PRIOR_RUN_LOG) != RECOVERY_PRIOR_RUN_LOG_SHA256:
            fail("prior guarded-run log is missing or differs from its reviewed hash")
        recovery_evidence = {
            "used": True,
            "baseline_target_sha256": RECOVERY_BASELINE_TARGET_SHA256,
            "baseline_target_bytes": RECOVERY_BASELINE_TARGET_BYTES,
            "baseline_actor_count": RECOVERY_BASELINE_ACTOR_COUNT,
            "prior_guarded_run_log": RECOVERY_PRIOR_RUN_LOG.as_posix(),
            "prior_guarded_run_log_sha256": RECOVERY_PRIOR_RUN_LOG_SHA256,
            "original_world_before_template_creation": RECOVERY_ORIGINAL_WORLD,
            "reason": "PRIOR_RUN_CREATED_AND_SAVED_PURE_TEMPLATE_THEN_FAILED_BEFORE_EXPLICIT_STAGED_MAP_SAVE",
        }
    if BUILD_RECEIPT.exists():
        fail("build receipt already exists; v002 never overwrites")
    BUILD_RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    probe = BUILD_RECEIPT.parent / ".pressshop_v002_write_probe"
    if probe.exists():
        fail("build receipt write probe already exists")
    try:
        with probe.open("xb") as handle:
            handle.write(b"")
        probe.unlink()
    except OSError as error:
        fail("build receipt directory is not safely writable: {}".format(error))

    current_world = _editor_world()
    current_package = world_package_name(current_world)
    if recovery_resume:
        if current_package != TARGET_MAP:
            fail("exact recovery target must be the current editor world")
    elif current_package in {SOURCE_MAP, TARGET_MAP}:
        fail("fresh build must run from an unrelated editor world")
    dirty_before = dirty_package_paths()
    if dirty_before["maps"] or dirty_before["content"]:
        fail("editor has dirty packages before staging")

    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    asset_registry.scan_paths_synchronous([SOURCE_MAP.rsplit("/", 1)[0]], True, False)
    source_data = list(asset_registry.get_assets_by_package_name(_unreal_name(SOURCE_MAP), True) or [])
    source_world_data = [
        row for row in source_data
        if str(getattr(getattr(row, "asset_class_path", None), "asset_name", "")) == "World"
        or str(getattr(row, "asset_class", "")) == "World"
    ]
    if len(source_world_data) != 1:
        fail("source World asset did not resolve exactly once")
    if source_world_data[0].is_asset_loaded():
        fail("source map package is already loaded")

    # Assets/classes are preflighted before the target level is created.
    loaded_assets = preflight_candidate_assets(inputs)
    visual_class = _load_class(VISUAL_LAYER_CLASS_PATH)
    presentation_class = _load_class(PRESENTATION_CLASS_PATH)
    camera_class = _load_class(CAMERA_CLASS_PATH)
    dirty_after_asset_preflight = dirty_package_paths()
    if dirty_after_asset_preflight["maps"] or dirty_after_asset_preflight["content"]:
        fail("asset/class preflight dirtied packages before target-map creation")
    if recovery_resume:
        target_world = current_world
    else:
        level_editor_subsystem = _level_editor_subsystem()
        if not level_editor_subsystem.new_level_from_template(TARGET_MAP, SOURCE_MAP):
            fail("failed to create the isolated target map from the unopened OneFactory template")
        target_world = _editor_world()
    if world_package_name(target_world) != TARGET_MAP:
        fail("target map did not become the current editor world")

    actor_subsystem = _actor_subsystem()
    existing_actors = list(actor_subsystem.get_all_level_actors() or [])
    if recovery_resume and len(existing_actors) != RECOVERY_BASELINE_ACTOR_COUNT:
        fail("recovery target actor count differs from the pinned pure-template baseline")
    existing_fingerprints_before = {
        str(actor.get_path_name()): actor_fingerprint(actor) for actor in existing_actors
    }
    existing_labels = {str(actor.get_actor_label()) for actor in existing_actors}
    reserved_labels = {
        "VIS | " + row["spawn_spec_id"] for row in inputs["source"]["spawn"]["specs"]
    } | {"VIS | Press Shop 2126 | Overhead runtime presentation", FULL_CAMERA_LABEL, HERO_CAMERA_LABEL}
    collisions = sorted(existing_labels.intersection(reserved_labels))
    if collisions:
        fail("reserved actor labels already exist: {}".format(collisions))
    for actor in existing_actors:
        tags = {str(value) for value in list(actor.get_editor_property("tags") or [])}
        if SUPERSEDED_PRESENTATION_TAG in tags:
            fail("superseded runtime presentation is unexpectedly map-authored; review instead of hiding")
    class_counts_before: Dict[str, int] = {}
    for actor in existing_actors:
        name = _class_name(actor)
        class_counts_before[name] = class_counts_before.get(name, 0) + 1
    if class_counts_before.get(BOOTSTRAP_CLASS_NAME, 0) != 1 or class_counts_before.get(BUILD_AUTHORITY_CLASS_NAME, 0) != 1:
        fail("target duplicate does not preserve exactly one bootstrap/build authority")
    game_mode_before = world_game_mode_path(target_world)
    if _normalise_asset_path(game_mode_before) != EXPECTED_GAME_MODE:
        fail("OneFactory GameMode changed before staging")

    visual_actors, visual_records = spawn_visual_layers(
        actor_subsystem, visual_class, inputs["source"]["spawn"]["specs"], loaded_assets,
    )
    presentation_actor, presentation_record = spawn_presentation_adapter(
        actor_subsystem, presentation_class, inputs["source"]["anchors"],
    )
    full_camera, full_camera_record = spawn_camera(
        actor_subsystem, camera_class, FULL_CAMERA_LABEL,
        inputs["source"]["spawn"]["full_bounds"], FULL_CAMERA_ORTHO_WIDTH_CM,
    )
    hero_camera, hero_camera_record = spawn_camera(
        actor_subsystem, camera_class, HERO_CAMERA_LABEL,
        inputs["source"]["spawn"]["hero_bounds"], HERO_CAMERA_ORTHO_WIDTH_CM,
    )

    all_after = list(actor_subsystem.get_all_level_actors() or [])
    if len(all_after) != len(existing_actors) + EXPECTED_SPAWN_SPEC_COUNT + 3:
        fail("unexpected actor-count delta after staging")
    existing_fingerprints_after = {
        path: actor_fingerprint(next(actor for actor in all_after if str(actor.get_path_name()) == path))
        for path in existing_fingerprints_before
    }
    if existing_fingerprints_after != existing_fingerprints_before:
        fail("a pre-existing OneFactory actor changed while staging presentation")
    game_mode_after = world_game_mode_path(target_world)
    if game_mode_after != game_mode_before:
        fail("GameMode changed while staging presentation")
    dirty_pre_save = dirty_package_paths()
    if dirty_pre_save["content"]:
        fail("content assets became dirty while staging the map")
    if not dirty_pre_save["maps"] or any(_normalise_asset_path(value) != TARGET_MAP for value in dirty_pre_save["maps"]):
        fail("only the target map may be dirty before save")

    if not unreal.EditorLevelLibrary.save_current_level():
        fail("failed to save the target map")
    if not TARGET_FILE.is_file():
        fail("target map file is missing after save")
    dirty_after = dirty_package_paths()
    if dirty_after["maps"] or dirty_after["content"]:
        fail("dirty packages remain after the single target-map save")
    protected_after = protected_snapshot()
    if protected_after != protected_before:
        fail("a protected map/config/native source changed")

    receipt = {
        "schema": BUILD_RECEIPT_SCHEMA,
        "status": BUILD_RECEIPT_STATUS,
        "source_map": SOURCE_MAP,
        "source_map_sha256": SOURCE_FILE_SHA256,
        "source_package_loaded_before_template_creation": False,
        "target_creation_api": "LevelEditorSubsystem.new_level_from_template",
        "guarded_recovery_resume": recovery_evidence,
        "target_map": TARGET_MAP,
        "target_map_sha256": digest(TARGET_FILE),
        "target_map_bytes": TARGET_FILE.stat().st_size,
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
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "current_world_before_target_creation": (
            RECOVERY_ORIGINAL_WORLD if recovery_resume else current_package
        ),
        "dirty_packages_before": dirty_before,
        "dirty_packages_after_asset_preflight": dirty_after_asset_preflight,
        "dirty_packages_before_save": dirty_pre_save,
        "dirty_packages_after_save": dirty_after,
        "game_mode_before": game_mode_before,
        "game_mode_after": game_mode_after,
        "pre_existing_actor_count": len(existing_actors),
        "pre_existing_actor_fingerprints_before": existing_fingerprints_before,
        "pre_existing_actor_fingerprints_after": existing_fingerprints_after,
        "pre_existing_actor_fingerprints_unchanged": True,
        "duplicate_gameplay_controllers_spawned": False,
        "editor_hidden_existing_actor_count": 0,
        "runtime_superseded_presentation_tag": SUPERSEDED_PRESENTATION_TAG,
        "spawned_visual_layer_count": len(visual_actors),
        "candidate_asset_preflight_count": len(loaded_assets),
        "candidate_material_parent_and_sprite_texture_parameters_verified": True,
        "native_visual_layer_class": VISUAL_LAYER_CLASS_PATH,
        "native_presentation_class": PRESENTATION_CLASS_PATH,
        "editor_preview_policy": "BASE_WORKPIECE_MOVING_PLUS_OPEN_PRESSES_PARKED_ROBOTS_AND_SEQUENCE_FRAME_ZERO",
        "spawned_visual_layers": visual_records,
        "presentation_adapter": presentation_record,
        "cameras": [full_camera_record, hero_camera_record],
        "save_scope": {"save_current_level_calls": 1, "target_map_only": True},
        "map_integrated": True,
        "runtime_validated": False,
        "runtime_ready": False,
        "packaged_build_validated": False,
        "steam_capture_validated": False,
        "unresolved_source_rows": inputs["source"]["manifest"].get("unresolved_rows", []),
    }
    _write_new_json(BUILD_RECEIPT, receipt)
    unreal.log("PRESSSHOP_2126_OVERHEAD_PLAYABLE_V002_BUILD_PASS: {}".format(TARGET_MAP))


if __name__ == "__main__":
    main()
