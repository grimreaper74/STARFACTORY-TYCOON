"""Guarded read-only saved-map capture for Press Shop 2126 v005.

This lane consumes only the completed v005 map and its canonical install
receipt.  Their two independent SHA-256 digests are required through the
environment.  The installer itself remains the geometry/layout contract: its
frozen plan is rebuilt offline and every one of the 61 mutations, 55 new
collision-inert native boxes, two new unlit materials, 302 actors, 146 visual
layers, 26 cargo layers, and three authored cameras is checked before capture.

Three transient native SceneCapture2D actors export 1920x1080 PNGs beneath
Saved.  Saved actors are never moved, scaled, relabelled, rematerialled,
created, deleted, or saved.  Visual-layer visibility is changed only for the
capture and restored before the append-only receipt is written.  A PASS is
saved-map visual evidence, not PIE, cook, package, performance, or Steam
approval evidence.

Run from an unrelated clean map (normally /Engine/Maps/Entry) with a rendering
RHI.  Do not use -NullRHI.
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

try:  # Importable by ordinary CPython contract tests.
    import unreal  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - outside Unreal only.
    unreal = None  # type: ignore


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
INSTALLER = PROJECT / "Tools/install_pressshop_2126_overhead_presentation_upgrade_v001.py"
INSTALLER_SHA256 = "6478f814b39628c2b6629e06673efad0cd0aede185ed737409420a6680f243c2"
V004_CAPTURE = PROJECT / "Tools/capture_pressshop_2126_overhead_presentation_v004.py"

TARGET_MAP = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v005/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v005"
)
TARGET_FILE = (
    PROJECT / "Content/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v005/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v005.umap"
)
INSTALL_RECEIPT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadPresentation_v005/"
    "install_receipt_v001.json"
)
OUTPUT_DIR = (
    PROJECT / "Saved/PressShop2126/"
    "OverheadPresentation_v005_SavedMapCapture_v001"
)
CAPTURE_RECEIPT = OUTPUT_DIR / "saved_map_capture_receipt_v001.json"

MAP_SHA_ENV = "LB_PRESSSHOP_V005_TARGET_MAP_SHA256"
RECEIPT_SHA_ENV = "LB_PRESSSHOP_V005_INSTALL_RECEIPT_SHA256"

INSTALL_SCHEMA = "cairnwell.press_shop.overhead_presentation_upgrade_install_receipt.v001"
INSTALL_STATUS = (
    "PASS_CANDIDATE_PRESENTATION_UPGRADE_APPLIED__"
    "V004_FINGERPRINTS_PRESERVED__VISUAL_CAPTURE_AND_PIE_PENDING"
)
CAPTURE_SCHEMA = (
    "cairnwell.press_shop.overhead_presentation_v005_saved_map_capture_receipt.v001"
)
CAPTURE_STATUS = (
    "PASS_IN_ENGINE_V005_SAVED_MAP_PRESENTATION_CAPTURE__"
    "PIE_LIFECYCLE_AND_STEAM_APPROVAL_PENDING"
)

EXPECTED_GAME_MODE = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
EXPECTED_ACTOR_COUNT = 302
EXPECTED_VISUAL_COUNT = 146
EXPECTED_BASE_VISUAL_COUNT = 120
EXPECTED_CARGO_COUNT = 26
EXPECTED_PRESENTATION_COUNT = 140
EXPECTED_PRESENTATION_DECK_COUNT = 137
EXPECTED_CAMERA_COUNT = 3
EXPECTED_RUNTIME_PRESENTATION_COUNT = 1
EXPECTED_MUTATION_COUNT = 61
EXPECTED_NEW_BOX_COUNT = 55
EXPECTED_UPGRADE_TAG_COUNT = 116
EXPECTED_V004_POLISH_TAG_COUNT = 41
EXPECTED_UNCHANGED_PRESENTATION_COUNT = 24
EXPECTED_MUTATED_PRIMITIVE_COUNT = 58

CAPTURE_WIDTH = 1920
CAPTURE_HEIGHT = 1080
NUMERIC_TOLERANCE = 0.001

VISUAL_CLASS = "/Script/LineBossCarFactory.LBPressShopOverheadVisualLayerActor"
PRESENTATION_CLASS = "/Script/LineBossCarFactory.LBPressShopOverheadPresentationActor"
STATIC_MESH_CLASS = "/Script/Engine.StaticMeshActor"
TEXT_RENDER_CLASS = "/Script/Engine.TextRenderActor"
CAMERA_CLASS = "/Script/Engine.CameraActor"

VISUAL_TAG = "LB.PressShop.Overhead.VisualLayer.v001"
PRESENTATION_ADAPTER_TAG = "LB.PressShop.OverheadPresentation.v001"
PRESENTATION_PASS_TAG = "LB.PressShop.OverheadDeckPresentation.v002"
CARGO_MAP_TAG = "LB.PressShop.OverheadCargoMap.v003"
CARGO_SOURCE_TAG = "LB.PressShop.CargoContinuity.v001"
V004_POLISH_TAG = "LB.PressShop.OverheadPresentationPolish.v004"
V005_UPGRADE_TAG = "LB.PressShop.OverheadPresentationUpgrade.v005"
CAMERA_V005_TAG = "LB.PressShop.OverheadDeck.Camera.v005"
VISUAL_ONLY_TAG = "LB.Environment.VisualOnly"
NOT_WIP_TAG = "LB.NotProcessWIP"
CUBE_ASSET = "/Engine/BasicShapes/Cube"

COLLISION_CHANNEL_NAMES = (
    "ECC_WORLD_STATIC", "ECC_WORLD_DYNAMIC", "ECC_PAWN", "ECC_VISIBILITY",
    "ECC_CAMERA", "ECC_PHYSICS_BODY", "ECC_VEHICLE", "ECC_DESTRUCTIBLE",
)

CAMERA_SPECS: Mapping[str, Mapping[str, Any]] = {
    "overview": {
        "label": "CAM | Press Shop 2126 | complete roofless flow overview v005",
        "location_cm": (-7730.645880159617, 8840.218280826943, 21712.544),
        "ortho_width_cm": 17200.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.Overview.v005",
        "filename": "PressShop2126_PresentationOverview_1920x1080_v005.png",
    },
    "press_spine": {
        "label": "CAM | Press Shop 2126 | connected production spine v005",
        "location_cm": (-8450.0, 11100.0, 21712.544),
        "ortho_width_cm": 10800.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.PressSpine.v005",
        "filename": "PressShop2126_PresentationSpine_1920x1080_v005.png",
    },
    "steam_hero": {
        "label": "CAM | Press Shop 2126 | S03-S06 grouped Steam hero v005",
        "location_cm": (-8990.75, 11087.5, 21712.544),
        "ortho_width_cm": 6000.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.SteamHero.v005",
        "filename": "PressShop2126_PresentationPressHero_1920x1080_v005.png",
    },
}

# This is the same coherent still state as v004.  The v005 installer proves
# all machinery/cargo fingerprints are byte-for-byte unchanged.
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
    """The v005 read-only capture contract rejected the current state."""


def fail(message: str) -> None:
    raise CaptureGuardError(
        "PRESSSHOP_2126_OVERHEAD_PRESENTATION_V005_CAPTURE_FAIL: " + message
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
    if (not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None
            or value == "0" * 64):
        fail(context + " must be an explicit lower-case SHA-256")
    return value


def required_guard_hashes(environ: Mapping[str, str] | None = None) -> Tuple[str, str]:
    values = os.environ if environ is None else environ
    return (
        _require_sha(values.get(MAP_SHA_ENV), MAP_SHA_ENV),
        _require_sha(values.get(RECEIPT_SHA_ENV), RECEIPT_SHA_ENV),
    )


def _load_module(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        fail("could not import frozen contract module: " + str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _installer_contract() -> Dict[str, Any]:
    if not INSTALLER.is_file() or digest(INSTALLER) != INSTALLER_SHA256:
        fail("v005 installer contract file is missing or changed")
    upgrade = _load_module(INSTALLER, "pressshop_v005_installer_capture_contract")
    exact_constants = {
        "TARGET_MAP": TARGET_MAP,
        "EXPECTED_FINAL_ACTOR_COUNT": EXPECTED_ACTOR_COUNT,
        "EXPECTED_COMBINED_VISUAL_LAYER_COUNT": EXPECTED_VISUAL_COUNT,
        "EXPECTED_BASE_VISUAL_LAYER_COUNT": EXPECTED_BASE_VISUAL_COUNT,
        "EXPECTED_CARGO_LAYER_COUNT": EXPECTED_CARGO_COUNT,
        "EXPECTED_EXISTING_MUTATION_COUNT": EXPECTED_MUTATION_COUNT,
        "EXPECTED_NEW_BOX_COUNT": EXPECTED_NEW_BOX_COUNT,
    }
    for name, expected in exact_constants.items():
        if getattr(upgrade, name, None) != expected:
            fail("installer contract constant changed: " + name)
    try:
        v002 = upgrade.validate_v002_receipt()
        v004 = upgrade.validate_source_receipt()
        plan = upgrade.build_upgrade_plan(v002, v004)
        validation = upgrade.validate_upgrade_plan(plan)
        protected = upgrade.protected_snapshot()
        materials = upgrade.validate_reused_material_locks()
    except Exception as error:
        fail("installer contract could not be rebuilt: " + str(error))
    if (
        len(plan["mutations"]) != EXPECTED_MUTATION_COUNT
        or len(plan["additions"]) != EXPECTED_NEW_BOX_COUNT
        or validation.get("final_actor_count") != EXPECTED_ACTOR_COUNT
        or validation.get("station_port_count") != 12
        or validation.get("station_connector_max_gap_cm") != 0.0
        or validation.get("new_materials") != [
            {
                "asset": str(row["asset"]),
                "srgb_hex": str(row["srgb_hex"]),
                "linear_rgb": list(upgrade.srgb_hex_to_linear(str(row["srgb_hex"]))),
                "shading_model": "UNLIT",
            }
            for row in upgrade.NEW_MATERIAL_SPECS
        ]
    ):
        fail("rebuilt installer plan no longer matches the accepted v005 contract")
    for item_id, spec in CAMERA_SPECS.items():
        target = upgrade.CAMERA_TARGETS.get(item_id)
        if (
            not isinstance(target, Mapping)
            or target.get("label") != spec["label"]
            or not _close(target.get("location_cm", ()), spec["location_cm"])
            or not _close((target.get("ortho_width_cm"),), (spec["ortho_width_cm"],))
        ):
            fail("authored v005 camera contract changed: " + item_id)
    return {
        "module": upgrade, "plan": plan, "validation": validation,
        "protected": protected, "reused_materials": materials,
    }


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
    result = (PROJECT / "Content" / (asset_path.removeprefix("/Game/") + ".uasset")).resolve()
    if not result.is_relative_to((PROJECT / "Content").resolve()):
        fail("asset path escapes Content: " + asset_path)
    return result


def _index(rows: Any, context: str, count: int) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(rows, list) or len(rows) != count:
        fail(context + " count changed")
    result: Dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("id"), str):
            fail(context + " contains an invalid record")
        if row["id"] in result:
            fail(context + " contains duplicate id: " + str(row["id"]))
        result[str(row["id"])] = row
    return result


def _valid_no_collision_receipt(value: Any) -> bool:
    if not isinstance(value, Mapping):
        return False
    return (
        value.get("actor_collision_enabled") is False
        and "NO_COLLISION" in str(value.get("component_collision_enabled", "")).upper()
        and value.get("generate_overlap_events") is False
        and value.get("can_ever_affect_navigation") is False
        and value.get("ignored_channels") == list(COLLISION_CHANNEL_NAMES)
        and value.get("profile_acceptance") in {
            "NativeNoCollisionWithIgnoreAll", "CustomWithNoCollisionAndIgnoreAll"
        }
    )


def _validate_mutation_receipt(row: Mapping[str, Any], mutation: Mapping[str, Any]) -> None:
    item_id, kind, target = str(mutation["id"]), str(mutation["kind"]), mutation["target"]
    actor_path = str(row.get("actor_path", ""))
    if (
        row.get("id") != item_id or row.get("kind") != kind
        or not actor_path.startswith(TARGET_MAP + ".")
        or row.get("source_label") != mutation["source"]["label"]
        or row.get("target_label") != target["label"]
        or not _close(row.get("target_location_cm", ()), target["location_cm"])
    ):
        fail("v005 mutation receipt changed: " + item_id)
    expected_rotation = ([0.0, float(target["yaw_deg"]), 0.0]
                         if kind == "box" else target["rotation_deg_pitch_yaw_roll"])
    if not _rotation_close(row.get("target_rotation_deg_pitch_yaw_roll", ()), expected_rotation):
        fail("v005 mutation rotation changed: " + item_id)
    if kind == "box":
        exact_role = "LB.PressShop.OverheadDeck.Role." + str(target["role"])
        if (
            not _close(row.get("target_dimensions_cm", ()), target["dimensions_cm"])
            or row.get("target_material") != _asset_path(target["material"])
            or row.get("exact_role_tag") != exact_role
            or row.get("collision") != "NoCollision"
            or not _valid_no_collision_receipt(row.get("collision_readback"))
        ):
            fail("v005 box mutation receipt changed: " + item_id)
    elif kind == "text":
        if (
            not _close((row.get("target_world_size_cm"),), (target["world_size_cm"],))
            or row.get("target_colour_rgba") != target["colour_rgba"]
            or row.get("collision") != "NoCollision"
            or not _valid_no_collision_receipt(row.get("collision_readback"))
        ):
            fail("v005 text mutation receipt changed: " + item_id)
    elif kind == "camera":
        if (
            not _close((row.get("target_ortho_width_cm"),), (target["ortho_width_cm"],))
            or row.get("collision") is not None or row.get("collision_readback") is not None
        ):
            fail("v005 camera mutation receipt changed: " + item_id)
    else:
        fail("unknown v005 mutation kind: " + kind)


def _validate_addition_receipt(row: Mapping[str, Any], spec: Mapping[str, Any]) -> None:
    item_id = str(spec["id"])
    actor_path = str(row.get("actor_path", ""))
    for key in ("id", "kind", "label", "role", "material", "location_cm",
                "dimensions_cm", "yaw_deg"):
        expected = spec[key]
        actual = row.get(key)
        if key in {"location_cm", "dimensions_cm"}:
            if not _close(actual or (), expected):
                fail("v005 addition receipt changed: {}:{}".format(item_id, key))
        elif actual != expected:
            fail("v005 addition receipt changed: {}:{}".format(item_id, key))
    if (
        not actor_path.startswith(TARGET_MAP + ".")
        or row.get("mesh") != CUBE_ASSET
        or row.get("collision") != "NoCollision"
        or not _valid_no_collision_receipt(row.get("collision_readback"))
        or row.get("cast_shadow") is not False
        or row.get("visual_only") is not True
        or row.get("process_wip") is not False
        or row.get("cargo_geometry") is not False
        or row.get("machine_geometry") is not False
        or row.get("exact_role_tag") != "LB.PressShop.OverheadDeck.Role." + str(spec["role"])
    ):
        fail("v005 native-box addition contract changed: " + item_id)


def validate_install_receipt(
    receipt: Mapping[str, Any], expected_map_sha: str, actual_map_bytes: int,
    contract: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    contract = _installer_contract() if contract is None else contract
    upgrade, plan, validation = contract["module"], contract["plan"], contract["validation"]
    if receipt.get("schema") != INSTALL_SCHEMA or receipt.get("status") != INSTALL_STATUS:
        fail("v005 install receipt schema or status changed")
    exact = {
        "candidate_only": True, "target_map": TARGET_MAP,
        "target_map_sha256": expected_map_sha, "target_map_bytes": actual_map_bytes,
        "source_actor_count": 247, "final_actor_count": EXPECTED_ACTOR_COUNT,
        "source_presentation_actor_count": 85,
        "final_presentation_actor_count": EXPECTED_PRESENTATION_COUNT,
        "preserved_nonpresentation_actor_count": 162,
        "unchanged_presentation_actor_count": EXPECTED_UNCHANGED_PRESENTATION_COUNT,
        "combined_visual_layer_count": EXPECTED_VISUAL_COUNT,
        "machinery_visual_layer_count": EXPECTED_BASE_VISUAL_COUNT,
        "cargo_layer_count": EXPECTED_CARGO_COUNT,
        "cargo_actor_mutated_count": 0, "machinery_actor_mutated_count": 0,
        "source_actor_removed_count": 0, "source_actor_created_count": EXPECTED_NEW_BOX_COUNT,
        "mutated_existing_presentation_actor_count": EXPECTED_MUTATION_COUNT,
        "created_presentation_box_count": EXPECTED_NEW_BOX_COUNT,
        "created_collision_readback_count": EXPECTED_NEW_BOX_COUNT,
        "collision_enabled_on_created_presentation": False,
        "collision_enabled_on_mutated_presentation_primitives": False,
        "mutated_primitive_collision_readback_count": EXPECTED_MUTATED_PRIMITIVE_COUNT,
        "source_map_mutated": False, "protected_authority_map_mutated": False,
        "native_cpp_modified": False, "roof_created": False,
        "new_machinery_geometry": 0, "new_cargo_geometry": 0,
        "empty_shuttle_visual_geometry": 9, "machine_or_cargo_transform_mutations": 0,
        "runtime_validated": False, "pie_validated": False, "cook_validated": False,
        "packaged_build_validated": False, "visual_capture_validated": False,
        "steam_capture_validated": False, "steam_visual_quality_human_approved": False,
        "dirty_packages_after_save": {"content": [], "maps": []},
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("v005 install receipt field changed: " + key)
    if receipt.get("game_mode_before") != EXPECTED_GAME_MODE or receipt.get("game_mode_after") != EXPECTED_GAME_MODE:
        fail("v005 install receipt GameMode changed")
    if receipt.get("plan_validation") != validation:
        fail("v005 install receipt no longer embeds the exact installer plan validation")
    if receipt.get("protected_hashes_before") != contract["protected"] or receipt.get("protected_hashes_after") != contract["protected"]:
        fail("v005 install receipt protected-hash contract changed")
    if receipt.get("reused_presentation_material_hashes_before") != contract["reused_materials"] or receipt.get("reused_presentation_material_hashes_after") != contract["reused_materials"]:
        fail("v005 reused-material lock changed")
    for before_key, after_key in (
        ("preserved_nonpresentation_actor_fingerprints_before_sha256", "preserved_nonpresentation_actor_fingerprints_after_sha256"),
        ("unchanged_presentation_actor_fingerprints_before_sha256", "unchanged_presentation_actor_fingerprints_after_sha256"),
        ("visual_layer_actor_fingerprints_before_sha256", "visual_layer_actor_fingerprints_after_sha256"),
        ("machinery_actor_fingerprints_before_sha256", "machinery_actor_fingerprints_after_sha256"),
        ("cargo_actor_fingerprints_before_sha256", "cargo_actor_fingerprints_after_sha256"),
    ):
        if receipt.get(before_key) != receipt.get(after_key):
            fail("v005 preserved fingerprint pair changed: " + before_key)
        _require_sha(receipt.get(before_key), before_key)

    mutations = _index(receipt.get("presentation_mutations"), "v005 mutations", EXPECTED_MUTATION_COUNT)
    additions = _index(receipt.get("created_presentation_boxes"), "v005 additions", EXPECTED_NEW_BOX_COUNT)
    if list(mutations) != [str(row["id"]) for row in plan["mutations"]] or list(additions) != [str(row["id"]) for row in plan["additions"]]:
        fail("v005 mutation/addition ordering or id inventory changed")
    for mutation in plan["mutations"]:
        _validate_mutation_receipt(mutations[str(mutation["id"])], mutation)
    for spec in plan["additions"]:
        _validate_addition_receipt(additions[str(spec["id"])], spec)
    all_paths = [str(row["actor_path"]) for row in [*mutations.values(), *additions.values()]]
    if len(all_paths) != len(set(all_paths)):
        fail("v005 receipt actor paths are duplicated")
    if receipt.get("created_presentation_box_role_counts") != validation["addition_role_counts"]:
        fail("v005 native-box role counts changed")

    style = {
        "full_deck_material": upgrade.SLATE_MATERIAL, "full_deck_srgb_hex": "#36534F",
        "floor_band_material": upgrade.FLOOR_BAND_MATERIAL, "floor_band_srgb_hex": "#294A46",
        "route_bed_material": upgrade.ROUTE_TEAL_MATERIAL, "route_bed_srgb_hex": "#3B8177",
        "station_zone_material": upgrade.ZONE_MATERIAL, "station_zone_srgb_hex": "#91AA9C",
        "route_rail_and_port_material": upgrade.CREAM_MATERIAL,
        "label_plaque_material": upgrade.CHARCOAL_MATERIAL,
        "new_material_shading_model": "UNLIT", "external_texture_assets": [],
        "lights_created": 0, "exposure_mutated": False,
    }
    if receipt.get("presentation_style") != style:
        fail("v005 presentation-style contract changed")
    materials = _index(receipt.get("created_materials"), "v005 created materials", 2)
    for spec in upgrade.NEW_MATERIAL_SPECS:
        row = materials[str(spec["id"])]
        if (
            row.get("asset") != spec["asset"] or row.get("srgb_hex") != spec["srgb_hex"]
            or row.get("shading_model") != "UNLIT" or row.get("material_recompile_passes") != 2
            or not isinstance(row.get("bytes"), int) or int(row["bytes"]) <= 0
        ):
            fail("v005 created-material contract changed: " + str(spec["id"]))
        _require_sha(row.get("sha256"), "v005 material sha256")
    return {"mutations": mutations, "additions": additions, "materials": materials,
            "plan": plan, "validation": validation, "protected": contract["protected"]}


def load_guarded_install_receipt(expected_map_sha: str, expected_receipt_sha: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not TARGET_FILE.is_file() or not INSTALL_RECEIPT.is_file():
        fail("v005 map or install receipt is missing")
    if digest(TARGET_FILE) != expected_map_sha:
        fail("v005 map hash differs from supplied final hash")
    if digest(INSTALL_RECEIPT) != expected_receipt_sha:
        fail("v005 receipt hash differs from supplied final hash")
    payload = INSTALL_RECEIPT.read_bytes()
    try:
        receipt = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail("v005 install receipt is not valid UTF-8 JSON: " + str(error))
    if not isinstance(receipt, dict) or payload != canonical_json_bytes(receipt):
        fail("v005 install receipt is not canonical JSON")
    contract = validate_install_receipt(receipt, expected_map_sha, TARGET_FILE.stat().st_size)
    for row in contract["materials"].values():
        disk = virtual_to_uasset(str(row["asset"]))
        if not disk.is_file() or disk.stat().st_size != int(row["bytes"]) or digest(disk) != row["sha256"]:
            fail("v005 material package differs from its receipt: " + str(row["id"]))
    return receipt, contract


def ensure_output_absent(path: Path = OUTPUT_DIR) -> None:
    if path.exists():
        fail("refusing to overwrite or merge capture evidence: " + str(path))


def _require_unreal() -> Any:
    if unreal is None:
        fail("this capture must run inside Unreal Editor Python")
    return unreal


def _base_capture_module() -> Any:
    base = _load_module(V004_CAPTURE, "pressshop_v004_capture_runtime_helpers")
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
        "location_cm": [float(value.translation.x), float(value.translation.y), float(value.translation.z)],
        "rotation_deg_pitch_yaw_roll": [float(rotation.pitch), float(rotation.yaw), float(rotation.roll)],
        "scale3d": [float(value.scale3d.x), float(value.scale3d.y), float(value.scale3d.z)],
    }


def _safe_property(value: Any, names: Sequence[str]) -> Any:
    for name in names:
        try:
            return value.get_editor_property(name)
        except Exception:
            pass
    return None


def _colour_rgba(component: Any) -> List[int]:
    colour = component.get_editor_property("text_render_color")
    return [int(colour.r), int(colour.g), int(colour.b), int(colour.a)]


def _fingerprint(actor: Any) -> Dict[str, Any]:
    row: Dict[str, Any] = {
        "path": str(actor.get_path_name()), "label": str(actor.get_actor_label()),
        "class_path": _class_path(actor), "tags": sorted(_tags(actor)),
        "actor_collision_enabled": bool(actor.get_actor_enable_collision()), **_transform(actor),
    }
    component = _safe_property(actor, ("static_mesh_component",))
    if component is not None:
        row["static_mesh_component"] = {
            "mesh": _asset_path(_safe_property(component, ("static_mesh",))),
            "materials": [_asset_path(component.get_material(i)) for i in range(int(component.get_num_materials()))],
            "cast_shadow": bool(component.get_editor_property("cast_shadow")),
            "collision_enabled": str(component.get_collision_enabled()),
            "collision_profile": str(component.get_collision_profile_name()),
            "generate_overlap_events": bool(component.get_editor_property("generate_overlap_events")),
            "can_ever_affect_navigation": bool(component.get_editor_property("can_ever_affect_navigation")),
        }
    text = _safe_property(actor, ("text_render",))
    if text is not None:
        row["text_render"] = {
            "text": str(text.get_editor_property("text")),
            "world_size_cm": float(text.get_editor_property("world_size")),
            "colour_rgba": _colour_rgba(text),
            "cast_shadow": bool(text.get_editor_property("cast_shadow")),
            "collision_enabled": str(text.get_collision_enabled()),
        }
    camera = _safe_property(actor, ("camera_component",))
    if camera is not None:
        row["camera"] = {
            "projection": str(camera.get_editor_property("projection_mode")),
            "ortho_width_cm": float(camera.get_editor_property("ortho_width")),
            "aspect_ratio": float(camera.get_editor_property("aspect_ratio")),
            "constrain_aspect_ratio": bool(camera.get_editor_property("constrain_aspect_ratio")),
        }
    return row


def _validate_no_collision(actor: Any, component: Any, item_id: str) -> None:
    ue = _require_unreal()
    if bool(actor.get_actor_enable_collision()) or "NO_COLLISION" not in str(component.get_collision_enabled()).upper():
        fail("v005 presentation primitive retained collision: " + item_id)
    if bool(component.get_editor_property("generate_overlap_events")) or bool(component.get_editor_property("can_ever_affect_navigation")):
        fail("v005 presentation primitive retained overlap/navigation: " + item_id)
    for channel_name in COLLISION_CHANNEL_NAMES:
        response = str(component.get_collision_response_to_channel(getattr(ue.CollisionChannel, channel_name)))
        if "ECR_IGNORE" not in response.upper():
            fail("v005 presentation primitive collision channel changed: " + item_id)


def _validate_mutated_actor(actor: Any, row: Mapping[str, Any], mutation: Mapping[str, Any]) -> None:
    item_id, kind, target = str(mutation["id"]), str(mutation["kind"]), mutation["target"]
    transform, tags = _transform(actor), _tags(actor)
    if str(actor.get_path_name()) != row["actor_path"] or str(actor.get_actor_label()) != target["label"] or V005_UPGRADE_TAG not in tags:
        fail("loaded v005 mutation identity changed: " + item_id)
    if not _close(transform["location_cm"], target["location_cm"]):
        fail("loaded v005 mutation location changed: " + item_id)
    if kind == "box":
        component = actor.get_editor_property("static_mesh_component")
        expected_rotation = [0.0, float(target["yaw_deg"]), 0.0]
        role_tags = sorted(tag for tag in tags if tag.startswith("LB.PressShop.OverheadDeck.Role."))
        if (
            _class_path(actor) != STATIC_MESH_CLASS
            or not _rotation_close(transform["rotation_deg_pitch_yaw_roll"], expected_rotation)
            or not _close(transform["scale3d"], [float(v)/100.0 for v in target["dimensions_cm"]])
            or _asset_path(component.get_material(0)) != _asset_path(target["material"])
            or role_tags != ["LB.PressShop.OverheadDeck.Role." + str(target["role"])]
            or bool(component.get_editor_property("cast_shadow"))
        ):
            fail("loaded v005 box mutation changed: " + item_id)
        _validate_no_collision(actor, component, item_id)
    elif kind == "text":
        component = actor.get_editor_property("text_render")
        if (
            _class_path(actor) != TEXT_RENDER_CLASS
            or not _rotation_close(transform["rotation_deg_pitch_yaw_roll"], target["rotation_deg_pitch_yaw_roll"])
            or str(component.get_editor_property("text")) != str(target["text"])
            or not _close((component.get_editor_property("world_size"),), (target["world_size_cm"],))
            or _colour_rgba(component) != [int(v) for v in target["colour_rgba"]]
            or bool(component.get_editor_property("cast_shadow"))
        ):
            fail("loaded v005 text mutation changed: " + item_id)
        _validate_no_collision(actor, component, item_id)
    elif kind == "camera":
        component = actor.get_editor_property("camera_component")
        if (
            _class_path(actor) != CAMERA_CLASS
            or not _rotation_close(transform["rotation_deg_pitch_yaw_roll"], target["rotation_deg_pitch_yaw_roll"])
            or "ORTHOGRAPHIC" not in str(component.get_editor_property("projection_mode")).upper()
            or not _close((component.get_editor_property("ortho_width"),), (target["ortho_width_cm"],))
            or not _close((component.get_editor_property("aspect_ratio"),), (16.0/9.0,))
            or not bool(component.get_editor_property("constrain_aspect_ratio"))
            or CAMERA_V005_TAG not in tags or target["role_tag"] not in tags
        ):
            fail("loaded v005 camera mutation changed: " + item_id)


def _validate_added_actor(actor: Any, row: Mapping[str, Any], spec: Mapping[str, Any]) -> None:
    item_id, transform, tags = str(spec["id"]), _transform(actor), _tags(actor)
    component = actor.get_editor_property("static_mesh_component")
    role_tag = "LB.PressShop.OverheadDeck.Role." + str(spec["role"])
    if (
        str(actor.get_path_name()) != row["actor_path"] or _class_path(actor) != STATIC_MESH_CLASS
        or str(actor.get_actor_label()) != spec["label"]
        or not {PRESENTATION_PASS_TAG, VISUAL_ONLY_TAG, NOT_WIP_TAG, V005_UPGRADE_TAG, role_tag} <= tags
        or CARGO_MAP_TAG in tags or CARGO_SOURCE_TAG in tags
        or _asset_path(component.get_editor_property("static_mesh")) != CUBE_ASSET
        or _asset_path(component.get_material(0)) != _asset_path(spec["material"])
        or not _close(transform["location_cm"], spec["location_cm"])
        or not _rotation_close(transform["rotation_deg_pitch_yaw_roll"], [0.0, float(spec["yaw_deg"]), 0.0])
        or not _close(transform["scale3d"], [float(v)/100.0 for v in spec["dimensions_cm"]])
        or bool(component.get_editor_property("cast_shadow"))
    ):
        fail("loaded v005 native-box addition changed: " + item_id)
    _validate_no_collision(actor, component, item_id)


def validate_loaded_world(world: Any, actors: Sequence[Any], contract: Mapping[str, Any]) -> Dict[str, Any]:
    if str(world.get_outermost().get_name()) != TARGET_MAP:
        fail("exact v005 map is not the current editor world")
    game_mode = _asset_path(world.get_world_settings().get_editor_property("default_game_mode"))
    if game_mode != EXPECTED_GAME_MODE or len(actors) != EXPECTED_ACTOR_COUNT:
        fail("v005 loaded world GameMode or actor count changed")
    by_path = {str(actor.get_path_name()): actor for actor in actors}
    if len(by_path) != len(actors):
        fail("v005 loaded actor paths are duplicated")
    visuals = [actor for actor in actors if _class_path(actor) == VISUAL_CLASS]
    cargo = [actor for actor in visuals if CARGO_MAP_TAG in _tags(actor)]
    base = [actor for actor in visuals if CARGO_MAP_TAG not in _tags(actor)]
    if (len(visuals), len(base), len(cargo)) != (EXPECTED_VISUAL_COUNT, EXPECTED_BASE_VISUAL_COUNT, EXPECTED_CARGO_COUNT):
        fail("v005 loaded visual/cargo inventory changed")
    if any(VISUAL_TAG not in _tags(actor) or CARGO_SOURCE_TAG not in _tags(actor)
           or not str(actor.get_actor_label()).startswith("CARGO | ") for actor in cargo):
        fail("v005 cargo tag or label contract changed")
    if any(VISUAL_TAG not in _tags(actor) or not str(actor.get_actor_label()).startswith("VIS | ") for actor in base):
        fail("v005 machinery visual tag or label contract changed")
    presentation = [actor for actor in actors if PRESENTATION_PASS_TAG in _tags(actor)]
    cameras = [actor for actor in actors if CAMERA_V005_TAG in _tags(actor)]
    deck = [actor for actor in presentation if actor not in cameras]
    runtime = [actor for actor in actors if _class_path(actor) == PRESENTATION_CLASS]
    upgrade_tagged = [actor for actor in actors if V005_UPGRADE_TAG in _tags(actor)]
    polish = [actor for actor in actors if V004_POLISH_TAG in _tags(actor)]
    if (len(presentation), len(deck), len(cameras), len(runtime), len(upgrade_tagged), len(polish)) != (
        EXPECTED_PRESENTATION_COUNT, EXPECTED_PRESENTATION_DECK_COUNT, EXPECTED_CAMERA_COUNT,
        EXPECTED_RUNTIME_PRESENTATION_COUNT, EXPECTED_UPGRADE_TAG_COUNT, EXPECTED_V004_POLISH_TAG_COUNT,
    ):
        fail("v005 presentation/deck/camera provenance inventory changed")
    if PRESENTATION_ADAPTER_TAG not in _tags(runtime[0]):
        fail("v005 runtime presentation adapter tag changed")
    plan_mutations = {str(row["id"]): row for row in contract["plan"]["mutations"]}
    plan_additions = {str(row["id"]): row for row in contract["plan"]["additions"]}
    for item_id, row in contract["mutations"].items():
        if str(row["actor_path"]) not in by_path:
            fail("v005 mutated actor is missing: " + item_id)
        _validate_mutated_actor(by_path[str(row["actor_path"])], row, plan_mutations[item_id])
    for item_id, row in contract["additions"].items():
        if str(row["actor_path"]) not in by_path:
            fail("v005 added actor is missing: " + item_id)
        _validate_added_actor(by_path[str(row["actor_path"])], row, plan_additions[item_id])
    expected_upgrade_paths = {str(row["actor_path"]) for row in [*contract["mutations"].values(), *contract["additions"].values()]}
    if {str(actor.get_path_name()) for actor in upgrade_tagged} != expected_upgrade_paths:
        fail("v005 provenance actor-path set changed")
    camera_by_label = {str(actor.get_actor_label()): actor for actor in cameras}
    if set(camera_by_label) != {str(spec["label"]) for spec in CAMERA_SPECS.values()}:
        fail("v005 saved camera label set changed")
    source_by_id = {str(actor.get_actor_label()).removeprefix("VIS | "): actor for actor in base}
    cargo_by_id = {str(actor.get_actor_label()).removeprefix("CARGO | "): actor for actor in cargo}
    if SELECTED_SOURCE_IDS - set(source_by_id) or SELECTED_CARGO_IDS - set(cargo_by_id):
        fail("v005 coherent-still visual selection no longer resolves")
    visible = [source_by_id[item_id] for item_id in sorted(SELECTED_SOURCE_IDS)]
    visible += [cargo_by_id[item_id] for item_id in sorted(SELECTED_CARGO_IDS)]
    return {"visuals": visuals, "visible_visuals": visible, "deck_actors": deck,
            "runtime_actor": runtime[0], "cameras_by_label": camera_by_label,
            "actors_by_path": by_path}


def protected_snapshot(contract: Mapping[str, Any]) -> Dict[str, str]:
    upgrade = contract["module"]
    result: Dict[str, str] = {}
    for lock_id, (path, expected) in sorted(upgrade.PROTECTED_MAPS.items()):
        if not path.is_file() or digest(path) != expected:
            fail("protected map is missing or changed: " + lock_id)
        result[lock_id] = expected
    return result


def _write_new_receipt(value: Mapping[str, Any]) -> None:
    try:
        with CAPTURE_RECEIPT.open("xb") as handle:
            handle.write(canonical_json_bytes(value))
    except FileExistsError as error:
        raise CaptureGuardError("refusing to overwrite capture receipt: " + str(CAPTURE_RECEIPT)) from error


def main() -> None:
    ue = _require_unreal()
    map_sha, receipt_sha = required_guard_hashes()
    receipt, contract = load_guarded_install_receipt(map_sha, receipt_sha)
    ensure_output_absent()
    protected_before = protected_snapshot({"module": _installer_contract()["module"]})
    if receipt.get("protected_hashes_after") != protected_before:
        fail("current protected hashes differ from the v005 install receipt")
    base_capture = _base_capture_module()
    if base_capture._dirty_packages() != {"content": [], "maps": []}:
        fail("editor has dirty packages before v005 capture")
    editor_subsystem = ue.get_editor_subsystem(ue.UnrealEditorSubsystem)
    current_world = editor_subsystem.get_editor_world() if editor_subsystem else None
    if current_world and str(current_world.get_outermost().get_name()) == TARGET_MAP:
        fail("run from an unrelated clean world; v005 must start unloaded")
    if not ue.EditorLoadingAndSavingUtils.load_map(TARGET_MAP):
        fail("could not load exact v005 saved map")
    world = editor_subsystem.get_editor_world()
    if str(world.get_outermost().get_name()) != TARGET_MAP:
        fail("v005 target did not become the current editor world")
    if base_capture._dirty_packages() != {"content": [], "maps": []} or digest(TARGET_FILE) != map_sha:
        fail("loading v005 dirtied or changed the saved map")
    actor_subsystem = ue.get_editor_subsystem(ue.EditorActorSubsystem)
    if actor_subsystem is None:
        fail("EditorActorSubsystem is unavailable")
    actors = list(actor_subsystem.get_all_level_actors() or [])
    loaded = validate_loaded_world(world, actors, contract)
    before = {path: _fingerprint(actor) for path, actor in sorted(loaded["actors_by_path"].items())}
    visibility_before = {str(actor.get_path_name()): base_capture._visibility_state(actor) for actor in loaded["visuals"]}
    visible_paths = {str(actor.get_path_name()) for actor in loaded["visible_visuals"]}
    residency = base_capture._prepare_texture_residency(loaded["visible_visuals"])
    try:
        for actor in loaded["visuals"]:
            base_capture._set_capture_visibility(actor, str(actor.get_path_name()) in visible_paths)
        show_only = [*loaded["deck_actors"], *loaded["visible_visuals"], loaded["runtime_actor"]]
        captures = base_capture._capture_saved_cameras(
            world, actor_subsystem, loaded["cameras_by_label"], show_only
        )
    finally:
        for actor in loaded["visuals"]:
            base_capture._restore_visibility(actor, visibility_before[str(actor.get_path_name())])
    actors_after = list(actor_subsystem.get_all_level_actors() or [])
    if len(actors_after) != EXPECTED_ACTOR_COUNT:
        fail("v005 actor count changed during transient capture")
    after = {str(actor.get_path_name()): _fingerprint(actor) for actor in actors_after}
    if after != before:
        fail("a saved actor layout, label, camera, material, or collision state changed during capture")
    if {str(actor.get_path_name()): base_capture._visibility_state(actor) for actor in loaded["visuals"]} != visibility_before:
        fail("visual visibility state was not restored after capture")
    dirty_after = base_capture._dirty_packages()
    if dirty_after not in ({"content": [], "maps": []}, {"content": [], "maps": [TARGET_MAP]}):
        fail("transient capture dirtied a package outside the target map")
    if digest(TARGET_FILE) != map_sha or digest(INSTALL_RECEIPT) != receipt_sha:
        fail("v005 map or install receipt bytes changed during capture")
    protected_after = protected_snapshot({"module": _installer_contract()["module"]})
    if protected_after != protected_before:
        fail("protected map changed during v005 capture")
    fingerprint_sha = hashlib.sha256(canonical_json_bytes(after)).hexdigest()
    capture_receipt = {
        "schema": CAPTURE_SCHEMA, "status": CAPTURE_STATUS,
        "target_map": TARGET_MAP, "target_map_sha256_before": map_sha,
        "target_map_sha256_after": digest(TARGET_FILE),
        "install_receipt": INSTALL_RECEIPT.as_posix(), "install_receipt_sha256": receipt_sha,
        "installer_contract_sha256": INSTALLER_SHA256,
        "protected_hashes_before": protected_before, "protected_hashes_after": protected_after,
        "actor_count": EXPECTED_ACTOR_COUNT, "visual_layer_count": EXPECTED_VISUAL_COUNT,
        "base_visual_layer_count": EXPECTED_BASE_VISUAL_COUNT, "cargo_layer_count": EXPECTED_CARGO_COUNT,
        "presentation_deck_actor_count": EXPECTED_PRESENTATION_DECK_COUNT,
        "saved_camera_count": EXPECTED_CAMERA_COUNT, "mutated_existing_presentation_actor_count": EXPECTED_MUTATION_COUNT,
        "new_collision_inert_native_box_count": EXPECTED_NEW_BOX_COUNT,
        "continuous_station_port_count": contract["validation"]["station_port_count"],
        "continuous_station_port_max_gap_cm": contract["validation"]["station_connector_max_gap_cm"],
        "selected_source_visual_ids": sorted(SELECTED_SOURCE_IDS),
        "selected_cargo_visual_ids": sorted(SELECTED_CARGO_IDS),
        "selected_visual_count": len(visible_paths),
        "resident_material_count": residency["materials"],
        "resident_sprite_texture_count": residency["textures"],
        "loaded_actor_layout_material_collision_fingerprint_sha256": fingerprint_sha,
        "layout_material_collision_fingerprint_unchanged": True,
        "visual_visibility_state_restored": True, "presentation_style": receipt["presentation_style"],
        "captures": captures, "capture_resolution": [CAPTURE_WIDTH, CAPTURE_HEIGHT],
        "capture_method": (
            "TRANSIENT_NATIVE_SCENECAPTURE2D_FROM_THREE_SAVED_V005_ORTHOGRAPHIC_"
            "CAMERAS_SHOW_ONLY_CONTINUOUS_SAVED_DECK_SELECTED_VISUALS_AND_NATIVE_PRESENTATION"
        ),
        "dirty_packages_after_capture": dirty_after, "map_load_calls": 1,
        "map_save_calls": 0, "content_save_calls": 0,
        "saved_actor_layout_mutated": False, "saved_actor_material_assignment_mutated": False,
        "saved_actor_collision_mutated": False, "project_content_mutated": False,
        "runtime_simulation_validated": False, "packaged_build_validated": False,
        "steam_visual_quality_human_approved": False,
    }
    _write_new_receipt(capture_receipt)
    ue.log("PRESSSHOP_2126_OVERHEAD_PRESENTATION_V005_CAPTURE_PASS: " + OUTPUT_DIR.as_posix())
    ue.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
