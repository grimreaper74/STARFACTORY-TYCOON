"""Guarded saved-map visual-evidence capture for Press Shop 2126 v006.

This lane reads only the completed v006 candidate map and its canonical
installer receipt.  The independently reviewed SHA-256 of each is mandatory
through the environment because installation is deliberately outside this
script.  It validates the complete correction plan and the loaded saved map,
then renders exactly three 1920x1080 PNGs from the three saved orthographic
camera actors through transient native SceneCapture2D actors.

The evidence written by this script is saved-map visual evidence only.  It is
not PIE lifecycle evidence, runtime simulation evidence, packaged-build
evidence, performance evidence, or Steam visual-quality approval.  The script
never saves a map or asset, creates/imports a Content asset, or writes beneath
Content.  Temporary visibility changes are restored before its append-only
receipt is written.

Run from an unrelated clean editor map with a rendering RHI.  Do not use
-NullRHI.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

try:  # Importable by ordinary CPython offline tests.
    import unreal  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - outside Unreal only.
    unreal = None  # type: ignore


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
INSTALLER = PROJECT / "Tools/install_pressshop_2126_overhead_presentation_correction_v001.py"
# Frozen after the v006 installer authoring lane completed its offline contract.
INSTALLER_SHA256 = "23322ded25bb4b3cfad116f28aeb162ccb8a695cdf38428c0718e7f09ec3c5ce"
BASE_CAPTURE = PROJECT / "Tools/capture_pressshop_2126_overhead_presentation_v004.py"
BASE_CAPTURE_SHA256 = "cb627f2f4728d5a1434de3cada1b99c449b33f8fdd01fed72e87a3c251c78562"

TARGET_MAP = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v006/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v006"
)
TARGET_FILE = (
    PROJECT / "Content/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v006/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v006.umap"
)
INSTALL_RECEIPT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadPresentation_v006/"
    "install_receipt_v001.json"
)
OUTPUT_DIR = (
    PROJECT / "Saved/PressShop2126/"
    "OverheadPresentation_v006_SavedMapCapture_v001"
)
CAPTURE_RECEIPT = OUTPUT_DIR / "saved_map_capture_receipt_v001.json"

MAP_SHA_ENV = "LB_PRESSSHOP_V006_TARGET_MAP_SHA256"
RECEIPT_SHA_ENV = "LB_PRESSSHOP_V006_INSTALL_RECEIPT_SHA256"

INSTALL_SCHEMA = "cairnwell.press_shop.overhead_presentation_correction_install_receipt.v001"
INSTALL_STATUS = (
    "PASS_CANDIDATE_PRESENTATION_CORRECTION_APPLIED__V005_VISUALS_PRESERVED__"
    "FRESH_CAPTURE_AND_PIE_PENDING"
)
CAPTURE_SCHEMA = (
    "cairnwell.press_shop.overhead_presentation_v006_saved_map_capture_receipt.v001"
)
CAPTURE_STATUS = (
    "PASS_IN_ENGINE_V006_SAVED_MAP_VISUAL_EVIDENCE_ONLY__"
    "PIE_AND_STEAM_NOT_VALIDATED"
)

EXPECTED_GAME_MODE = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
EXPECTED_ACTOR_COUNT = 302
EXPECTED_VISUAL_COUNT = 146
EXPECTED_MACHINERY_COUNT = 120
EXPECTED_CARGO_COUNT = 26
EXPECTED_PRESENTATION_COUNT = 140
EXPECTED_PRESENTATION_DECK_COUNT = 137
EXPECTED_RUNTIME_PRESENTATION_COUNT = 1
EXPECTED_CAMERA_COUNT = 3
EXPECTED_CORRECTION_TAG_COUNT = 83
EXPECTED_V005_UPGRADE_TAG_COUNT = 116
EXPECTED_V004_POLISH_TAG_COUNT = 41
EXPECTED_ROUTE_PORT_COUNT = 12

CAPTURE_WIDTH = 1920
CAPTURE_HEIGHT = 1080
NUMERIC_TOLERANCE = 0.001

VISUAL_CLASS = "/Script/LineBossCarFactory.LBPressShopOverheadVisualLayerActor"
PRESENTATION_CLASS = "/Script/LineBossCarFactory.LBPressShopOverheadPresentationActor"
STATIC_MESH_CLASS = "/Script/Engine.StaticMeshActor"
TEXT_RENDER_CLASS = "/Script/Engine.TextRenderActor"
CAMERA_CLASS = "/Script/Engine.CameraActor"
CUBE_ASSET = "/Engine/BasicShapes/Cube"

VISUAL_TAG = "LB.PressShop.Overhead.VisualLayer.v001"
PRESENTATION_ADAPTER_TAG = "LB.PressShop.OverheadPresentation.v001"
PRESENTATION_PASS_TAG = "LB.PressShop.OverheadDeckPresentation.v002"
PRESENTATION_CAMERA_TAG = "LB.PressShop.OverheadDeck.Camera.v002"
CARGO_MAP_TAG = "LB.PressShop.OverheadCargoMap.v003"
CARGO_SOURCE_TAG = "LB.PressShop.CargoContinuity.v001"
V004_POLISH_TAG = "LB.PressShop.OverheadPresentationPolish.v004"
V005_UPGRADE_TAG = "LB.PressShop.OverheadPresentationUpgrade.v005"
V006_CORRECTION_TAG = "LB.PressShop.OverheadPresentationCorrection.v006"
CAMERA_V006_TAG = "LB.PressShop.OverheadDeck.Camera.v006"
VISUAL_ONLY_TAG = "LB.Environment.VisualOnly"
NOT_WIP_TAG = "LB.NotProcessWIP"
ROLE_PREFIX = "LB.PressShop.OverheadDeck.Role."
CAMERA_ROLE_PREFIXES = (
    "LB.PressShop.OverheadDeck.Camera.Overview.",
    "LB.PressShop.OverheadDeck.Camera.PressSpine.",
    "LB.PressShop.OverheadDeck.Camera.SteamHero.",
)

COLLISION_CHANNEL_NAMES = (
    "ECC_WORLD_STATIC", "ECC_WORLD_DYNAMIC", "ECC_PAWN", "ECC_VISIBILITY",
    "ECC_CAMERA", "ECC_PHYSICS_BODY", "ECC_VEHICLE", "ECC_DESTRUCTIBLE",
)

CAMERA_ROTATION = (-90.0, 0.0, 0.0)
CAMERA_SPECS: Mapping[str, Mapping[str, Any]] = {
    "overview": {
        "label": "CAM | Press Shop 2126 | complete flow overview v006",
        "location_cm": (-7436.895880159617, 8840.218280826943, 21712.544),
        "rotation_deg_pitch_yaw_roll": CAMERA_ROTATION,
        "ortho_width_cm": 16200.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.Overview.v006",
        "filename": "PressShop2126_PresentationOverview_1920x1080_v006.png",
    },
    "press_spine": {
        "label": "CAM | Press Shop 2126 | production spine close v006",
        "location_cm": (-8095.0, 11125.0, 21712.544),
        "rotation_deg_pitch_yaw_roll": CAMERA_ROTATION,
        "ortho_width_cm": 11200.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.PressSpine.v006",
        "filename": "PressShop2126_PresentationSpine_1920x1080_v006.png",
    },
    "steam_hero": {
        "label": "CAM | Press Shop 2126 | S03-S06 framed Steam hero v006",
        "location_cm": (-8855.75, 11092.0, 21712.544),
        "rotation_deg_pitch_yaw_roll": CAMERA_ROTATION,
        "ortho_width_cm": 5700.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.SteamHero.v006",
        "filename": "PressShop2126_PresentationPressHero_1920x1080_v006.png",
    },
}

# The frozen coherent still from v004/v005 remains the visual-state contract.
SELECTED_SOURCE_IDS = {
    "LAYER_096_S07_InspectionCell_BaseEmpty_v001",
    "LAYER_109_S07_PalletisingCell_BaseEmpty_v001",
    "LAYER_070_S02_FRAME_OPEN_v001", "LAYER_074_S03_FRAME_OPEN_v001",
    "LAYER_078_S04_FRAME_OPEN_v001", "LAYER_082_S05_FRAME_OPEN_v001",
    "LAYER_086_S06_FRAME_OPEN_v001", "LAYER_088_S07_ExitConveyor_BeltMotion_00_v001",
    "LAYER_105_S07_PalletStack_00_Overlay_v001", "LAYER_111_S07_ROBOT_A_PARKED",
    "LAYER_115_S07_ROBOT_B_PARKED", "LAYER_037_IN03_storage_base_v001",
    "LAYER_003_IN04_depack_base_sprite_v001", "LAYER_038_IN05_bare_coil_saddle_v001",
    "LAYER_040_S01A_coil_rack_base_v001", "LAYER_041_S01B_decoiler_base_v001",
    "LAYER_058_S01C_straightener_base_v001", "LAYER_059_S01D_feed_bridge_base_v001",
    "LAYER_001_IN01A_tractor_sprite_v002", "LAYER_002_IN01B_trailer_sidesaddle_sprite_v002",
    "LAYER_036_IN02_coil_handler_agv_v001", "LAYER_004_IN04_drive_rollers_frame_00_v001",
    "LAYER_020_IN04_film_takeup_frame_00_v001", "LAYER_039_S01A_coil_cart_base_v001",
    "LAYER_042_S01B_decoiler_spindle_payoff_frame_00_v001",
    "LAYER_050_S01C_entry_strip_pulse_frame_00_v001",
    "LAYER_060_S01D_feed_strip_pulse_frame_00_v001",
    "LAYER_110_IN05_BARE_COIL_AT_SADDLE",
}
SELECTED_CARGO_IDS = {
    "WRAPPED_IN01_UNLOAD", "WRAPPED_IN03_BUFFERED", "BARE_IN05_OUTPUT_TO_RACK",
    "S02_PANEL_BLANK", "S03_WORKPIECE_REGISTERED", "S04_WORKPIECE_REGISTERED",
    "S05_WORKPIECE_REGISTERED", "S06_WORKPIECE_REGISTERED", "S07_PANEL_INSPECT",
    "S07_PALLET_BASE_PARKED", "S07_DISPATCH_STACK_08",
}


class CaptureGuardError(RuntimeError):
    """The v006 read-only saved-map capture contract rejected the state."""


def fail(message: str) -> None:
    raise CaptureGuardError(
        "PRESSSHOP_2126_OVERHEAD_PRESENTATION_V006_SAVED_MAP_CAPTURE_FAIL: "
        + message
    )


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest().lower()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2,
                       sort_keys=True) + "\n").encode("utf-8")


def _require_sha(value: Any, context: str) -> str:
    if (not isinstance(value, str)
            or re.fullmatch(r"[0-9a-f]{64}", value) is None
            or len(set(value)) < 2):
        fail(context + " must be an explicit non-placeholder lower-case SHA-256")
    return value


def required_guard_hashes(
    environ: Mapping[str, str] | None = None,
) -> Tuple[str, str]:
    values = os.environ if environ is None else environ
    map_sha = _require_sha(values.get(MAP_SHA_ENV), MAP_SHA_ENV)
    receipt_sha = _require_sha(values.get(RECEIPT_SHA_ENV), RECEIPT_SHA_ENV)
    if map_sha == receipt_sha:
        fail("map and receipt SHA-256 guards must be independent")
    return map_sha, receipt_sha


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail("could not import frozen helper: " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _close(left: Sequence[Any], right: Sequence[Any]) -> bool:
    if len(left) != len(right):
        return False
    try:
        return all(math.isfinite(float(a)) and math.isfinite(float(b))
                   and abs(float(a) - float(b)) <= NUMERIC_TOLERANCE
                   for a, b in zip(left, right))
    except (TypeError, ValueError):
        return False


def _rotation_close(left: Sequence[Any], right: Sequence[Any]) -> bool:
    if len(left) != len(right):
        return False

    def quaternion(values: Sequence[Any]) -> Tuple[float, float, float, float]:
        pitch, yaw, roll = (math.radians(float(value)) / 2.0 for value in values)
        sr, cr = math.sin(roll), math.cos(roll)
        sp, cp = math.sin(pitch), math.cos(pitch)
        sy, cy = math.sin(yaw), math.cos(yaw)
        return (sr*cp*cy-cr*sp*sy, cr*sp*cy+sr*cp*sy,
                cr*cp*sy-sr*sp*cy, cr*cp*cy+sr*sp*sy)

    try:
        dot = sum(a*b for a, b in zip(quaternion(left), quaternion(right)))
    except (TypeError, ValueError):
        return False
    return 1.0 - abs(dot) <= NUMERIC_TOLERANCE


def _asset_path(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value.get_path_name()) if hasattr(value, "get_path_name") else str(value)
    if raw.startswith("Class'") and raw.endswith("'"):
        raw = raw[6:-1]
    return raw.split(".", 1)[0] if raw.startswith(("/Game/", "/Engine/")) else raw


def virtual_to_uasset(asset_path: str) -> Path:
    if not asset_path.startswith("/Game/"):
        fail("not a /Game asset path: " + asset_path)
    content = (PROJECT / "Content").resolve()
    result = (content / (asset_path.removeprefix("/Game/") + ".uasset")).resolve()
    if not result.is_relative_to(content):
        fail("asset path escapes Content: " + asset_path)
    return result


def _installer_contract() -> Dict[str, Any]:
    if not INSTALLER.is_file() or digest(INSTALLER) != INSTALLER_SHA256:
        fail("v006 installer contract file is missing or changed")
    try:
        correction = _load_module(
            INSTALLER, "pressshop_v006_installer_saved_capture_contract"
        )
        source_receipt = correction.validate_source_receipt()
        source_capture = correction.validate_source_capture()
        plan = correction.build_correction_plan(source_receipt)
        validation = correction.validate_correction_plan(plan, source_receipt)
        protected = correction.protected_snapshot()
        reused = correction.validate_material_locks()
    except CaptureGuardError:
        raise
    except Exception as error:
        fail("v006 installer contract could not be rebuilt: " + str(error))
    exact = {
        "TARGET_MAP": TARGET_MAP,
        "INSTALL_RECEIPT_SCHEMA": INSTALL_SCHEMA,
        "INSTALL_STATUS": INSTALL_STATUS,
        "EXPECTED_FINAL_ACTOR_COUNT": EXPECTED_ACTOR_COUNT,
        "EXPECTED_FINAL_PRESENTATION_COUNT": EXPECTED_PRESENTATION_COUNT,
        "EXPECTED_VISUAL_COUNT": EXPECTED_VISUAL_COUNT,
        "EXPECTED_MACHINERY_COUNT": EXPECTED_MACHINERY_COUNT,
        "EXPECTED_CARGO_COUNT": EXPECTED_CARGO_COUNT,
        "EXPECTED_TOTAL_MUTATION_COUNT": EXPECTED_CORRECTION_TAG_COUNT,
        "CAMERA_ROTATION": CAMERA_ROTATION,
        "V006_CORRECTION_TAG": V006_CORRECTION_TAG,
        "CAMERA_V006_TAG": CAMERA_V006_TAG,
    }
    for name, expected in exact.items():
        if getattr(correction, name, None) != expected:
            fail("v006 installer constant changed: " + name)
    if len(plan.get("mutations", [])) != EXPECTED_CORRECTION_TAG_COUNT:
        fail("v006 rebuilt correction inventory changed")
    if (validation.get("station_port_count") != EXPECTED_ROUTE_PORT_COUNT
            or validation.get("station_connector_max_gap_cm") != 0.0):
        fail("v006 rebuilt zero-gap route contract changed")
    if set(correction.CAMERA_TARGETS) != set(CAMERA_SPECS):
        fail("v006 installer camera id inventory changed")
    for item_id, spec in CAMERA_SPECS.items():
        target = correction.CAMERA_TARGETS[item_id]
        if (target.get("label") != spec["label"]
                or target.get("role_tag") != spec["role_tag"]
                or not _close(target.get("location_cm", ()), spec["location_cm"])
                or not _close((target.get("ortho_width_cm"),),
                              (spec["ortho_width_cm"],))):
            fail("v006 installer camera target changed: " + item_id)
    expected_material_specs = {
        str(asset): {"role": str(spec["role"]), "srgb_hex": str(spec["srgb_hex"])}
        for asset, spec in correction.CANDIDATE_MATERIAL_SPECS.items()
    }
    if len(expected_material_specs) != 2:
        fail("v006 candidate material inventory changed")
    return {
        "module": correction, "source_receipt": source_receipt,
        "source_capture": source_capture, "plan": plan,
        "validation": validation, "protected": protected,
        "reused_materials": reused,
        "candidate_material_specs": expected_material_specs,
    }


def _index(rows: Any, context: str, count: int) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(rows, list) or len(rows) != count:
        fail(context + " count changed")
    result: Dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("id"), str):
            fail(context + " contains an invalid row")
        if row["id"] in result:
            fail(context + " contains duplicate id: " + str(row["id"]))
        result[str(row["id"])] = row
    return result


def _valid_no_collision_receipt(value: Any) -> bool:
    return bool(
        isinstance(value, Mapping)
        and value.get("actor_collision_enabled") is False
        and "NO_COLLISION" in str(value.get("component_collision_enabled", "")).upper()
        and value.get("generate_overlap_events") is False
        and value.get("can_ever_affect_navigation") is False
        and value.get("ignored_channels") == list(COLLISION_CHANNEL_NAMES)
        and value.get("profile_acceptance") in {
            "NativeNoCollisionWithIgnoreAll", "CustomWithNoCollisionAndIgnoreAll"
        }
    )


def _validate_mutation_receipt(
    row: Mapping[str, Any], mutation: Mapping[str, Any]
) -> None:
    item_id = str(mutation["id"])
    kind = str(mutation["kind"])
    target = mutation["target"]
    actor_path = str(row.get("actor_path", ""))
    if (row.get("id") != item_id or row.get("kind") != kind
            or not actor_path.startswith(TARGET_MAP + ".")
            or row.get("label") != target["label"]
            or not _close(row.get("location_cm", ()), target["location_cm"])):
        fail("v006 mutation receipt identity changed: " + item_id)
    if kind == "box":
        if (not _close(row.get("dimensions_cm", ()), target["dimensions_cm"])
                or row.get("material") != target["material"]
                or not _valid_no_collision_receipt(row.get("collision_readback"))):
            fail("v006 box mutation receipt changed: " + item_id)
    elif kind == "text":
        if (not _close((row.get("world_size_cm"),), (target["world_size_cm"],))
                or row.get("colour_rgba") != target["colour_rgba"]
                or not _valid_no_collision_receipt(row.get("collision_readback"))):
            fail("v006 text mutation receipt changed: " + item_id)
    elif kind == "camera":
        if (not _close((row.get("ortho_width_cm"),), (target["ortho_width_cm"],))
                or row.get("role_tag") != target["role_tag"]
                or "collision_readback" in row):
            fail("v006 camera mutation receipt changed: " + item_id)
    else:
        fail("unknown v006 mutation kind: " + kind)


def validate_install_receipt(
    receipt: Mapping[str, Any], expected_map_sha: str, actual_map_bytes: int,
    contract: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Validate the canonical installer receipt against the frozen plan."""
    contract = _installer_contract() if contract is None else dict(contract)
    correction = contract["module"]
    plan = contract["plan"]
    validation = contract["validation"]
    if receipt.get("schema") != INSTALL_SCHEMA or receipt.get("status") != INSTALL_STATUS:
        fail("v006 install receipt schema or status changed")
    exact = {
        "candidate_only": True,
        "source_map": correction.SOURCE_MAP,
        "source_map_sha256": correction.SOURCE_FILE_SHA256,
        "source_map_bytes": correction.SOURCE_FILE_BYTES,
        "source_receipt": correction.SOURCE_RECEIPT.as_posix(),
        "source_receipt_sha256": correction.SOURCE_RECEIPT_SHA256,
        "source_capture_receipt": correction.SOURCE_CAPTURE_RECEIPT.as_posix(),
        "source_capture_receipt_sha256": correction.SOURCE_CAPTURE_RECEIPT_SHA256,
        "target_map": TARGET_MAP,
        "target_map_sha256": expected_map_sha,
        "target_map_bytes": actual_map_bytes,
        "target_creation_api": "LevelEditorSubsystem.new_level_from_template",
        "source_actor_count": EXPECTED_ACTOR_COUNT,
        "final_actor_count": EXPECTED_ACTOR_COUNT,
        "source_presentation_actor_count": EXPECTED_PRESENTATION_COUNT,
        "final_presentation_actor_count": EXPECTED_PRESENTATION_COUNT,
        "combined_visual_layer_count": EXPECTED_VISUAL_COUNT,
        "machinery_visual_layer_count": EXPECTED_MACHINERY_COUNT,
        "cargo_layer_count": EXPECTED_CARGO_COUNT,
        "machinery_actor_mutated_count": 0,
        "cargo_actor_mutated_count": 0,
        "source_actor_removed_count": 0,
        "source_actor_created_count": 0,
        "mutated_existing_presentation_actor_count": EXPECTED_CORRECTION_TAG_COUNT,
        "mutated_station_zone_actor_count": 36,
        "mutated_route_actor_count": 29,
        "created_presentation_box_count": 0,
        "created_presentation_boxes": [],
        "machine_or_cargo_transform_mutations": 0,
        "new_machinery_geometry": 0,
        "new_cargo_geometry": 0,
        "collision_enabled_on_created_presentation": False,
        "native_cpp_modified": False,
        "roof_created": False,
        "game_mode_before": EXPECTED_GAME_MODE,
        "game_mode_after": EXPECTED_GAME_MODE,
        "dirty_packages_before_save": {"content": [], "maps": [TARGET_MAP]},
        "dirty_packages_after_save": {"content": [], "maps": []},
        "runtime_validated": False,
        "pie_validated": False,
        "cook_validated": False,
        "packaged_build_validated": False,
        "visual_capture_validated": False,
        "steam_capture_validated": False,
        "steam_visual_quality_human_approved": False,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("v006 install receipt field changed: " + key)
    source_hash_fields = {
        "source_path_keyed_visual_fingerprints_sha256":
            correction.EXPECTED_SOURCE_HASHES["combined_visual"],
        "source_path_keyed_machinery_fingerprints_sha256":
            correction.EXPECTED_SOURCE_HASHES["machinery_visual"],
        "source_path_keyed_cargo_fingerprints_sha256":
            correction.EXPECTED_SOURCE_HASHES["cargo_visual"],
    }
    for key, expected in source_hash_fields.items():
        if receipt.get(key) != expected:
            fail("v006 source visual fingerprint evidence changed: " + key)

    if receipt.get("plan_validation") != validation:
        fail("v006 receipt no longer embeds the exact correction-plan validation")
    if (validation.get("mutation_count") != EXPECTED_CORRECTION_TAG_COUNT
            or validation.get("station_port_count") != EXPECTED_ROUTE_PORT_COUNT
            or validation.get("station_branch_count") != EXPECTED_ROUTE_PORT_COUNT
            or validation.get("station_connector_max_gap_cm") != 0.0):
        fail("v006 plan validation route or mutation evidence changed")
    if (receipt.get("protected_hashes_before") != contract["protected"]
            or receipt.get("protected_hashes_after") != contract["protected"]):
        fail("v006 protected-map hash contract changed")
    if (receipt.get("reused_material_hashes_before") != contract["reused_materials"]
            or receipt.get("reused_material_hashes_after") != contract["reused_materials"]):
        fail("v006 reused-material hash contract changed")

    for before_key, after_key in (
        ("visual_layer_actor_semantic_fingerprints_before_sha256",
         "visual_layer_actor_semantic_fingerprints_after_sha256"),
        ("machinery_actor_semantic_fingerprints_before_sha256",
         "machinery_actor_semantic_fingerprints_after_sha256"),
        ("cargo_actor_semantic_fingerprints_before_sha256",
         "cargo_actor_semantic_fingerprints_after_sha256"),
    ):
        before = _require_sha(receipt.get(before_key), before_key)
        after = _require_sha(receipt.get(after_key), after_key)
        if before != after:
            fail("v006 preserved semantic fingerprint pair changed: " + before_key)

    mutations = _index(
        receipt.get("presentation_mutations"), "v006 presentation mutations",
        EXPECTED_CORRECTION_TAG_COUNT,
    )
    expected_ids = [str(row["id"]) for row in plan["mutations"]]
    if list(mutations) != expected_ids:
        fail("v006 mutation ordering or id inventory changed")
    for mutation in plan["mutations"]:
        _validate_mutation_receipt(mutations[str(mutation["id"])], mutation)
    paths = [str(row["actor_path"]) for row in mutations.values()]
    if len(paths) != len(set(paths)):
        fail("v006 mutation receipt contains duplicate actor paths")

    expected_style = {
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
    }
    if receipt.get("presentation_style") != expected_style:
        fail("v006 presentation-style contract changed")

    material_rows = receipt.get("candidate_materials")
    if not isinstance(material_rows, list) or len(material_rows) != 2:
        fail("v006 candidate-material receipt inventory changed")
    materials: Dict[str, Mapping[str, Any]] = {}
    for row in material_rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("asset"), str):
            fail("v006 candidate-material receipt contains an invalid row")
        asset = str(row["asset"])
        if asset in materials:
            fail("v006 candidate-material receipt contains a duplicate asset")
        materials[asset] = row
    if set(materials) != set(contract["candidate_material_specs"]):
        fail("v006 candidate-material asset set changed")
    packages: Dict[str, Dict[str, Any]] = {}
    for asset, spec in contract["candidate_material_specs"].items():
        row = materials[asset]
        linear = list(correction._v005.srgb_hex_to_linear(spec["srgb_hex"]))
        if (row.get("role") != spec["role"]
                or row.get("srgb_hex") != spec["srgb_hex"]
                or row.get("shading_model") != "UNLIT"
                or not _close(row.get("linear_rgb", ()), linear)
                or not _close(row.get("linear_rgb_readback", ()), linear)
                or not isinstance(row.get("bytes"), int) or int(row["bytes"]) <= 0):
            fail("v006 candidate-material contract changed: " + asset)
        sha = _require_sha(row.get("sha256"), "candidate material sha256")
        packages[asset] = {
            "role": spec["role"], "srgb_hex": spec["srgb_hex"],
            "sha256": sha, "bytes": int(row["bytes"]),
        }
    if receipt.get("candidate_material_packages") != packages:
        fail("v006 candidate-material package snapshot changed")
    return {
        **contract,
        "mutations": mutations,
        "candidate_materials": materials,
        "candidate_material_packages": packages,
    }


