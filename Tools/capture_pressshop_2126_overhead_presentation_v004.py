"""Guarded read-only saved-map capture for the Press Shop 2126 v004 candidate.

The script consumes the *completed* v004 presentation-polish map and its
canonical install receipt.  Both independent SHA-256 values must be supplied
through environment variables; no placeholder digest is embedded here.  It
then validates the saved slate deck, readable labels, authored cameras, the
146 visual layers (including 26 cargo layers), and all three new press-lane
connectors before exporting three 1920x1080 PNGs beneath ``Saved``.

Only visual visibility is selected transiently for one coherent still-image
state.  No saved actor is moved, scaled, re-labelled, re-materialled, created,
deleted, or saved.  A transient native SceneCapture2D is created separately
for each authored camera.  A PASS is saved-map presentation evidence only; it
is not PIE lifecycle, packaged-build, performance, or Steam approval evidence.

Run from an unrelated clean map (normally ``/Engine/Maps/Entry``) with a
rendering RHI, not ``-NullRHI``.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import struct
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

try:  # Keeps the contract importable by ordinary CPython unit tests.
    import unreal  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised only outside UE.
    unreal = None  # type: ignore


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
TARGET_MAP = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v004/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v004"
)
TARGET_FILE = (
    PROJECT / "Content/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v004/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v004.umap"
)
INSTALL_RECEIPT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadPresentation_v004/"
    "install_receipt_v001.json"
)
OUTPUT_DIR = (
    PROJECT / "Saved/PressShop2126/"
    "OverheadPresentation_v004_SavedMapCapture_v001"
)
CAPTURE_RECEIPT = OUTPUT_DIR / "saved_map_capture_receipt_v001.json"

MAP_SHA_ENV = "LB_PRESSSHOP_V004_TARGET_MAP_SHA256"
RECEIPT_SHA_ENV = "LB_PRESSSHOP_V004_INSTALL_RECEIPT_SHA256"

INSTALL_SCHEMA = (
    "cairnwell.press_shop.overhead_presentation_polish_install_receipt.v001"
)
INSTALL_STATUS = (
    "PASS_CANDIDATE_PRESENTATION_POLISH_APPLIED__"
    "CARGO_PRESERVED__PIE_CAPTURE_PENDING"
)
CAPTURE_SCHEMA = (
    "cairnwell.press_shop.overhead_presentation_saved_map_capture_receipt.v001"
)
CAPTURE_STATUS = (
    "PASS_IN_ENGINE_SAVED_MAP_PRESENTATION_CAPTURE__"
    "PIE_LIFECYCLE_AND_STEAM_APPROVAL_PENDING"
)

EXPECTED_GAME_MODE = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
EXPECTED_ACTOR_COUNT = 247
EXPECTED_VISUAL_COUNT = 146
EXPECTED_BASE_VISUAL_COUNT = 120
EXPECTED_CARGO_COUNT = 26
EXPECTED_PRESENTATION_TAG_COUNT = 85
EXPECTED_PRESENTATION_DECK_COUNT = 82
EXPECTED_CAMERA_COUNT = 3
EXPECTED_RUNTIME_PRESENTATION_COUNT = 1
EXPECTED_MUTATION_COUNT = 38
EXPECTED_CONNECTOR_COUNT = 3
EXPECTED_POLISH_TAG_COUNT = 41

CAPTURE_WIDTH = 1920
CAPTURE_HEIGHT = 1080
MIN_CAPTURE_BYTES = 32768
NUMERIC_TOLERANCE = 0.001

VISUAL_CLASS = "/Script/LineBossCarFactory.LBPressShopOverheadVisualLayerActor"
PRESENTATION_CLASS = "/Script/LineBossCarFactory.LBPressShopOverheadPresentationActor"
STATIC_MESH_CLASS = "/Script/Engine.StaticMeshActor"
TEXT_RENDER_CLASS = "/Script/Engine.TextRenderActor"
CAMERA_CLASS = "/Script/Engine.CameraActor"

VISUAL_TAG = "LB.PressShop.Overhead.VisualLayer.v001"
PRESENTATION_ADAPTER_TAG = "LB.PressShop.OverheadPresentation.v001"
PRESENTATION_PASS_TAG = "LB.PressShop.OverheadDeckPresentation.v002"
PRESENTATION_CAMERA_TAG = "LB.PressShop.OverheadDeck.Camera.v002"
CARGO_MAP_TAG = "LB.PressShop.OverheadCargoMap.v003"
CARGO_SOURCE_TAG = "LB.PressShop.CargoContinuity.v001"
POLISH_TAG = "LB.PressShop.OverheadPresentationPolish.v004"
CAMERA_V004_TAG = "LB.PressShop.OverheadDeck.Camera.v004"

SLATE_DECK_MATERIAL = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v004/Materials/"
    "M_CA_MW_PS2126_DeckSlateGreen_Unlit_v004"
)
ZONE_MATERIAL = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v002/Materials/"
    "M_CA_MW_PS2126_ZonePaleGreen_Unlit_v001"
)
DECK_CHARCOAL_MATERIAL = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v002/Materials/"
    "M_CA_MW_PS2126_DeckCharcoal_Unlit_v001"
)
CREAM_MATERIAL = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v002/Materials/"
    "M_CA_MW_PS2126_FlowCream_Unlit_v001"
)
SLATE_DECK_SRGB_HEX = "#36534F"

TEXT_ROTATION = (90.0, 180.0, 0.0)
CAMERA_ROTATION = (-90.0, 0.0, 0.0)
CAMERA_ASPECT = 16.0 / 9.0
CAMERA_SPECS: Mapping[str, Mapping[str, Any]] = {
    "overview": {
        "label": "CAM | Press Shop 2126 | roofless deck overview v004",
        "location_cm": (-7730.645880159617, 8840.218280826943, 21712.544),
        "ortho_width_cm": 16800.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.Overview.v004",
        "filename": "PressShop2126_PresentationOverview_1920x1080_v004.png",
    },
    "press_spine": {
        "label": "CAM | Press Shop 2126 | roofless production spine v004",
        "location_cm": (-8450.0, 10450.0, 21712.544),
        "ortho_width_cm": 8900.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.PressSpine.v004",
        "filename": "PressShop2126_PresentationSpine_1920x1080_v004.png",
    },
    "steam_hero": {
        "label": "CAM | Press Shop 2126 | S03-S06 native-scale Steam hero v004",
        "location_cm": (-8990.75, 11125.0, 21712.544),
        "ortho_width_cm": 6300.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.SteamHero.v004",
        "filename": "PressShop2126_PresentationPressHero_1920x1080_v004.png",
    },
}

TEXT_IDS = {
    "LABEL_IN01", "LABEL_IN02", "LABEL_IN03", "LABEL_IN04_05",
    "LABEL_S01", "LABEL_S02", "LABEL_S03", "LABEL_S04", "LABEL_S05",
    "LABEL_S06", "LABEL_S07_INSPECT", "LABEL_S07_PALLET",
    "LABEL_TITLE", "LABEL_INBOUND", "LABEL_OUTBOUND",
}
PRESS_PAD_LENGTHS_Y: Mapping[str, float] = {
    "S03": 1350.0,
    "S04": 1050.0,
    "S05": 1350.0,
    "S06": 1200.0,
}
BOX_IDS = {
    "DECK_BASE", "FLOW_LANE",
    "FLOW_EDGE_WEST", "FLOW_EDGE_EAST",
    "FLOW_EDGE_INBOUND", "FLOW_EDGE_OUTBOUND",
    *("PAD_" + station for station in PRESS_PAD_LENGTHS_Y),
    *("PAD_KEY_" + station for station in PRESS_PAD_LENGTHS_Y),
    *("FLOW_CONNECTOR_{:02d}".format(index) for index in range(1, 7)),
}

CONNECTOR_SPECS: Mapping[str, Mapping[str, Any]] = {
    station: {
        "id": "FLOW_CONNECTOR_PRESS_" + station,
        "label": "2126 OVERHEAD FLOW | cream press connector {} v004".format(station),
        "location_cm": (-7420.375, center_y, -0.25),
        "dimensions_cm": (1340.75, 58.0, 0.3),
        "material": CREAM_MATERIAL,
    }
    for station, center_y in {
        "S03": 8950.0,
        "S05": 11850.0,
        "S06": 13300.0,
    }.items()
}

# One honest simultaneous still state.  Visibility is capture-only; neither
# transforms nor materials are touched.  Runtime/PIE captures separately prove
# the animation states.
SELECTED_SOURCE_IDS = {
    "LAYER_096_S07_InspectionCell_BaseEmpty_v001",
    "LAYER_109_S07_PalletisingCell_BaseEmpty_v001",
    "LAYER_070_S02_FRAME_OPEN_v001",
    "LAYER_074_S03_FRAME_OPEN_v001",
    "LAYER_078_S04_FRAME_OPEN_v001",
    "LAYER_082_S05_FRAME_OPEN_v001",
    "LAYER_086_S06_FRAME_OPEN_v001",
    "LAYER_088_S07_ExitConveyor_BeltMotion_00_v001",
    "LAYER_105_S07_PalletStack_00_Overlay_v001",
    "LAYER_111_S07_ROBOT_A_PARKED",
    "LAYER_115_S07_ROBOT_B_PARKED",
    "LAYER_037_IN03_storage_base_v001",
    "LAYER_003_IN04_depack_base_sprite_v001",
    "LAYER_038_IN05_bare_coil_saddle_v001",
    "LAYER_040_S01A_coil_rack_base_v001",
    "LAYER_041_S01B_decoiler_base_v001",
    "LAYER_058_S01C_straightener_base_v001",
    "LAYER_059_S01D_feed_bridge_base_v001",
    "LAYER_001_IN01A_tractor_sprite_v002",
    "LAYER_002_IN01B_trailer_sidesaddle_sprite_v002",
    "LAYER_036_IN02_coil_handler_agv_v001",
    "LAYER_004_IN04_drive_rollers_frame_00_v001",
    "LAYER_020_IN04_film_takeup_frame_00_v001",
    "LAYER_039_S01A_coil_cart_base_v001",
    "LAYER_042_S01B_decoiler_spindle_payoff_frame_00_v001",
    "LAYER_050_S01C_entry_strip_pulse_frame_00_v001",
    "LAYER_060_S01D_feed_strip_pulse_frame_00_v001",
    "LAYER_110_IN05_BARE_COIL_AT_SADDLE",
}
SELECTED_CARGO_IDS = {
    "WRAPPED_IN01_UNLOAD",
    "WRAPPED_IN03_BUFFERED",
    "BARE_IN05_OUTPUT_TO_RACK",
    "S02_PANEL_BLANK",
    "S03_WORKPIECE_REGISTERED",
    "S04_WORKPIECE_REGISTERED",
    "S05_WORKPIECE_REGISTERED",
    "S06_WORKPIECE_REGISTERED",
    "S07_PANEL_INSPECT",
    "S07_PALLET_BASE_PARKED",
    "S07_DISPATCH_STACK_08",
}

PROTECTED_MAPS: Mapping[str, Tuple[Path, str]] = {
    "source_overhead_cargo_v003": (
        PROJECT / "Content/LineBoss/Candidates/PressShop/"
        "PressShop2126_OverheadCargo_v003/Maps/"
        "LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003.umap",
        "5eae51f2a7d3e1c72deb4fd455d57a6339dee061840b7d062c5ddf680ab6100f",
    ),
    "source_overhead_presentation_v002": (
        PROJECT / "Content/LineBoss/Candidates/PressShop/"
        "PressShop2126_OverheadPresentation_v002/Maps/"
        "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v002.umap",
        "58fe57f3af0dfcf4021d6bbcd3a52d7d66de22187b561fb2db41becd83023275",
    ),
    "builder_authority_v438": (
        PROJECT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap",
        "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    ),
    "onefactory_authority": (
        PROJECT / "Content/LineBoss/Factory/OneFactory/v001/Maps/"
        "LB_MoorcrossWorks_OneFactory_v001.umap",
        "f4e97b33cdfb1f242b2c606a16b4caa05b74b298fdf1b1263d4a4c46d50e8d5c",
    ),
    "overhead_playable_v001": (
        PROJECT / "Content/LineBoss/Candidates/PressShop/"
        "PressShop2126_OverheadPlayable_v001/Maps/"
        "LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001.umap",
        "43020cb3ea7d18a49319da68a04ae1b96d5af0d535c705e947f81d5c005ba7ce",
    ),
    "legacy_steam_v002": (
        PROJECT / "Content/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/"
        "LB_PressShop_2126_Steam_v002.umap",
        "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
    ),
}


class CaptureGuardError(RuntimeError):
    """The v004 read-only capture contract rejected the current state."""


def fail(message: str) -> None:
    raise CaptureGuardError(
        "PRESSSHOP_2126_OVERHEAD_PRESENTATION_V004_CAPTURE_FAIL: " + message
    )


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest().lower()


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _require_sha(value: Any, context: str) -> str:
    if (
        not isinstance(value, str)
        or re.fullmatch(r"[0-9a-f]{64}", value) is None
        or value == "0" * 64
    ):
        fail(context + " must be an explicit lower-case SHA-256")
    return value


def required_guard_hashes(
    environ: Mapping[str, str] | None = None,
) -> Tuple[str, str]:
    values = os.environ if environ is None else environ
    map_sha = _require_sha(values.get(MAP_SHA_ENV), MAP_SHA_ENV)
    receipt_sha = _require_sha(values.get(RECEIPT_SHA_ENV), RECEIPT_SHA_ENV)
    return map_sha, receipt_sha


def _close(left: Sequence[Any], right: Sequence[Any]) -> bool:
    if len(left) != len(right):
        return False
    try:
        return all(
            math.isfinite(float(a))
            and math.isfinite(float(b))
            and abs(float(a) - float(b)) <= NUMERIC_TOLERANCE
            for a, b in zip(left, right)
        )
    except (TypeError, ValueError):
        return False


def _rotation_close(left: Sequence[Any], right: Sequence[Any]) -> bool:
    if len(left) != len(right):
        return False

    def quaternion(values: Sequence[Any]) -> Tuple[float, float, float, float]:
        pitch, yaw, roll = (math.radians(float(value)) / 2.0 for value in values)
        sin_roll, cos_roll = math.sin(roll), math.cos(roll)
        sin_pitch, cos_pitch = math.sin(pitch), math.cos(pitch)
        sin_yaw, cos_yaw = math.sin(yaw), math.cos(yaw)
        return (
            sin_roll * cos_pitch * cos_yaw - cos_roll * sin_pitch * sin_yaw,
            cos_roll * sin_pitch * cos_yaw + sin_roll * cos_pitch * sin_yaw,
            cos_roll * cos_pitch * sin_yaw - sin_roll * sin_pitch * cos_yaw,
            cos_roll * cos_pitch * cos_yaw + sin_roll * sin_pitch * sin_yaw,
        )

    try:
        dot = sum(a * b for a, b in zip(quaternion(left), quaternion(right)))
    except (TypeError, ValueError):
        return False
    return 1.0 - abs(dot) <= NUMERIC_TOLERANCE


def _asset_path(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value.get_path_name()) if hasattr(value, "get_path_name") else str(value)
    if raw.startswith("Class'") and raw.endswith("'"):
        raw = raw[6:-1]
    # Object paths use ``Package.Object`` while native class paths use the dot
    # inside ``/Script/Module.Class`` as part of the class identity.
    if raw.startswith(("/Game/", "/Engine/")):
        return raw.split(".", 1)[0]
    return raw


def virtual_to_uasset(asset_path: str) -> Path:
    if not asset_path.startswith("/Game/"):
        fail("not a /Game asset path: " + asset_path)
    result = (
        PROJECT / "Content" / (asset_path.removeprefix("/Game/") + ".uasset")
    ).resolve()
    if not result.is_relative_to((PROJECT / "Content").resolve()):
        fail("asset path escapes Content: " + asset_path)
    return result


def protected_snapshot() -> Dict[str, str]:
    result: Dict[str, str] = {}
    for lock_id, (path, expected_sha) in sorted(PROTECTED_MAPS.items()):
        if not path.is_file():
            fail("protected map is missing: {}: {}".format(lock_id, path))
        actual_sha = digest(path)
        if actual_sha != expected_sha:
            fail("protected map hash changed: {}: {}".format(lock_id, actual_sha))
        result[lock_id] = actual_sha
    return result


def _index_records(
    rows: Any, context: str, expected_count: int,
) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(rows, list) or len(rows) != expected_count:
        fail("{} count changed".format(context))
    result: Dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if not isinstance(row, Mapping) or not isinstance(row.get("id"), str):
            fail(context + " contains an invalid record")
        item_id = str(row["id"])
        if item_id in result:
            fail(context + " contains duplicate id: " + item_id)
        result[item_id] = row
    return result


def validate_install_receipt(
    receipt: Mapping[str, Any],
    expected_map_sha: str,
    actual_map_bytes: int,
) -> Dict[str, Any]:
    """Validate the pure v004 receipt contract without importing Unreal."""
    if receipt.get("schema") != INSTALL_SCHEMA or receipt.get("status") != INSTALL_STATUS:
        fail("v004 install receipt schema or status changed")
    exact = {
        "candidate_only": True,
        "target_map": TARGET_MAP,
        "target_map_sha256": expected_map_sha,
        "target_map_bytes": actual_map_bytes,
        "source_actor_count": 244,
        "final_actor_count": EXPECTED_ACTOR_COUNT,
        "combined_visual_layer_count": EXPECTED_VISUAL_COUNT,
        "cargo_layer_count": EXPECTED_CARGO_COUNT,
        "cargo_actor_mutated_count": 0,
        "machinery_actor_mutated_count": 0,
        "source_actor_removed_count": 0,
        "source_actor_created_count": EXPECTED_CONNECTOR_COUNT,
        "mutated_existing_presentation_actor_count": EXPECTED_MUTATION_COUNT,
        "created_presentation_connector_count": EXPECTED_CONNECTOR_COUNT,
        "source_map_mutated": False,
        "protected_authority_map_mutated": False,
        "native_cpp_modified": False,
        "roof_created": False,
        "new_machinery_geometry": 0,
        "new_cargo_geometry": 0,
        "runtime_validated": False,
        "packaged_build_validated": False,
        "visual_capture_validated": False,
        "steam_capture_validated": False,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("v004 install receipt field changed: " + key)
    if receipt.get("game_mode_before") != EXPECTED_GAME_MODE or receipt.get("game_mode_after") != EXPECTED_GAME_MODE:
        fail("v004 install receipt GameMode changed")
    if receipt.get("protected_hashes_before") != receipt.get("protected_hashes_after"):
        fail("v004 install receipt does not preserve protected hashes")
    expected_protected = {key: value[1] for key, value in sorted(PROTECTED_MAPS.items())}
    if receipt.get("protected_hashes_after") != expected_protected:
        fail("v004 install receipt protected-hash set changed")

    deck_style = receipt.get("deck_style")
    if deck_style != {
        "full_deck_material": SLATE_DECK_MATERIAL,
        "full_deck_srgb_hex": SLATE_DECK_SRGB_HEX,
        "station_pad_material": ZONE_MATERIAL,
        "narrow_flow_lane_material": DECK_CHARCOAL_MATERIAL,
    }:
        fail("v004 saved deck-style contract changed")

    material_rows = receipt.get("created_materials")
    if not isinstance(material_rows, list) or len(material_rows) != 1:
        fail("v004 created-material inventory changed")
    material = material_rows[0]
    if (
        not isinstance(material, Mapping)
        or material.get("asset") != SLATE_DECK_MATERIAL
        or material.get("srgb_hex") != SLATE_DECK_SRGB_HEX
        or material.get("shading_model") != "UNLIT"
        or not isinstance(material.get("bytes"), int)
        or int(material["bytes"]) <= 0
    ):
        fail("v004 slate material receipt changed")
    _require_sha(material.get("sha256"), "v004 slate material sha256")

    mutations = _index_records(
        receipt.get("presentation_mutations"),
        "v004 presentation mutations",
        EXPECTED_MUTATION_COUNT,
    )
    expected_ids = BOX_IDS | TEXT_IDS | set(CAMERA_SPECS)
    if set(mutations) != expected_ids:
        fail("v004 presentation mutation id set changed")
    if {item_id for item_id, row in mutations.items() if row.get("kind") == "box"} != BOX_IDS:
        fail("v004 box mutation set changed")
    if {item_id for item_id, row in mutations.items() if row.get("kind") == "text"} != TEXT_IDS:
        fail("v004 text mutation set changed")
    if {item_id for item_id, row in mutations.items() if row.get("kind") == "camera"} != set(CAMERA_SPECS):
        fail("v004 camera mutation set changed")

    deck = mutations["DECK_BASE"]
    if deck.get("target_material") != SLATE_DECK_MATERIAL:
        fail("v004 saved deck does not use the slate material")
    lane = mutations["FLOW_LANE"]
    if (
        lane.get("target_material") != DECK_CHARCOAL_MATERIAL
        or not _close(lane.get("target_dimensions_cm", ()), (500.0, 15500.0, 0.6))
    ):
        fail("v004 saved narrow flow lane changed")
    for station, length_y in PRESS_PAD_LENGTHS_Y.items():
        pad = mutations["PAD_" + station]
        key = mutations["PAD_KEY_" + station]
        if (
            pad.get("target_material") != ZONE_MATERIAL
            or not _close(pad.get("target_dimensions_cm", ()), (1800.0, length_y, 0.8))
            or not _close(key.get("target_dimensions_cm", ()), (42.0, length_y - 100.0, 0.4))
        ):
            fail("v004 saved press-pad contract changed: " + station)
    for item_id in TEXT_IDS:
        if not _rotation_close(
            mutations[item_id].get("target_rotation_deg_pitch_yaw_roll", ()),
            TEXT_ROTATION,
        ):
            fail("v004 readable label rotation changed: " + item_id)
    for item_id, spec in CAMERA_SPECS.items():
        row = mutations[item_id]
        if (
            row.get("target_label") != spec["label"]
            or not _close(row.get("target_location_cm", ()), spec["location_cm"])
            or not _rotation_close(
                row.get("target_rotation_deg_pitch_yaw_roll", ()), CAMERA_ROTATION
            )
            or not _close(
                (row.get("target_ortho_width_cm"),), (spec["ortho_width_cm"],)
            )
        ):
            fail("v004 saved camera contract changed: " + item_id)

    connectors = _index_records(
        receipt.get("created_press_connectors"),
        "v004 press connectors",
        EXPECTED_CONNECTOR_COUNT,
    )
    expected_connector_ids = {
        str(spec["id"]) for spec in CONNECTOR_SPECS.values()
    }
    if set(connectors) != expected_connector_ids:
        fail("v004 press connector id set changed")
    connector_specs_by_id = {
        str(spec["id"]): spec for spec in CONNECTOR_SPECS.values()
    }
    for item_id, row in connectors.items():
        spec = connector_specs_by_id[item_id]
        if (
            row.get("label") != spec["label"]
            or row.get("material") != spec["material"]
            or row.get("collision") != "NoCollision"
            or row.get("cast_shadow") is not False
            or not _close(row.get("location_cm", ()), spec["location_cm"])
            or not _close(row.get("dimensions_cm", ()), spec["dimensions_cm"])
        ):
            fail("v004 press connector contract changed: " + item_id)

    return {
        "mutations": mutations,
        "connectors": connectors,
        "material": dict(material),
    }


def load_guarded_install_receipt(
    expected_map_sha: str, expected_receipt_sha: str,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not TARGET_FILE.is_file() or not INSTALL_RECEIPT.is_file():
        fail("v004 map or install receipt is missing")
    actual_map_sha = digest(TARGET_FILE)
    actual_receipt_sha = digest(INSTALL_RECEIPT)
    if actual_map_sha != expected_map_sha:
        fail("v004 map hash differs from supplied final hash: " + actual_map_sha)
    if actual_receipt_sha != expected_receipt_sha:
        fail("v004 receipt hash differs from supplied final hash: " + actual_receipt_sha)
    payload = INSTALL_RECEIPT.read_bytes()
    try:
        receipt = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        fail("v004 install receipt is not valid UTF-8 JSON: " + str(error))
    if not isinstance(receipt, dict) or payload != canonical_json_bytes(receipt):
        fail("v004 install receipt is not canonical JSON")
    contract = validate_install_receipt(receipt, expected_map_sha, TARGET_FILE.stat().st_size)
    material_path = virtual_to_uasset(SLATE_DECK_MATERIAL)
    material = contract["material"]
    if (
        not material_path.is_file()
        or material_path.stat().st_size != int(material["bytes"])
        or digest(material_path) != str(material["sha256"])
    ):
        fail("v004 slate material package differs from its receipt")
    return receipt, contract


def ensure_output_absent(path: Path = OUTPUT_DIR) -> None:
    if path.exists():
        fail("refusing to overwrite or merge capture evidence: " + str(path))


def _require_unreal() -> Any:
    if unreal is None:
        fail("this capture must run inside Unreal Editor Python")
    return unreal


def _class_path(actor: Any) -> str:
    return str(actor.get_class().get_path_name())


def _tags(actor: Any) -> set[str]:
    return {str(tag) for tag in list(actor.tags or [])}


def _transform_record(actor: Any) -> Dict[str, List[float]]:
    transform = actor.get_actor_transform()
    rotation = transform.rotation.rotator()
    return {
        "location_cm": [
            float(transform.translation.x),
            float(transform.translation.y),
            float(transform.translation.z),
        ],
        "rotation_deg_pitch_yaw_roll": [
            float(rotation.pitch), float(rotation.yaw), float(rotation.roll)
        ],
        "scale3d": [
            float(transform.scale3d.x),
            float(transform.scale3d.y),
            float(transform.scale3d.z),
        ],
    }


def _safe_property(value: Any, names: Sequence[str]) -> Any:
    for name in names:
        try:
            return value.get_editor_property(name)
        except Exception:
            continue
    return None


def _layout_material_fingerprint(actor: Any) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "path": str(actor.get_path_name()),
        "label": str(actor.get_actor_label()),
        "class_path": _class_path(actor),
        "tags": sorted(_tags(actor)),
        **_transform_record(actor),
    }
    component = _safe_property(actor, ("static_mesh_component",))
    if component is not None:
        record["static_mesh"] = _asset_path(
            _safe_property(component, ("static_mesh",))
        )
        record["materials"] = [
            _asset_path(component.get_material(index))
            for index in range(int(component.get_num_materials()))
        ]
    text = _safe_property(actor, ("text_render",))
    if text is not None:
        record["text"] = str(text.get_editor_property("text"))
    camera = _safe_property(actor, ("camera_component",))
    if camera is not None:
        record["camera"] = {
            "projection": str(camera.get_editor_property("projection_mode")),
            "ortho_width_cm": float(camera.get_editor_property("ortho_width")),
            "aspect_ratio": float(camera.get_editor_property("aspect_ratio")),
        }
    return record


def _dirty_packages() -> Dict[str, List[str]]:
    ue = _require_unreal()
    return {
        "content": sorted(
            str(value.get_path_name())
            for value in ue.EditorLoadingAndSavingUtils.get_dirty_content_packages()
        ),
        "maps": sorted(
            str(value.get_path_name())
            for value in ue.EditorLoadingAndSavingUtils.get_dirty_map_packages()
        ),
    }


def _world_package_name(world: Any) -> str:
    return str(world.get_outermost().get_name()) if world else ""


def _world_game_mode(world: Any) -> str | None:
    game_mode = world.get_world_settings().get_editor_property("default_game_mode")
    return _asset_path(game_mode)


def _validate_actor_against_mutation(actor: Any, row: Mapping[str, Any]) -> None:
    item_id = str(row["id"])
    kind = str(row["kind"])
    transform = _transform_record(actor)
    if str(actor.get_actor_label()) != str(row["target_label"]):
        fail("v004 loaded actor label changed: " + item_id)
    if POLISH_TAG not in _tags(actor):
        fail("v004 loaded actor lost polish provenance: " + item_id)
    if (
        not _close(transform["location_cm"], row["target_location_cm"])
        or not _rotation_close(
            transform["rotation_deg_pitch_yaw_roll"],
            row["target_rotation_deg_pitch_yaw_roll"],
        )
    ):
        fail("v004 loaded actor transform changed: " + item_id)
    if kind == "box":
        if _class_path(actor) != STATIC_MESH_CLASS:
            fail("v004 loaded box class changed: " + item_id)
        expected_scale = [float(value) / 100.0 for value in row["target_dimensions_cm"]]
        component = actor.get_editor_property("static_mesh_component")
        if (
            not _close(transform["scale3d"], expected_scale)
            or _asset_path(component.get_material(0)) != row["target_material"]
        ):
            fail("v004 loaded box dimensions or material changed: " + item_id)
    elif kind == "text":
        if _class_path(actor) != TEXT_RENDER_CLASS:
            fail("v004 loaded TextRender class changed: " + item_id)
    elif kind == "camera":
        if _class_path(actor) != CAMERA_CLASS:
            fail("v004 loaded camera class changed: " + item_id)
        component = actor.get_editor_property("camera_component")
        if (
            component.get_editor_property("projection_mode")
            != unreal.CameraProjectionMode.ORTHOGRAPHIC
            or not _close(
                (component.get_editor_property("ortho_width"),),
                (row["target_ortho_width_cm"],),
            )
            or not _close(
                (component.get_editor_property("aspect_ratio"),), (CAMERA_ASPECT,)
            )
            or CAMERA_V004_TAG not in _tags(actor)
        ):
            fail("v004 loaded camera settings changed: " + item_id)
    else:
        fail("v004 loaded unknown mutation kind: " + kind)


def _validate_connector_actor(actor: Any, row: Mapping[str, Any]) -> None:
    item_id = str(row["id"])
    transform = _transform_record(actor)
    component = actor.get_editor_property("static_mesh_component")
    if (
        _class_path(actor) != STATIC_MESH_CLASS
        or str(actor.get_actor_label()) != str(row["label"])
        or POLISH_TAG not in _tags(actor)
        or PRESENTATION_PASS_TAG not in _tags(actor)
        or not _close(transform["location_cm"], row["location_cm"])
        or not _close(
            transform["scale3d"],
            [float(value) / 100.0 for value in row["dimensions_cm"]],
        )
        or _asset_path(component.get_material(0)) != row["material"]
        or bool(actor.get_actor_enable_collision())
        or "NO_COLLISION" not in str(component.get_collision_enabled()).upper()
    ):
        fail("v004 loaded press connector changed: " + item_id)


def validate_loaded_world(
    world: Any,
    actors: Sequence[Any],
    contract: Mapping[str, Any],
) -> Dict[str, Any]:
    if _world_package_name(world) != TARGET_MAP:
        fail("exact v004 map is not the current editor world")
    if _world_game_mode(world) != EXPECTED_GAME_MODE:
        fail("v004 map GameMode changed")
    if len(actors) != EXPECTED_ACTOR_COUNT:
        fail("v004 loaded actor count changed")
    by_path = {str(actor.get_path_name()): actor for actor in actors}
    if len(by_path) != len(actors):
        fail("v004 loaded actor paths are duplicated")

    visuals = [actor for actor in actors if _class_path(actor) == VISUAL_CLASS]
    cargo = [actor for actor in visuals if CARGO_MAP_TAG in _tags(actor)]
    base = [actor for actor in visuals if CARGO_MAP_TAG not in _tags(actor)]
    if len(visuals) != EXPECTED_VISUAL_COUNT or len(cargo) != EXPECTED_CARGO_COUNT or len(base) != EXPECTED_BASE_VISUAL_COUNT:
        fail("v004 loaded visual/cargo inventory changed")
    if any(
        VISUAL_TAG not in _tags(actor)
        or not str(actor.get_actor_label()).startswith("CARGO | ")
        or CARGO_SOURCE_TAG not in _tags(actor)
        for actor in cargo
    ):
        fail("v004 cargo tag or label contract changed")
    if any(
        VISUAL_TAG not in _tags(actor)
        or not str(actor.get_actor_label()).startswith("VIS | ")
        for actor in base
    ):
        fail("v004 base visual tag or label contract changed")

    presentation_tagged = [
        actor for actor in actors if PRESENTATION_PASS_TAG in _tags(actor)
    ]
    cameras = [actor for actor in actors if CAMERA_V004_TAG in _tags(actor)]
    deck = [actor for actor in presentation_tagged if actor not in cameras]
    runtime = [actor for actor in actors if _class_path(actor) == PRESENTATION_CLASS]
    polish = [actor for actor in actors if POLISH_TAG in _tags(actor)]
    if (
        len(presentation_tagged) != EXPECTED_PRESENTATION_TAG_COUNT
        or len(deck) != EXPECTED_PRESENTATION_DECK_COUNT
        or len(cameras) != EXPECTED_CAMERA_COUNT
        or len(runtime) != EXPECTED_RUNTIME_PRESENTATION_COUNT
        or len(polish) != EXPECTED_POLISH_TAG_COUNT
    ):
        fail("v004 presentation/deck/camera inventory changed")
    if PRESENTATION_ADAPTER_TAG not in _tags(runtime[0]):
        fail("v004 runtime presentation adapter tag changed")

    for row in contract["mutations"].values():
        path = str(row.get("actor_path", ""))
        if path not in by_path:
            fail("v004 receipt actor is missing from loaded world: " + str(row["id"]))
        _validate_actor_against_mutation(by_path[path], row)
    for row in contract["connectors"].values():
        path = str(row.get("actor_path", ""))
        if path not in by_path:
            fail("v004 receipt connector is missing from loaded world: " + str(row["id"]))
        _validate_connector_actor(by_path[path], row)

    camera_by_label = {str(actor.get_actor_label()): actor for actor in cameras}
    expected_camera_labels = {str(spec["label"]) for spec in CAMERA_SPECS.values()}
    if set(camera_by_label) != expected_camera_labels:
        fail("v004 saved camera label set changed")

    source_by_id = {
        str(actor.get_actor_label()).removeprefix("VIS | "): actor for actor in base
    }
    cargo_by_id = {
        str(actor.get_actor_label()).removeprefix("CARGO | "): actor for actor in cargo
    }
    if set(SELECTED_SOURCE_IDS) - set(source_by_id):
        fail("v004 capture source selection no longer resolves")
    if set(SELECTED_CARGO_IDS) - set(cargo_by_id):
        fail("v004 capture cargo selection no longer resolves")
    visible = [source_by_id[item_id] for item_id in sorted(SELECTED_SOURCE_IDS)]
    visible += [cargo_by_id[item_id] for item_id in sorted(SELECTED_CARGO_IDS)]
    return {
        "visuals": visuals,
        "visible_visuals": visible,
        "deck_actors": deck,
        "runtime_actor": runtime[0],
        "cameras_by_label": camera_by_label,
        "actors_by_path": by_path,
    }


def _visibility_state(actor: Any) -> Dict[str, bool]:
    component = actor.get_editor_property("static_mesh_component")
    return {
        "actor_hidden": bool(actor.get_editor_property("hidden")),
        "component_visible": bool(component.get_editor_property("visible")),
        "component_hidden": bool(component.get_editor_property("hidden_in_game")),
    }


def _set_capture_visibility(actor: Any, visible: bool) -> None:
    component = actor.get_editor_property("static_mesh_component")
    actor.set_actor_hidden_in_game(not visible)
    component.set_visibility(visible, True)
    component.set_hidden_in_game(not visible, True)


def _restore_visibility(actor: Any, state: Mapping[str, bool]) -> None:
    component = actor.get_editor_property("static_mesh_component")
    actor.set_actor_hidden_in_game(bool(state["actor_hidden"]))
    component.set_visibility(bool(state["component_visible"]), True)
    component.set_hidden_in_game(bool(state["component_hidden"]), True)


def validate_png(path: Path) -> Dict[str, Any]:
    if not path.is_file() or path.stat().st_size < MIN_CAPTURE_BYTES:
        fail("capture is missing or implausibly small: " + str(path))
    with path.open("rb") as handle:
        header = handle.read(24)
    if len(header) != 24 or header[:8] != b"\x89PNG\r\n\x1a\n" or header[12:16] != b"IHDR":
        fail("capture is not a PNG: " + str(path))
    width, height = struct.unpack(">II", header[16:24])
    if (width, height) != (CAPTURE_WIDTH, CAPTURE_HEIGHT):
        fail("capture resolution changed: {}x{}".format(width, height))
    return {
        "path": path.as_posix(),
        "sha256": digest(path),
        "bytes": path.stat().st_size,
        "width": width,
        "height": height,
    }


def _prepare_texture_residency(visuals: Iterable[Any]) -> Dict[str, int]:
    ue = _require_unreal()
    materials: Dict[str, Any] = {}
    textures: Dict[str, Any] = {}
    for actor in visuals:
        component = actor.get_editor_property("static_mesh_component")
        material = component.get_material(0)
        if material is None:
            fail("selected visual has no resolved slot-0 material")
        materials[str(material.get_path_name())] = material
        texture = ue.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
            material, "SpriteTexture"
        )
        if texture is None:
            fail("selected visual material has no SpriteTexture")
        textures[str(texture.get_path_name())] = texture
    for texture in textures.values():
        texture.set_force_mip_levels_to_be_resident(120.0, 0)
    for material in materials.values():
        material.set_force_mip_levels_to_be_resident(True, True, 120.0, 0, True)
    return {"materials": len(materials), "textures": len(textures)}


def _capture_saved_cameras(
    world: Any,
    actor_subsystem: Any,
    cameras_by_label: Mapping[str, Any],
    show_only: Sequence[Any],
) -> List[Dict[str, Any]]:
    ue = _require_unreal()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=False)
    for command in (
        "viewmode lit",
        "r.TextureStreaming 0",
        "r.Streaming.FullyLoadUsedTextures 1",
        "r.Streaming.FramesForFullUpdate 1",
        "r.BloomQuality 0",
        "sg.AntiAliasingQuality 4",
        "r.ScreenPercentage 100",
    ):
        ue.SystemLibrary.execute_console_command(world, command)
    ue.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    ue.AutomationLibrary.finish_loading_before_screenshot()

    results: List[Dict[str, Any]] = []
    for item_id in ("overview", "press_spine", "steam_hero"):
        spec = CAMERA_SPECS[item_id]
        camera = cameras_by_label[str(spec["label"])]
        camera_component = camera.get_editor_property("camera_component")
        output = OUTPUT_DIR / str(spec["filename"])
        if output.exists():
            fail("refusing to overwrite capture: " + str(output))
        target = ue.RenderingLibrary.create_render_target2d(
            world,
            CAPTURE_WIDTH,
            CAPTURE_HEIGHT,
            ue.TextureRenderTargetFormat.RTF_RGBA8,
            ue.LinearColor(0.018, 0.040, 0.043, 1.0),
            False,
            False,
        )
        if target is None:
            fail("could not create transient render target: " + item_id)
        target.set_editor_property("target_gamma", 2.2)
        capture_actor = actor_subsystem.spawn_actor_from_class(
            ue.SceneCapture2D,
            camera.get_actor_location(),
            camera.get_actor_rotation(),
            transient=True,
        )
        if capture_actor is None:
            fail("could not spawn transient SceneCapture2D: " + item_id)
        try:
            component = capture_actor.get_editor_property("capture_component2d")
            component.set_editor_property("texture_target", target)
            component.set_editor_property(
                "capture_source", ue.SceneCaptureSource.SCS_FINAL_COLOR_LDR
            )
            component.set_editor_property(
                "projection_type", ue.CameraProjectionMode.ORTHOGRAPHIC
            )
            component.set_editor_property(
                "ortho_width", float(camera_component.get_editor_property("ortho_width"))
            )
            component.set_editor_property("capture_every_frame", False)
            component.set_editor_property("capture_on_movement", False)
            component.set_editor_property("post_process_blend_weight", 0.0)
            component.set_editor_property("ignore_screen_percentage", True)
            component.set_editor_property(
                "primitive_render_mode",
                ue.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST,
            )
            for actor in show_only:
                component.show_only_actor_components(actor, True)
            ue.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
            ue.AutomationLibrary.finish_loading_before_screenshot()
            for _ in range(4):
                component.capture_scene()
            ue.RenderingLibrary.export_render_target(
                world, target, str(OUTPUT_DIR), output.name
            )
            record = validate_png(output)
            record.update({
                "camera_id": item_id,
                "source_camera_label": str(spec["label"]),
                "source_camera_path": str(camera.get_path_name()),
                "projection": "ORTHOGRAPHIC",
                "ortho_width_cm": float(
                    camera_component.get_editor_property("ortho_width")
                ),
                "show_only_actor_count": len(show_only),
            })
            results.append(record)
        finally:
            if not actor_subsystem.destroy_actor(capture_actor):
                fail("could not destroy transient SceneCapture2D: " + item_id)
    return results


def _write_new_receipt(value: Mapping[str, Any]) -> None:
    try:
        with CAPTURE_RECEIPT.open("xb") as handle:
            handle.write(canonical_json_bytes(value))
    except FileExistsError as error:
        raise CaptureGuardError(
            "refusing to overwrite capture receipt: " + str(CAPTURE_RECEIPT)
        ) from error


def main() -> None:
    ue = _require_unreal()
    map_sha, receipt_sha = required_guard_hashes()
    receipt, contract = load_guarded_install_receipt(map_sha, receipt_sha)
    ensure_output_absent()
    protected_before = protected_snapshot()
    if receipt.get("protected_hashes_after") != protected_before:
        fail("current protected hashes differ from v004 install receipt")
    if _dirty_packages() != {"content": [], "maps": []}:
        fail("editor has dirty packages before v004 capture")

    editor_subsystem = ue.get_editor_subsystem(ue.UnrealEditorSubsystem)
    current_world = editor_subsystem.get_editor_world() if editor_subsystem else None
    current_package = _world_package_name(current_world)
    if current_package == TARGET_MAP:
        fail("run from an unrelated clean world; v004 must start unloaded")
    if not ue.EditorLoadingAndSavingUtils.load_map(TARGET_MAP):
        fail("could not load exact v004 saved map")
    world = editor_subsystem.get_editor_world()
    if _world_package_name(world) != TARGET_MAP:
        fail("v004 target did not become the current editor world")
    if _dirty_packages() != {"content": [], "maps": []}:
        fail("loading v004 dirtied a package")
    if digest(TARGET_FILE) != map_sha:
        fail("loading v004 changed target map bytes")

    actor_subsystem = ue.get_editor_subsystem(ue.EditorActorSubsystem)
    if actor_subsystem is None:
        fail("EditorActorSubsystem is unavailable")
    actors = list(actor_subsystem.get_all_level_actors() or [])
    loaded = validate_loaded_world(world, actors, contract)
    layout_before = {
        path: _layout_material_fingerprint(actor)
        for path, actor in sorted(loaded["actors_by_path"].items())
    }
    visibility_before = {
        str(actor.get_path_name()): _visibility_state(actor)
        for actor in loaded["visuals"]
    }
    visible_paths = {
        str(actor.get_path_name()) for actor in loaded["visible_visuals"]
    }
    residency = _prepare_texture_residency(loaded["visible_visuals"])
    captures: List[Dict[str, Any]] = []
    try:
        for actor in loaded["visuals"]:
            _set_capture_visibility(
                actor, str(actor.get_path_name()) in visible_paths
            )
        show_only = (
            list(loaded["deck_actors"])
            + list(loaded["visible_visuals"])
            + [loaded["runtime_actor"]]
        )
        captures = _capture_saved_cameras(
            world,
            actor_subsystem,
            loaded["cameras_by_label"],
            show_only,
        )
    finally:
        for actor in loaded["visuals"]:
            _restore_visibility(
                actor, visibility_before[str(actor.get_path_name())]
            )

    actors_after = list(actor_subsystem.get_all_level_actors() or [])
    if len(actors_after) != EXPECTED_ACTOR_COUNT:
        fail("v004 actor count changed during transient capture")
    layout_after = {
        str(actor.get_path_name()): _layout_material_fingerprint(actor)
        for actor in actors_after
    }
    if layout_after != layout_before:
        fail("a saved actor layout, label, text, camera, or material changed during capture")
    visibility_after = {
        str(actor.get_path_name()): _visibility_state(actor)
        for actor in loaded["visuals"]
    }
    if visibility_after != visibility_before:
        fail("visual visibility state was not restored after capture")

    dirty_after = _dirty_packages()
    if dirty_after not in (
        {"content": [], "maps": []},
        {"content": [], "maps": [TARGET_MAP]},
    ):
        fail("transient capture dirtied a package outside the target map")
    if digest(TARGET_FILE) != map_sha:
        fail("v004 target map bytes changed during capture")
    if digest(INSTALL_RECEIPT) != receipt_sha:
        fail("v004 install receipt changed during capture")
    protected_after = protected_snapshot()
    if protected_after != protected_before:
        fail("protected map changed during v004 capture")

    fingerprint_sha = hashlib.sha256(
        canonical_json_bytes(layout_after)
    ).hexdigest()
    capture_receipt = {
        "schema": CAPTURE_SCHEMA,
        "status": CAPTURE_STATUS,
        "target_map": TARGET_MAP,
        "target_map_sha256_before": map_sha,
        "target_map_sha256_after": digest(TARGET_FILE),
        "install_receipt": INSTALL_RECEIPT.as_posix(),
        "install_receipt_sha256": receipt_sha,
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "actor_count": len(actors_after),
        "visual_layer_count": EXPECTED_VISUAL_COUNT,
        "base_visual_layer_count": EXPECTED_BASE_VISUAL_COUNT,
        "cargo_layer_count": EXPECTED_CARGO_COUNT,
        "presentation_deck_actor_count": EXPECTED_PRESENTATION_DECK_COUNT,
        "saved_camera_count": EXPECTED_CAMERA_COUNT,
        "new_press_connector_count": EXPECTED_CONNECTOR_COUNT,
        "selected_source_visual_ids": sorted(SELECTED_SOURCE_IDS),
        "selected_cargo_visual_ids": sorted(SELECTED_CARGO_IDS),
        "selected_visual_count": len(visible_paths),
        "resident_material_count": residency["materials"],
        "resident_sprite_texture_count": residency["textures"],
        "loaded_actor_layout_material_fingerprint_sha256": fingerprint_sha,
        "layout_material_fingerprint_unchanged": True,
        "visual_visibility_state_restored": True,
        "deck_style": receipt["deck_style"],
        "captures": captures,
        "capture_resolution": [CAPTURE_WIDTH, CAPTURE_HEIGHT],
        "capture_method": (
            "TRANSIENT_NATIVE_SCENECAPTURE2D_FROM_THREE_SAVED_V004_ORTHOGRAPHIC_"
            "CAMERAS_SHOW_ONLY_SAVED_DECK_SELECTED_VISUALS_AND_NATIVE_PRESENTATION"
        ),
        "dirty_packages_after_capture": dirty_after,
        "map_load_calls": 1,
        "map_save_calls": 0,
        "content_save_calls": 0,
        "saved_actor_layout_mutated": False,
        "saved_actor_material_assignment_mutated": False,
        "project_content_mutated": False,
        "runtime_simulation_validated": False,
        "packaged_build_validated": False,
        "steam_visual_quality_human_approved": False,
    }
    _write_new_receipt(capture_receipt)
    ue.log(
        "PRESSSHOP_2126_OVERHEAD_PRESENTATION_V004_CAPTURE_PASS: "
        + OUTPUT_DIR.as_posix()
    )
    ue.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