def load_guarded_install_receipt(
    expected_map_sha: str, expected_receipt_sha: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Load only the independently hash-approved installed result."""
    if not TARGET_FILE.is_file() or not INSTALL_RECEIPT.is_file():
        fail("v006 target map or install receipt is missing")
    if digest(TARGET_FILE) != expected_map_sha:
        fail("v006 target map hash differs from supplied final hash")
    if digest(INSTALL_RECEIPT) != expected_receipt_sha:
        fail("v006 install receipt hash differs from supplied final hash")
    payload = INSTALL_RECEIPT.read_bytes()
    try:
        receipt = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail("v006 install receipt is not valid UTF-8 JSON: " + str(error))
    if not isinstance(receipt, dict) or payload != canonical_json_bytes(receipt):
        fail("v006 install receipt is not canonical JSON")
    contract = validate_install_receipt(
        receipt, expected_map_sha, TARGET_FILE.stat().st_size
    )
    for asset, row in contract["candidate_material_packages"].items():
        disk = virtual_to_uasset(asset)
        if (not disk.is_file() or disk.stat().st_size != int(row["bytes"])
                or digest(disk) != row["sha256"]):
            fail("v006 candidate material package differs from receipt: " + asset)
    return receipt, contract


def ensure_output_absent(path: Path = OUTPUT_DIR) -> None:
    if path.exists():
        fail("refusing to overwrite or merge capture evidence: " + str(path))


def _require_unreal() -> Any:
    if unreal is None:
        fail("this saved-map capture must run inside Unreal Editor Python")
    return unreal


def _base_capture_module() -> Any:
    if not BASE_CAPTURE.is_file() or digest(BASE_CAPTURE) != BASE_CAPTURE_SHA256:
        fail("native SceneCapture2D helper is missing or changed")
    base = _load_module(BASE_CAPTURE, "pressshop_v004_capture_runtime_helpers_for_v006")
    base.OUTPUT_DIR = OUTPUT_DIR
    base.CAPTURE_RECEIPT = CAPTURE_RECEIPT
    base.CAMERA_SPECS = CAMERA_SPECS
    return base


def _class_path(actor: Any) -> str:
    return str(actor.get_class().get_path_name())


def _tags(actor: Any) -> set[str]:
    return {str(tag) for tag in list(actor.tags or [])}


def _transform(actor: Any) -> Dict[str, List[float]]:
    value = actor.get_actor_transform()
    rotation = value.rotation.rotator()
    return {
        "location_cm": [float(value.translation.x), float(value.translation.y),
                        float(value.translation.z)],
        "rotation_deg_pitch_yaw_roll": [float(rotation.pitch), float(rotation.yaw),
                                          float(rotation.roll)],
        "scale3d": [float(value.scale3d.x), float(value.scale3d.y),
                    float(value.scale3d.z)],
    }


def _colour_rgba(component: Any) -> List[int]:
    colour = component.get_editor_property("text_render_color")
    return [int(colour.r), int(colour.g), int(colour.b), int(colour.a)]


def _component_material(component: Any) -> str | None:
    return _asset_path(component.get_material(0))


def _validate_no_collision(actor: Any, component: Any, item_id: str) -> None:
    ue = _require_unreal()
    if (bool(actor.get_actor_enable_collision())
            or "NO_COLLISION" not in str(component.get_collision_enabled()).upper()):
        fail("v006 presentation primitive retained collision: " + item_id)
    if (bool(component.get_editor_property("generate_overlap_events"))
            or bool(component.get_editor_property("can_ever_affect_navigation"))):
        fail("v006 presentation primitive retained overlap/navigation: " + item_id)
    for channel_name in COLLISION_CHANNEL_NAMES:
        response = str(component.get_collision_response_to_channel(
            getattr(ue.CollisionChannel, channel_name)
        ))
        if "ECR_IGNORE" not in response.upper():
            fail("v006 presentation collision response changed: " + item_id)


def _exact_role_tags(tags: Iterable[str]) -> List[str]:
    return sorted(tag for tag in tags if tag.startswith(ROLE_PREFIX))


def _exact_camera_role_tags(tags: Iterable[str]) -> List[str]:
    return sorted(
        tag for tag in tags if any(tag.startswith(prefix) for prefix in CAMERA_ROLE_PREFIXES)
    )


def _validate_mutated_actor(
    actor: Any, row: Mapping[str, Any], mutation: Mapping[str, Any]
) -> None:
    item_id = str(mutation["id"])
    kind = str(mutation["kind"])
    target = mutation["target"]
    transform = _transform(actor)
    tags = _tags(actor)
    if (str(actor.get_path_name()) != row["actor_path"]
            or str(actor.get_actor_label()) != target["label"]
            or V006_CORRECTION_TAG not in tags
            or PRESENTATION_PASS_TAG not in tags
            or VISUAL_TAG in tags or CARGO_MAP_TAG in tags):
        fail("loaded v006 correction identity changed: " + item_id)
    if not _close(transform["location_cm"], target["location_cm"]):
        fail("loaded v006 correction location changed: " + item_id)
    if kind == "box":
        component = actor.get_editor_property("static_mesh_component")
        expected_rotation = target.get("rotation_deg_pitch_yaw_roll", [0.0, 0.0, 0.0])
        expected_role = ROLE_PREFIX + str(target["role"])
        if (_class_path(actor) != STATIC_MESH_CLASS
                or not _rotation_close(
                    transform["rotation_deg_pitch_yaw_roll"], expected_rotation
                )
                or not _close(
                    transform["scale3d"],
                    [float(value) / 100.0 for value in target["dimensions_cm"]],
                )
                or _asset_path(component.get_editor_property("static_mesh")) != CUBE_ASSET
                or _component_material(component) != target["material"]
                or _exact_role_tags(tags) != [expected_role]
                or bool(component.get_editor_property("cast_shadow"))):
            fail("loaded v006 presentation box changed: " + item_id)
        _validate_no_collision(actor, component, item_id)
    elif kind == "text":
        component = actor.get_editor_property("text_render")
        if (_class_path(actor) != TEXT_RENDER_CLASS
                or not _rotation_close(
                    transform["rotation_deg_pitch_yaw_roll"],
                    target["rotation_deg_pitch_yaw_roll"],
                )
                or str(component.get_editor_property("text")) != str(target["text"])
                or not _close(
                    (component.get_editor_property("world_size"),),
                    (target["world_size_cm"],),
                )
                or _colour_rgba(component) != [int(value) for value in target["colour_rgba"]]
                or bool(component.get_editor_property("cast_shadow"))):
            fail("loaded v006 presentation text changed: " + item_id)
        _validate_no_collision(actor, component, item_id)
    elif kind == "camera":
        component = actor.get_editor_property("camera_component")
        if (_class_path(actor) != CAMERA_CLASS
                or not _rotation_close(
                    transform["rotation_deg_pitch_yaw_roll"], CAMERA_ROTATION
                )
                or "ORTHOGRAPHIC" not in str(
                    component.get_editor_property("projection_mode")
                ).upper()
                or not _close(
                    (component.get_editor_property("ortho_width"),),
                    (target["ortho_width_cm"],),
                )
                or not _close(
                    (component.get_editor_property("aspect_ratio"),), (16.0 / 9.0,)
                )
                or not bool(component.get_editor_property("constrain_aspect_ratio"))
                or PRESENTATION_CAMERA_TAG not in tags
                or V005_UPGRADE_TAG not in tags
                or CAMERA_V006_TAG not in tags
                or _exact_camera_role_tags(tags) != [target["role_tag"]]):
            fail("loaded v006 saved camera changed: " + item_id)
    else:
        fail("unknown loaded v006 correction kind: " + kind)


def _route_gap_readback(
    actors_by_id: Mapping[str, Any], plan: Mapping[str, Any]
) -> Dict[str, Any]:
    branches: Dict[str, Any] = {}
    caps: Dict[str, Any] = {}
    for mutation in plan["mutations"]:
        item_id = str(mutation["id"])
        target = mutation["target"]
        role = str(target.get("role", ""))
        if role == "StationRouteBranch" or item_id.startswith("FLOW_CONNECTOR"):
            parts = str(target["label"]).split(" | ")
            if len(parts) < 2:
                fail("v006 route branch label no longer identifies a station")
            branches[parts[1].split()[0]] = actors_by_id[item_id]
        elif role == "StationPortCap":
            caps[item_id.removeprefix("STATION_PORT_CAP_")] = actors_by_id[item_id]
    if set(branches) != set(caps) or len(caps) != EXPECTED_ROUTE_PORT_COUNT:
        fail("loaded v006 route does not contain exactly 12 paired ports")
    gaps: Dict[str, float] = {}
    for station in sorted(caps):
        branch_transform = _transform(branches[station])
        cap_transform = _transform(caps[station])
        branch_left_x = (
            branch_transform["location_cm"][0]
            - branch_transform["scale3d"][0] * 100.0 / 2.0
        )
        gap = abs(branch_left_x - cap_transform["location_cm"][0])
        if gap > NUMERIC_TOLERANCE:
            fail("loaded v006 station route port is not zero-gap: " + station)
        gaps[station] = gap
    return {"station_port_count": len(gaps), "station_connector_gaps_cm": gaps,
            "station_connector_max_gap_cm": max(gaps.values())}


def validate_loaded_world(
    world: Any, actors: Sequence[Any], contract: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> Dict[str, Any]:
    """Validate the exact loaded saved map before any transient capture state."""
    if str(world.get_outermost().get_name()) != TARGET_MAP:
        fail("exact v006 saved map is not the current editor world")
    game_mode = _asset_path(
        world.get_world_settings().get_editor_property("default_game_mode")
    )
    if game_mode != EXPECTED_GAME_MODE or len(actors) != EXPECTED_ACTOR_COUNT:
        fail("v006 loaded world GameMode or actor count changed")
    by_path = {str(actor.get_path_name()): actor for actor in actors}
    if len(by_path) != len(actors):
        fail("v006 loaded actor paths are duplicated")

    visuals = [actor for actor in actors if _class_path(actor) == VISUAL_CLASS]
    cargo = [actor for actor in visuals if CARGO_MAP_TAG in _tags(actor)]
    machinery = [actor for actor in visuals if CARGO_MAP_TAG not in _tags(actor)]
    if (len(visuals), len(machinery), len(cargo)) != (
            EXPECTED_VISUAL_COUNT, EXPECTED_MACHINERY_COUNT, EXPECTED_CARGO_COUNT):
        fail("v006 loaded machinery/cargo visual inventory changed")
    if any(VISUAL_TAG not in _tags(actor) or CARGO_SOURCE_TAG not in _tags(actor)
           or V006_CORRECTION_TAG in _tags(actor)
           or not str(actor.get_actor_label()).startswith("CARGO | ") for actor in cargo):
        fail("v006 cargo label/tag/provenance contract changed")
    if any(VISUAL_TAG not in _tags(actor) or V006_CORRECTION_TAG in _tags(actor)
           or not str(actor.get_actor_label()).startswith("VIS | ")
           for actor in machinery):
        fail("v006 machinery label/tag/provenance contract changed")

    presentation = [actor for actor in actors if PRESENTATION_PASS_TAG in _tags(actor)]
    cameras = [actor for actor in actors if CAMERA_V006_TAG in _tags(actor)]
    deck = [actor for actor in presentation if actor not in cameras]
    runtime = [actor for actor in actors if _class_path(actor) == PRESENTATION_CLASS]
    corrected = [actor for actor in actors if V006_CORRECTION_TAG in _tags(actor)]
    v005 = [actor for actor in actors if V005_UPGRADE_TAG in _tags(actor)]
    v004 = [actor for actor in actors if V004_POLISH_TAG in _tags(actor)]
    if (len(presentation), len(deck), len(cameras), len(runtime), len(corrected),
            len(v005), len(v004)) != (
                EXPECTED_PRESENTATION_COUNT, EXPECTED_PRESENTATION_DECK_COUNT,
                EXPECTED_CAMERA_COUNT, EXPECTED_RUNTIME_PRESENTATION_COUNT,
                EXPECTED_CORRECTION_TAG_COUNT, EXPECTED_V005_UPGRADE_TAG_COUNT,
                EXPECTED_V004_POLISH_TAG_COUNT,
            ):
        fail("v006 presentation/camera/provenance inventory changed")
    if PRESENTATION_ADAPTER_TAG not in _tags(runtime[0]):
        fail("v006 runtime presentation adapter tag changed")

    plan_by_id = {str(row["id"]): row for row in contract["plan"]["mutations"]}
    actors_by_id: Dict[str, Any] = {}
    for item_id, row in contract["mutations"].items():
        path = str(row["actor_path"])
        if path not in by_path:
            fail("v006 corrected actor is missing: " + item_id)
        actor = by_path[path]
        _validate_mutated_actor(actor, row, plan_by_id[item_id])
        actors_by_id[item_id] = actor
    if {str(actor.get_path_name()) for actor in corrected} != {
            str(row["actor_path"]) for row in contract["mutations"].values()}:
        fail("v006 correction provenance actor-path set changed")

    camera_by_label = {str(actor.get_actor_label()): actor for actor in cameras}
    if (len(camera_by_label) != EXPECTED_CAMERA_COUNT
            or set(camera_by_label) != {
                str(spec["label"]) for spec in CAMERA_SPECS.values()
            }):
        fail("v006 saved camera label set changed")
    route = _route_gap_readback(actors_by_id, contract["plan"])

    correction = contract["module"]
    semantic_groups = {
        "visual_layer_actor_semantic_fingerprints_after_sha256": visuals,
        "machinery_actor_semantic_fingerprints_after_sha256": machinery,
        "cargo_actor_semantic_fingerprints_after_sha256": cargo,
    }
    semantic_hashes: Dict[str, str] = {}
    for field, group in semantic_groups.items():
        value = correction._hash_records(correction._semantic_records(group))
        if value != receipt.get(field):
            fail("loaded v006 preserved visual semantic fingerprint changed: " + field)
        semantic_hashes[field] = value

    source_by_id = {
        str(actor.get_actor_label()).removeprefix("VIS | "): actor
        for actor in machinery
    }
    cargo_by_id = {
        str(actor.get_actor_label()).removeprefix("CARGO | "): actor
        for actor in cargo
    }
    if (SELECTED_SOURCE_IDS - set(source_by_id)
            or SELECTED_CARGO_IDS - set(cargo_by_id)):
        fail("v006 coherent-still visual selection no longer resolves")
    visible = [source_by_id[item_id] for item_id in sorted(SELECTED_SOURCE_IDS)]
    visible += [cargo_by_id[item_id] for item_id in sorted(SELECTED_CARGO_IDS)]
    return {
        "visuals": visuals, "machinery": machinery, "cargo": cargo,
        "visible_visuals": visible, "deck_actors": deck,
        "runtime_actor": runtime[0], "cameras_by_label": camera_by_label,
        "actors_by_path": by_path, "route_readback": route,
        "semantic_hashes": semantic_hashes,
    }


def protected_snapshot(contract: Mapping[str, Any]) -> Dict[str, str]:
    try:
        value = contract["module"].protected_snapshot()
    except Exception as error:
        fail("could not read protected-map snapshot: " + str(error))
    if value != contract["protected"]:
        fail("protected-map snapshot changed after contract preflight")
    return value


def candidate_material_snapshot(contract: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for asset, expected in contract["candidate_material_packages"].items():
        disk = virtual_to_uasset(asset)
        if (not disk.is_file() or disk.stat().st_size != int(expected["bytes"])
                or digest(disk) != expected["sha256"]):
            fail("v006 candidate material changed: " + asset)
        result[asset] = dict(expected)
    return result


def _write_new_receipt(value: Mapping[str, Any]) -> None:
    try:
        with CAPTURE_RECEIPT.open("xb") as handle:
            handle.write(canonical_json_bytes(value))
    except FileExistsError as error:
        raise CaptureGuardError(
            "refusing to overwrite capture receipt: " + str(CAPTURE_RECEIPT)
        ) from error


def validate_capture_records(rows: Any) -> List[Dict[str, Any]]:
    if not isinstance(rows, list) or len(rows) != EXPECTED_CAMERA_COUNT:
        fail("capture did not produce exactly three PNG records")
    result: List[Dict[str, Any]] = []
    for index, item_id in enumerate(("overview", "press_spine", "steam_hero")):
        row = rows[index]
        spec = CAMERA_SPECS[item_id]
        if not isinstance(row, Mapping):
            fail("capture record is not an object: " + item_id)
        expected_path = (OUTPUT_DIR / str(spec["filename"])).resolve()
        try:
            actual_path = Path(str(row.get("path", ""))).resolve()
        except (OSError, ValueError) as error:
            fail("capture path is invalid for {}: {}".format(item_id, error))
        if (row.get("camera_id") != item_id
                or actual_path != expected_path
                or row.get("source_camera_label") != spec["label"]
                or row.get("projection") != "ORTHOGRAPHIC"
                or not _close(
                    (row.get("ortho_width_cm"),), (spec["ortho_width_cm"],)
                )
                or row.get("width") != CAPTURE_WIDTH
                or row.get("height") != CAPTURE_HEIGHT
                or not isinstance(row.get("bytes"), int) or int(row["bytes"]) <= 0):
            fail("saved-camera capture record changed: " + item_id)
        _require_sha(row.get("sha256"), "capture PNG sha256")
        if not expected_path.is_file() or digest(expected_path) != row["sha256"]:
            fail("captured PNG is missing or differs from its record: " + item_id)
        result.append(dict(row))
    return result


def main() -> None:
    ue = _require_unreal()
    map_sha, receipt_sha = required_guard_hashes()
    receipt, contract = load_guarded_install_receipt(map_sha, receipt_sha)
    ensure_output_absent()
    protected_before = protected_snapshot(contract)
    candidate_materials_before = candidate_material_snapshot(contract)
    base_capture = _base_capture_module()
    if base_capture._dirty_packages() != {"content": [], "maps": []}:
        fail("editor has dirty packages before v006 saved-map capture")
    editor_subsystem = ue.get_editor_subsystem(ue.UnrealEditorSubsystem)
    if editor_subsystem is None:
        fail("UnrealEditorSubsystem is unavailable")
    current_world = editor_subsystem.get_editor_world()
    if current_world and str(current_world.get_outermost().get_name()) == TARGET_MAP:
        fail("run from an unrelated clean world; v006 must start unloaded")
    if not ue.EditorLoadingAndSavingUtils.load_map(TARGET_MAP):
        fail("could not load exact v006 saved map")
    world = editor_subsystem.get_editor_world()
    if world is None or str(world.get_outermost().get_name()) != TARGET_MAP:
        fail("v006 target did not become the current editor world")
    if (base_capture._dirty_packages() != {"content": [], "maps": []}
            or digest(TARGET_FILE) != map_sha):
        fail("loading v006 dirtied or changed the saved map")
    actor_subsystem = ue.get_editor_subsystem(ue.EditorActorSubsystem)
    if actor_subsystem is None:
        fail("EditorActorSubsystem is unavailable")
    actors = list(actor_subsystem.get_all_level_actors() or [])
    loaded = validate_loaded_world(world, actors, contract, receipt)

    fingerprint_helper = contract["module"]._v005._actor_fingerprint_record
    before = {
        path: fingerprint_helper(actor)
        for path, actor in sorted(loaded["actors_by_path"].items())
    }
    visibility_before = {
        str(actor.get_path_name()): base_capture._visibility_state(actor)
        for actor in loaded["visuals"]
    }
    visible_paths = {
        str(actor.get_path_name()) for actor in loaded["visible_visuals"]
    }
    residency = base_capture._prepare_texture_residency(loaded["visible_visuals"])
    try:
        for actor in loaded["visuals"]:
            base_capture._set_capture_visibility(
                actor, str(actor.get_path_name()) in visible_paths
            )
        show_only = [
            *loaded["deck_actors"], *loaded["visible_visuals"],
            loaded["runtime_actor"],
        ]
        captures = validate_capture_records(base_capture._capture_saved_cameras(
            world, actor_subsystem, loaded["cameras_by_label"], show_only
        ))
    finally:
        for actor in loaded["visuals"]:
            base_capture._restore_visibility(
                actor, visibility_before[str(actor.get_path_name())]
            )

    actors_after = list(actor_subsystem.get_all_level_actors() or [])
    if len(actors_after) != EXPECTED_ACTOR_COUNT:
        fail("v006 actor count changed during transient capture")
    after = {
        str(actor.get_path_name()): fingerprint_helper(actor)
        for actor in actors_after
    }
    if after != before:
        fail("a saved actor changed during v006 transient capture")
    if {
        str(actor.get_path_name()): base_capture._visibility_state(actor)
        for actor in loaded["visuals"]
    } != visibility_before:
        fail("visual visibility state was not restored after v006 capture")

    dirty_after = base_capture._dirty_packages()
    if dirty_after not in (
        {"content": [], "maps": []},
        {"content": [], "maps": [TARGET_MAP]},
    ):
        fail("transient v006 capture dirtied a package outside the target map")
    if digest(TARGET_FILE) != map_sha or digest(INSTALL_RECEIPT) != receipt_sha:
        fail("v006 target map or install receipt bytes changed during capture")
    protected_after = protected_snapshot(contract)
    if protected_after != protected_before:
        fail("a protected map changed during v006 saved-map capture")
    candidate_materials_after = candidate_material_snapshot(contract)
    if candidate_materials_after != candidate_materials_before:
        fail("a candidate material package changed during v006 capture")
    if contract["module"].validate_material_locks() != contract["reused_materials"]:
        fail("a reused presentation material changed during v006 capture")

    fingerprint_sha = hashlib.sha256(canonical_json_bytes(after)).hexdigest()
    capture_receipt = {
        "schema": CAPTURE_SCHEMA,
        "status": CAPTURE_STATUS,
        "evidence_scope": "SAVED_MAP_VISUAL_EVIDENCE_ONLY",
        "explicitly_not_validated": [
            "PIE_LIFECYCLE", "RUNTIME_SIMULATION", "PACKAGED_BUILD",
            "PERFORMANCE", "STEAM_VISUAL_QUALITY_APPROVAL",
        ],
        "target_map": TARGET_MAP,
        "target_map_sha256_before": map_sha,
        "target_map_sha256_after": digest(TARGET_FILE),
        "install_receipt": INSTALL_RECEIPT.as_posix(),
        "install_receipt_sha256": receipt_sha,
        "installer_contract_sha256": INSTALLER_SHA256,
        "scene_capture_helper_sha256": BASE_CAPTURE_SHA256,
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "candidate_material_packages_before": candidate_materials_before,
        "candidate_material_packages_after": candidate_materials_after,
        "actor_count": EXPECTED_ACTOR_COUNT,
        "visual_layer_count": EXPECTED_VISUAL_COUNT,
        "machinery_visual_layer_count": EXPECTED_MACHINERY_COUNT,
        "cargo_layer_count": EXPECTED_CARGO_COUNT,
        "presentation_actor_count": EXPECTED_PRESENTATION_COUNT,
        "presentation_deck_actor_count": EXPECTED_PRESENTATION_DECK_COUNT,
        "saved_camera_count": EXPECTED_CAMERA_COUNT,
        "v006_correction_tagged_actor_count": EXPECTED_CORRECTION_TAG_COUNT,
        "continuous_station_port_count": loaded["route_readback"]["station_port_count"],
        "continuous_station_port_gaps_cm": loaded["route_readback"]["station_connector_gaps_cm"],
        "continuous_station_port_max_gap_cm": loaded["route_readback"]["station_connector_max_gap_cm"],
        "loaded_visual_semantic_fingerprints_sha256": loaded["semantic_hashes"],
        "selected_source_visual_ids": sorted(SELECTED_SOURCE_IDS),
        "selected_cargo_visual_ids": sorted(SELECTED_CARGO_IDS),
        "selected_visual_count": len(visible_paths),
        "resident_material_count": residency["materials"],
        "resident_sprite_texture_count": residency["textures"],
        "loaded_actor_fingerprint_sha256": fingerprint_sha,
        "loaded_actor_fingerprint_unchanged": True,
        "visual_visibility_state_restored": True,
        "presentation_style": receipt["presentation_style"],
        "saved_camera_contract": {
            item_id: {
                "label": spec["label"],
                "location_cm": list(spec["location_cm"]),
                "rotation_deg_pitch_yaw_roll": list(CAMERA_ROTATION),
                "ortho_width_cm": spec["ortho_width_cm"],
                "role_tag": spec["role_tag"],
            }
            for item_id, spec in CAMERA_SPECS.items()
        },
        "captures": captures,
        "capture_resolution": [CAPTURE_WIDTH, CAPTURE_HEIGHT],
        "capture_method": (
            "TRANSIENT_NATIVE_SCENECAPTURE2D_FROM_EXACTLY_THREE_SAVED_V006_"
            "ORTHOGRAPHIC_CAMERAS_SHOW_ONLY_SAVED_PRESENTATION_AND_FROZEN_"
            "COHERENT_MACHINERY_CARGO_VISUAL_STATE"
        ),
        "dirty_packages_after_capture": dirty_after,
        "map_load_calls": 1,
        "map_save_calls": 0,
        "content_save_calls": 0,
        "content_import_calls": 0,
        "content_asset_create_calls": 0,
        "saved_actor_layout_mutated": False,
        "saved_actor_material_assignment_mutated": False,
        "saved_actor_collision_mutated": False,
        "project_content_written": False,
        "runtime_simulation_validated": False,
        "pie_validated": False,
        "packaged_build_validated": False,
        "steam_visual_quality_human_approved": False,
    }
    _write_new_receipt(capture_receipt)
    ue.log(
        "PRESSSHOP_2126_OVERHEAD_PRESENTATION_V006_SAVED_MAP_CAPTURE_PASS: "
        + OUTPUT_DIR.as_posix()
    )
    ue.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
