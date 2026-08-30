"""Guarded v004 presentation polish for the Press Shop 2126 overhead map.

This one-shot editor tool clones the immutable, cargo-integrated v003 candidate
to a new v004 candidate.  It edits only the exact v002-authored presentation
boxes, TextRender labels, and cameras named by :func:`build_polish_plan`, then
adds three collision-free press-lane connectors.  Every pre-existing machinery,
runtime, infrastructure, visual-layer, and cargo actor is retained; no machine
or cargo transform is authored here.

The module is importable by ordinary CPython for offline contract tests.
``main`` is the only Unreal entry point.  It never overwrites, deletes, renames,
or saves the v003 source or any protected package.  Fresh visual capture, PIE,
cook, packaged behavior, and Steam evidence remain separate gates.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Sequence, Tuple

try:  # Offline tests intentionally run without Unreal's Python module.
    import unreal  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised by offline tests.
    unreal = None  # type: ignore


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")

SOURCE_ROOT = (
    "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadCargo_v003"
)
SOURCE_MAP = (
    SOURCE_ROOT + "/Maps/LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003"
)
SOURCE_FILE = (
    PROJECT / "Content/LineBoss/Candidates/PressShop"
    / "PressShop2126_OverheadCargo_v003/Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003.umap"
)
SOURCE_FILE_SHA256 = (
    "5eae51f2a7d3e1c72deb4fd455d57a6339dee061840b7d062c5ddf680ab6100f"
)
SOURCE_FILE_BYTES = 1175784
SOURCE_RECEIPT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadCargo_v003"
    / "integration_receipt_v001.json"
)
SOURCE_RECEIPT_SHA256 = (
    "0d58168d05869693aef7aaac8ddd4d5bac3e7e71785b4b4db6d6f32cd6569619"
)
SOURCE_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.overhead_cargo_map_integration_receipt.v001"
)
SOURCE_RECEIPT_STATUS = (
    "PASS_CANDIDATE_CARGO_MAP_INTEGRATED__"
    "S07_INTERMEDIATE_PALLET_COUNTS_DEFERRED__PIE_CAPTURE_PENDING"
)

V002_MAP = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v002/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v002"
)
V002_FILE = (
    PROJECT / "Content/LineBoss/Candidates/PressShop"
    / "PressShop2126_OverheadPresentation_v002/Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v002.umap"
)
V002_FILE_SHA256 = (
    "58fe57f3af0dfcf4021d6bbcd3a52d7d66de22187b561fb2db41becd83023275"
)
V002_RECEIPT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadPresentation_v002"
    / "install_receipt_v001.json"
)
V002_RECEIPT_SHA256 = (
    "eec9ebd5661e835943ceb606ba1569b209b8eb4ee2ab2836bcfb287c8634803d"
)
V002_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.overhead_deck_presentation_install_receipt.v001"
)
V002_RECEIPT_STATUS = (
    "PASS_CANDIDATE_PRESENTATION_MAP_ASSEMBLED__"
    "VISUAL_CAPTURE_AND_RUNTIME_PENDING"
)

CARGO_IMPORT_RECEIPT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadCargo_v001"
    / "import_receipt_v001.json"
)
CARGO_IMPORT_RECEIPT_SHA256 = (
    "34d5dc97701edd624b7690778e4a71f22fe9a23e90bda58de524f3fac66fc9aa"
)
CARGO_IMPORT_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.true_overhead_cargo_import_receipt.v001"
)

TARGET_ROOT = (
    "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPresentation_v004"
)
TARGET_MAP = (
    TARGET_ROOT
    + "/Maps/LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v004"
)
TARGET_ROOT_DISK = (
    PROJECT / "Content/LineBoss/Candidates/PressShop"
    / "PressShop2126_OverheadPresentation_v004"
)
TARGET_FILE = (
    TARGET_ROOT_DISK / "Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v004.umap"
)
INSTALL_RECEIPT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadPresentation_v004"
    / "install_receipt_v001.json"
)
INSTALL_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.overhead_presentation_polish_install_receipt.v001"
)
INSTALL_STATUS = (
    "PASS_CANDIDATE_PRESENTATION_POLISH_APPLIED__"
    "CARGO_PRESERVED__PIE_CAPTURE_PENDING"
)

EXPECTED_GAME_MODE = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
EXPECTED_SOURCE_ACTOR_COUNT = 244
EXPECTED_BASE_VISUAL_LAYER_COUNT = 120
EXPECTED_CARGO_LAYER_COUNT = 26
EXPECTED_COMBINED_VISUAL_LAYER_COUNT = 146
EXPECTED_PRESENTATION_ACTOR_COUNT = 82
EXPECTED_SOURCE_CAMERA_COUNT = 3
EXPECTED_RUNTIME_PRESENTATION_COUNT = 1
EXPECTED_PRESERVED_NONPRESENTATION_COUNT = 162
EXPECTED_EXISTING_MUTATION_COUNT = 38
EXPECTED_NEW_CONNECTOR_COUNT = 3
EXPECTED_FINAL_ACTOR_COUNT = 247

VISUAL_LAYER_CLASS_PATH = (
    "/Script/LineBossCarFactory.LBPressShopOverheadVisualLayerActor"
)
PRESENTATION_ACTOR_CLASS_PATH = (
    "/Script/LineBossCarFactory.LBPressShopOverheadPresentationActor"
)
STATIC_MESH_ACTOR_CLASS_PATH = "/Script/Engine.StaticMeshActor"
TEXT_RENDER_ACTOR_CLASS_PATH = "/Script/Engine.TextRenderActor"
CAMERA_ACTOR_CLASS_PATH = "/Script/Engine.CameraActor"
CUBE_ASSET = "/Engine/BasicShapes/Cube.Cube"

VISUAL_LAYER_TAG = "LB.PressShop.Overhead.VisualLayer.v001"
PRESENTATION_ADAPTER_TAG = "LB.PressShop.OverheadPresentation.v001"
PRESENTATION_PASS_TAG = "LB.PressShop.OverheadDeckPresentation.v002"
PRESENTATION_CAMERA_TAG = "LB.PressShop.OverheadDeck.Camera.v002"
CARGO_MAP_TAG = "LB.PressShop.OverheadCargoMap.v003"
CARGO_SOURCE_TAG = "LB.PressShop.CargoContinuity.v001"
BOOTSTRAP_TAG = "LB.OneFactory.Bootstrap.v001"
BUILD_AUTHORITY_TAG = "LB.OneFactory.MapAuthored.PressBuildAuthority.v001"
PLAYER_START_TAG = "LB.OneFactory.PlayerStart.Management.v001"
VISUAL_ONLY_TAG = "LB.Environment.VisualOnly"
NOT_WIP_TAG = "LB.NotProcessWIP"
ROOFLESS_TAG = "LB.PressShop.RooflessPresentation.v002"
POLISH_TAG = "LB.PressShop.OverheadPresentationPolish.v004"
CAMERA_V004_TAG = "LB.PressShop.OverheadDeck.Camera.v004"

MATERIAL_ROOT = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v002/Materials"
)
DECK_MATERIAL = MATERIAL_ROOT + "/M_CA_MW_PS2126_DeckCharcoal_Unlit_v001"
ZONE_MATERIAL = MATERIAL_ROOT + "/M_CA_MW_PS2126_ZonePaleGreen_Unlit_v001"
CREAM_MATERIAL = MATERIAL_ROOT + "/M_CA_MW_PS2126_FlowCream_Unlit_v001"
YELLOW_MATERIAL = MATERIAL_ROOT + "/M_CA_MW_PS2126_SafetyYellow_Unlit_v001"
TARGET_MATERIAL_ROOT = TARGET_ROOT + "/Materials"
SLATE_DECK_MATERIAL_NAME = "M_CA_MW_PS2126_DeckSlateGreen_Unlit_v004"
SLATE_DECK_MATERIAL = TARGET_MATERIAL_ROOT + "/" + SLATE_DECK_MATERIAL_NAME
SLATE_DECK_SRGB_HEX = "#36534F"
MATERIAL_LOCKS: Mapping[str, Mapping[str, Any]] = {
    DECK_MATERIAL: {
        "sha256": "3989147a929f8df91e04f204a2eb0c7da53f643fbf2be53f235d2be019be5df3",
        "bytes": 5354,
    },
    ZONE_MATERIAL: {
        "sha256": "03e3ea7c2396ce58a9d7cf0120f6243bfce9ba4e79f137e5778337b034e63106",
        "bytes": 5360,
    },
    CREAM_MATERIAL: {
        "sha256": "452162d4e8a155b5906e7f94e83e982a79684a789fcb10fff6a3691f49a8debd",
        "bytes": 5336,
    },
    YELLOW_MATERIAL: {
        "sha256": "0e86ed7f4de19d7752ebea8e8bddd42187b7f2a93599c1dd9aedd43e53d445bd",
        "bytes": 5354,
    },
}

PROTECTED_MAPS: Mapping[str, Tuple[Path, str]] = {
    "source_overhead_cargo_v003": (SOURCE_FILE, SOURCE_FILE_SHA256),
    "source_overhead_presentation_v002": (V002_FILE, V002_FILE_SHA256),
    "builder_authority_v438": (
        PROJECT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap",
        "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    ),
    "onefactory_authority": (
        PROJECT / "Content/LineBoss/Factory/OneFactory/v001/Maps"
        / "LB_MoorcrossWorks_OneFactory_v001.umap",
        "f4e97b33cdfb1f242b2c606a16b4caa05b74b298fdf1b1263d4a4c46d50e8d5c",
    ),
    "overhead_playable_v001": (
        PROJECT / "Content/LineBoss/Candidates/PressShop"
        / "PressShop2126_OverheadPlayable_v001/Maps"
        / "LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001.umap",
        "43020cb3ea7d18a49319da68a04ae1b96d5af0d535c705e947f81d5c005ba7ce",
    ),
    "legacy_steam_v002": (
        PROJECT / "Content/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps"
        / "LB_PressShop_2126_Steam_v002.umap",
        "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
    ),
}

STATION_ROWS: Tuple[Mapping[str, Any], ...] = (
    {"id": "IN01", "center_y": 1600.0, "press_safe": False},
    {"id": "IN02", "center_y": 3260.0, "press_safe": False},
    {"id": "IN03", "center_y": 4260.0, "press_safe": False},
    {"id": "IN04_05", "center_y": 5200.0, "press_safe": False},
    {"id": "S01", "center_y": 6350.0, "press_safe": False},
    {"id": "S02", "center_y": 7500.0, "press_safe": False},
    {"id": "S03", "center_y": 8950.0, "press_safe": True},
    {"id": "S04", "center_y": 10400.0, "press_safe": True},
    {"id": "S05", "center_y": 11850.0, "press_safe": True},
    {"id": "S06", "center_y": 13300.0, "press_safe": True},
    {"id": "S07_INSPECT", "center_y": 14700.0, "press_safe": False},
    {"id": "S07_PALLET", "center_y": 15900.0, "press_safe": False},
)
PRESS_PAD_LENGTHS_Y: Mapping[str, float] = {
    "S03": 1350.0,
    "S04": 1050.0,
    "S05": 1350.0,
    "S06": 1200.0,
}
PROCESS_PAD_X = -8990.75
SOURCE_PAD_DEPTH_X = 2300.0
TARGET_PRESS_PAD_DEPTH_X = 1800.0
PAD_KEY_INSET_X = 32.0
LABEL_INSET_X = 200.0
FLOW_LANE_X = -6500.0
SOURCE_FLOW_WIDTH_X = 950.0
TARGET_FLOW_WIDTH_X = 500.0
FLOW_LANE_CENTER_Y = 8840.218280826943
FLOW_LANE_LENGTH_Y = 15500.0
SOURCE_FLOW_CONNECTOR_Y = (2200.0, 5200.0, 7500.0, 10400.0, 14700.0, 15900.0)
NEW_PRESS_CONNECTOR_Y: Mapping[str, float] = {
    "S03": 8950.0,
    "S05": 11850.0,
    "S06": 13300.0,
}

# Two capture-only probes resolved the saved-camera basis exactly: pitch=-90 is
# the mirrored back face (with either horizontal yaw), while pitch=+90/yaw=0 is
# non-mirrored but upside-down.  Pitch=+90/yaw=180 is horizontal and readable.
TEXT_ROTATION = (90.0, 180.0, 0.0)
CAMERA_ROTATION = (-90.0, 0.0, 0.0)
CAMERA_ASPECT = 16.0 / 9.0
CAMERA_TARGETS: Mapping[str, Mapping[str, Any]] = {
    "overview": {
        "label": "CAM | Press Shop 2126 | roofless deck overview v004",
        "location_cm": [-7730.645880159617, 8840.218280826943, 21712.544],
        "ortho_width_cm": 16800.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.Overview.v004",
    },
    "press_spine": {
        "label": "CAM | Press Shop 2126 | roofless production spine v004",
        "location_cm": [-8450.0, 10450.0, 21712.544],
        "ortho_width_cm": 8900.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.PressSpine.v004",
    },
    "steam_hero": {
        "label": "CAM | Press Shop 2126 | S03-S06 native-scale Steam hero v004",
        "location_cm": [-8990.75, 11125.0, 21712.544],
        "ortho_width_cm": 6300.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.SteamHero.v004",
    },
}

COLLISION_CHANNEL_NAMES = (
    "ECC_WORLD_STATIC",
    "ECC_WORLD_DYNAMIC",
    "ECC_PAWN",
    "ECC_VISIBILITY",
    "ECC_CAMERA",
    "ECC_PHYSICS_BODY",
    "ECC_VEHICLE",
    "ECC_DESTRUCTIBLE",
)
NUMERIC_TOLERANCE = 0.001


class PresentationPolishGuardError(RuntimeError):
    """Fail-closed error for the v004 candidate-only polish lane."""


def fail(message: str) -> None:
    raise PresentationPolishGuardError(
        "PRESSSHOP_2126_OVERHEAD_PRESENTATION_POLISH_V001_FAIL: " + message
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
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def srgb_hex_to_linear(value: str) -> Tuple[float, float, float]:
    """Return the exact Unreal linear RGB authored for an sRGB hex colour."""
    if len(value) != 7 or not value.startswith("#"):
        fail("invalid sRGB hex colour: " + value)
    try:
        srgb = tuple(int(value[index:index + 2], 16) / 255.0 for index in (1, 3, 5))
    except ValueError:
        fail("invalid sRGB hex colour: " + value)

    def channel_to_linear(channel: float) -> float:
        if channel <= 0.04045:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    return tuple(channel_to_linear(channel) for channel in srgb)  # type: ignore[return-value]


def load_locked_json(path: Path, expected_hash: str, context: str) -> Dict[str, Any]:
    if not path.is_file():
        fail(context + " is missing: " + path.as_posix())
    actual = digest(path)
    if actual != expected_hash:
        fail("{} hash changed: {}".format(context, actual))
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail(context + " is unreadable: " + str(exc))
    if not isinstance(value, dict):
        fail(context + " must be a JSON object")
    return value


def _require_list(value: Any, context: str) -> List[Any]:
    if not isinstance(value, list):
        fail(context + " must be a JSON array")
    return value


def _finite_vector(value: Any, size: int, context: str) -> Tuple[float, ...]:
    if not isinstance(value, (list, tuple)) or len(value) != size:
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


def _close(left: Sequence[float], right: Sequence[float]) -> bool:
    return len(left) == len(right) and all(
        abs(float(a) - float(b)) <= NUMERIC_TOLERANCE
        for a, b in zip(left, right)
    )


def _rotation_close(left: Sequence[float], right: Sequence[float]) -> bool:
    """Compare rotations, accepting Unreal's equivalent gimbal readbacks."""
    if len(left) != len(right):
        return False

    def quaternion(values: Sequence[float]) -> Tuple[float, float, float, float]:
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

    left_quat = quaternion(left)
    right_quat = quaternion(right)
    dot = sum(a * b for a, b in zip(left_quat, right_quat))
    return 1.0 - abs(dot) <= NUMERIC_TOLERANCE


def _asset_path(value: Any) -> str | None:
    if value is None:
        return None
    raw = str(value.get_path_name()) if hasattr(value, "get_path_name") else str(value)
    return raw.split(".", 1)[0]


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
    for lock_id, (path, expected) in sorted(PROTECTED_MAPS.items()):
        if not path.is_file():
            fail("protected map is missing: {}: {}".format(lock_id, path))
        actual = digest(path)
        if actual != expected:
            fail("protected map changed: {}: {}".format(lock_id, actual))
        result[lock_id] = actual
    return result


def validate_material_locks() -> Dict[str, str]:
    result: Dict[str, str] = {}
    for asset_path, expected in sorted(MATERIAL_LOCKS.items()):
        disk = virtual_to_uasset(asset_path)
        if not disk.is_file():
            fail("presentation material is missing: " + asset_path)
        actual = digest(disk)
        if disk.stat().st_size != int(expected["bytes"]):
            fail("presentation material byte count changed: " + asset_path)
        if actual != str(expected["sha256"]):
            fail("presentation material hash changed: " + asset_path)
        result[asset_path] = actual
    return result


def validate_cargo_import_receipt() -> Dict[str, Any]:
    receipt = load_locked_json(
        CARGO_IMPORT_RECEIPT,
        CARGO_IMPORT_RECEIPT_SHA256,
        "cargo import receipt",
    )
    exact = {
        "schema": CARGO_IMPORT_RECEIPT_SCHEMA,
        "status": "PASS__ASSETS_IMPORTED__NOT_MAP_INTEGRATED",
        "map_loaded_by_tool": False,
        "map_saved_by_tool": False,
        "native_cpp_modified": False,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("cargo import receipt field changed: " + key)
    hashes = receipt.get("created_uasset_sha256")
    if not isinstance(hashes, dict) or len(hashes) != 30:
        fail("cargo import receipt must lock exactly 30 created uassets")
    if sorted(receipt.get("created_assets", [])) != sorted(hashes):
        fail("cargo import receipt asset/hash inventories differ")
    for asset_path, expected_hash in sorted(hashes.items()):
        disk = virtual_to_uasset(str(asset_path))
        if not disk.is_file() or digest(disk) != str(expected_hash):
            fail("cargo imported uasset is missing or changed: " + str(asset_path))
    return receipt


def validate_v002_receipt() -> Dict[str, Any]:
    receipt = load_locked_json(
        V002_RECEIPT, V002_RECEIPT_SHA256, "v002 presentation receipt"
    )
    exact = {
        "schema": V002_RECEIPT_SCHEMA,
        "status": V002_RECEIPT_STATUS,
        "candidate_only": True,
        "target_map": V002_MAP,
        "target_map_sha256": V002_FILE_SHA256,
        "target_map_bytes": 1097822,
        "created_actor_count": EXPECTED_PRESENTATION_ACTOR_COUNT,
        "created_box_actor_count": 64,
        "created_text_actor_count": 15,
        "created_camera_actor_count": 3,
        "collision_enabled_on_created_presentation": False,
        "roof_created": False,
        "roof_actor_count_after": 0,
        "runtime_validated": False,
        "visual_capture_validated": False,
        "steam_capture_validated": False,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("v002 presentation receipt field changed: " + key)
    if receipt.get("dirty_packages_after_save") != {"content": [], "maps": []}:
        fail("v002 presentation receipt is not clean after save")
    materials = {
        str(row.get("asset")): row
        for row in _require_list(receipt.get("created_materials"), "created materials")
        if isinstance(row, dict)
    }
    if set(materials) != set(MATERIAL_LOCKS):
        fail("v002 presentation material inventory changed")
    for asset_path, lock in MATERIAL_LOCKS.items():
        row = materials[asset_path]
        if row.get("sha256") != lock["sha256"] or row.get("bytes") != lock["bytes"]:
            fail("v002 presentation material receipt lock changed: " + asset_path)
    boxes = _require_list(receipt.get("created_boxes"), "created boxes")
    texts = _require_list(receipt.get("created_texts"), "created texts")
    cameras = _require_list(receipt.get("cameras"), "created cameras")
    if len(boxes) != 64 or len(texts) != 15 or len(cameras) != 3:
        fail("v002 authored presentation inventory changed")
    return receipt


def validate_source_receipt() -> Dict[str, Any]:
    receipt = load_locked_json(
        SOURCE_RECEIPT, SOURCE_RECEIPT_SHA256, "v003 cargo integration receipt"
    )
    exact = {
        "schema": SOURCE_RECEIPT_SCHEMA,
        "status": SOURCE_RECEIPT_STATUS,
        "candidate_only": True,
        "target_map": SOURCE_MAP,
        "target_map_sha256": SOURCE_FILE_SHA256,
        "target_map_bytes": SOURCE_FILE_BYTES,
        "source_map": V002_MAP,
        "source_map_sha256": V002_FILE_SHA256,
        "source_receipt_sha256": V002_RECEIPT_SHA256,
        "source_actor_count": 218,
        "source_actor_mutated_count": 0,
        "source_actor_removed_count": 0,
        "cargo_layer_count": EXPECTED_CARGO_LAYER_COUNT,
        "combined_visual_layer_count": EXPECTED_COMBINED_VISUAL_LAYER_COUNT,
        "existing_camera_actor_count_preserved": EXPECTED_SOURCE_CAMERA_COUNT,
        "existing_deck_presentation_actor_count_preserved": EXPECTED_PRESENTATION_ACTOR_COUNT,
        "existing_runtime_presentation_adapter_count_preserved": 1,
        "collision_enabled_on_cargo_layers": False,
        "protected_authority_map_mutated": False,
        "source_map_mutated": False,
        "native_cpp_modified": False,
        "runtime_validated": False,
        "packaged_build_validated": False,
        "visual_capture_validated": False,
        "steam_capture_validated": False,
        "s07_intermediate_payload_assets_spawned": False,
        "native_extension_required_for_exact_s07_counts": True,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("v003 cargo receipt field changed: " + key)
    if receipt.get("dirty_packages_after_save") != {"content": [], "maps": []}:
        fail("v003 cargo receipt is not clean after save")
    if receipt.get("protected_hashes_before") != receipt.get("protected_hashes_after"):
        fail("v003 cargo receipt does not prove protected hashes stable")
    cargo_layers = _require_list(receipt.get("cargo_layers"), "cargo layers")
    if len(cargo_layers) != EXPECTED_CARGO_LAYER_COUNT:
        fail("v003 cargo layer receipt inventory changed")
    labels: List[str] = []
    for raw in cargo_layers:
        if not isinstance(raw, dict) or not isinstance(raw.get("actor"), dict):
            fail("v003 cargo layer receipt row changed")
        actor = raw["actor"]
        label = str(actor.get("label"))
        labels.append(label)
        tags = set(actor.get("tags", ()))
        if (
            actor.get("class_path") != VISUAL_LAYER_CLASS_PATH
            or actor.get("collision_enabled") is not False
            or CARGO_MAP_TAG not in tags
            or CARGO_SOURCE_TAG not in tags
            or VISUAL_LAYER_TAG not in tags
        ):
            fail("v003 cargo actor contract changed: " + label)
    if len(labels) != len(set(labels)) or any(not label.startswith("CARGO | ") for label in labels):
        fail("v003 cargo labels are missing or duplicated")
    return receipt


def _indexed_rows(rows: Any, context: str) -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for raw in _require_list(rows, context):
        if not isinstance(raw, dict) or not isinstance(raw.get("id"), str):
            fail(context + " contains an invalid row")
        item_id = str(raw["id"])
        if item_id in result:
            fail(context + " contains a duplicate id: " + item_id)
        result[item_id] = copy.deepcopy(raw)
    return result


def _mutation(kind: str, item_id: str, source: Mapping[str, Any], target: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "kind": kind,
        "id": item_id,
        "source": copy.deepcopy(dict(source)),
        "target": copy.deepcopy(dict(target)),
    }


def _box_target(source: Mapping[str, Any], **changes: Any) -> Dict[str, Any]:
    target = copy.deepcopy(dict(source))
    target.update(changes)
    return target


def build_polish_plan(v002_receipt: Mapping[str, Any]) -> Dict[str, Any]:
    boxes = _indexed_rows(v002_receipt.get("created_boxes"), "v002 created boxes")
    texts = _indexed_rows(v002_receipt.get("created_texts"), "v002 created texts")
    cameras = _indexed_rows(v002_receipt.get("cameras"), "v002 cameras")
    mutations: List[Dict[str, Any]] = []

    deck = boxes["DECK_BASE"]
    mutations.append(_mutation(
        "box", "DECK_BASE", deck,
        _box_target(deck, material=SLATE_DECK_MATERIAL),
    ))

    lane = boxes["FLOW_LANE"]
    mutations.append(_mutation(
        "box", "FLOW_LANE", lane,
        _box_target(
            lane,
            dimensions_cm=[TARGET_FLOW_WIDTH_X, FLOW_LANE_LENGTH_Y, 0.6],
            material=DECK_MATERIAL,
        ),
    ))

    flow_min_x = FLOW_LANE_X - TARGET_FLOW_WIDTH_X / 2.0
    flow_max_x = FLOW_LANE_X + TARGET_FLOW_WIDTH_X / 2.0
    flow_min_y = FLOW_LANE_CENTER_Y - FLOW_LANE_LENGTH_Y / 2.0
    flow_max_y = FLOW_LANE_CENTER_Y + FLOW_LANE_LENGTH_Y / 2.0
    flow_edge_targets = {
        "FLOW_EDGE_WEST": ([-6750.0, FLOW_LANE_CENTER_Y, -0.3], [28.0, FLOW_LANE_LENGTH_Y, 0.4]),
        "FLOW_EDGE_EAST": ([-6250.0, FLOW_LANE_CENTER_Y, -0.3], [28.0, FLOW_LANE_LENGTH_Y, 0.4]),
        "FLOW_EDGE_INBOUND": ([FLOW_LANE_X, flow_min_y, -0.3], [TARGET_FLOW_WIDTH_X, 28.0, 0.4]),
        "FLOW_EDGE_OUTBOUND": ([FLOW_LANE_X, flow_max_y, -0.3], [TARGET_FLOW_WIDTH_X, 28.0, 0.4]),
    }
    for item_id, (location, dimensions) in flow_edge_targets.items():
        source = boxes[item_id]
        mutations.append(_mutation(
            "box", item_id, source,
            _box_target(source, location_cm=location, dimensions_cm=dimensions),
        ))

    press_ids = set(PRESS_PAD_LENGTHS_Y)
    for station_id in sorted(press_ids):
        length_y = float(PRESS_PAD_LENGTHS_Y[station_id])
        pad_id = "PAD_" + station_id
        pad = boxes[pad_id]
        mutations.append(_mutation(
            "box", pad_id, pad,
            _box_target(
                pad,
                dimensions_cm=[TARGET_PRESS_PAD_DEPTH_X, length_y, 0.8],
            ),
        ))
        key_id = "PAD_KEY_" + station_id
        key = boxes[key_id]
        key_x = PROCESS_PAD_X - TARGET_PRESS_PAD_DEPTH_X / 2.0 + PAD_KEY_INSET_X
        mutations.append(_mutation(
            "box", key_id, key,
            _box_target(
                key,
                location_cm=[key_x, float(key["location_cm"][1]), -0.3],
                dimensions_cm=[42.0, length_y - 100.0, 0.4],
            ),
        ))

    for index, center_y in enumerate(SOURCE_FLOW_CONNECTOR_Y, start=1):
        item_id = "FLOW_CONNECTOR_{:02d}".format(index)
        source = boxes[item_id]
        is_press = abs(float(center_y) - 10400.0) <= NUMERIC_TOLERANCE
        pad_edge_x = PROCESS_PAD_X + (
            TARGET_PRESS_PAD_DEPTH_X / 2.0 if is_press else SOURCE_PAD_DEPTH_X / 2.0
        )
        width_x = flow_min_x - pad_edge_x
        center_x = pad_edge_x + width_x / 2.0
        mutations.append(_mutation(
            "box", item_id, source,
            _box_target(
                source,
                location_cm=[center_x, float(center_y), -0.25],
                dimensions_cm=[width_x, 58.0, 0.3],
            ),
        ))

    station_index = {str(row["id"]): row for row in STATION_ROWS}
    for item_id, source in sorted(texts.items()):
        target = copy.deepcopy(source)
        target["rotation_deg_pitch_yaw_roll"] = list(TEXT_ROTATION)
        if item_id.startswith("LABEL_"):
            station_id = item_id.removeprefix("LABEL_")
            if station_id in station_index:
                depth = (
                    TARGET_PRESS_PAD_DEPTH_X
                    if bool(station_index[station_id]["press_safe"])
                    else SOURCE_PAD_DEPTH_X
                )
                label_x = PROCESS_PAD_X - depth / 2.0 + LABEL_INSET_X
                target["location_cm"] = [
                    label_x,
                    float(station_index[station_id]["center_y"]),
                    float(source["location_cm"][2]),
                ]
        mutations.append(_mutation("text", item_id, source, target))

    for item_id, target_values in CAMERA_TARGETS.items():
        source = cameras[item_id]
        target = copy.deepcopy(source)
        target.update({
            "label": str(target_values["label"]),
            "location_cm": list(target_values["location_cm"]),
            "rotation_deg_pitch_yaw_roll": list(CAMERA_ROTATION),
            "ortho_width_cm": float(target_values["ortho_width_cm"]),
            "role_tag": str(target_values["role_tag"]),
        })
        mutations.append(_mutation("camera", item_id, source, target))

    press_pad_edge_x = PROCESS_PAD_X + TARGET_PRESS_PAD_DEPTH_X / 2.0
    connector_width_x = flow_min_x - press_pad_edge_x
    connector_center_x = press_pad_edge_x + connector_width_x / 2.0
    new_connectors = []
    for station_id, center_y in NEW_PRESS_CONNECTOR_Y.items():
        new_connectors.append({
            "kind": "box",
            "id": "FLOW_CONNECTOR_PRESS_" + station_id,
            "label": "2126 OVERHEAD FLOW | cream press connector {} v004".format(station_id),
            "role": "FlowConnector",
            "material": CREAM_MATERIAL,
            "location_cm": [connector_center_x, float(center_y), -0.25],
            "dimensions_cm": [connector_width_x, 58.0, 0.3],
            "yaw_deg": 0.0,
        })
    return {
        "mutations": tuple(mutations),
        "new_connectors": tuple(new_connectors),
    }


def validate_polish_plan(plan: Mapping[str, Any]) -> Dict[str, Any]:
    mutations = list(plan.get("mutations", ()))
    new_connectors = list(plan.get("new_connectors", ()))
    if len(mutations) != EXPECTED_EXISTING_MUTATION_COUNT:
        fail("polish plan existing-mutation count changed")
    if len(new_connectors) != EXPECTED_NEW_CONNECTOR_COUNT:
        fail("polish plan new-connector count changed")
    ids = [str(row.get("id")) for row in mutations + new_connectors]
    labels = [
        str(row["source"]["label"]) if "source" in row else str(row.get("label"))
        for row in mutations + new_connectors
    ]
    if len(ids) != len(set(ids)) or len(labels) != len(set(labels)):
        fail("polish plan ids or actor labels are duplicated")
    if any(label.startswith(("VIS | ", "CARGO | ")) for label in labels):
        fail("polish plan illegally selects machinery or cargo")

    by_id = {str(row["id"]): row for row in mutations}
    expected_box_ids = {
        "DECK_BASE",
        "FLOW_LANE",
        "FLOW_EDGE_WEST", "FLOW_EDGE_EAST",
        "FLOW_EDGE_INBOUND", "FLOW_EDGE_OUTBOUND",
        *("PAD_" + item_id for item_id in PRESS_PAD_LENGTHS_Y),
        *("PAD_KEY_" + item_id for item_id in PRESS_PAD_LENGTHS_Y),
        *("FLOW_CONNECTOR_{:02d}".format(index) for index in range(1, 7)),
    }
    expected_text_ids = {
        "LABEL_" + str(row["id"]) for row in STATION_ROWS
    } | {"LABEL_TITLE", "LABEL_INBOUND", "LABEL_OUTBOUND"}
    expected_camera_ids = set(CAMERA_TARGETS)
    if {row["id"] for row in mutations if row["kind"] == "box"} != expected_box_ids:
        fail("polish plan box selector changed")
    if {row["id"] for row in mutations if row["kind"] == "text"} != expected_text_ids:
        fail("polish plan text selector changed")
    if {row["id"] for row in mutations if row["kind"] == "camera"} != expected_camera_ids:
        fail("polish plan camera selector changed")

    deck_source = by_id["DECK_BASE"]["source"]
    deck = by_id["DECK_BASE"]["target"]
    if deck != _box_target(deck_source, material=SLATE_DECK_MATERIAL):
        fail("full deck no longer has the reviewed Cairnwell slate-green material")

    lane_source = by_id["FLOW_LANE"]["source"]
    lane = by_id["FLOW_LANE"]["target"]
    if (
        lane != _box_target(
            lane_source,
            dimensions_cm=[TARGET_FLOW_WIDTH_X, FLOW_LANE_LENGTH_Y, 0.6],
            material=DECK_MATERIAL,
        )
        or not _close(lane["location_cm"], [FLOW_LANE_X, FLOW_LANE_CENTER_Y, -0.45])
        or not _close(lane["dimensions_cm"], [500.0, 15500.0, 0.6])
        or _asset_path(lane["material"]) != DECK_MATERIAL
    ):
        fail("flow lane no longer has the reviewed narrow charcoal hierarchy")

    flow_min_y = FLOW_LANE_CENTER_Y - FLOW_LANE_LENGTH_Y / 2.0
    flow_max_y = FLOW_LANE_CENTER_Y + FLOW_LANE_LENGTH_Y / 2.0
    edge_contract = {
        "FLOW_EDGE_WEST": ([-6750.0, FLOW_LANE_CENTER_Y, -0.3], [28.0, FLOW_LANE_LENGTH_Y, 0.4]),
        "FLOW_EDGE_EAST": ([-6250.0, FLOW_LANE_CENTER_Y, -0.3], [28.0, FLOW_LANE_LENGTH_Y, 0.4]),
        "FLOW_EDGE_INBOUND": ([FLOW_LANE_X, flow_min_y, -0.3], [TARGET_FLOW_WIDTH_X, 28.0, 0.4]),
        "FLOW_EDGE_OUTBOUND": ([FLOW_LANE_X, flow_max_y, -0.3], [TARGET_FLOW_WIDTH_X, 28.0, 0.4]),
    }
    for item_id, (location, dimensions) in edge_contract.items():
        source = by_id[item_id]["source"]
        target = by_id[item_id]["target"]
        if (
            target != _box_target(source, location_cm=location, dimensions_cm=dimensions)
            or _asset_path(target["material"]) != YELLOW_MATERIAL
        ):
            fail("reviewed safety-yellow flow edge changed: " + item_id)

    station_index = {str(row["id"]): row for row in STATION_ROWS}
    for item_id in expected_text_ids:
        source = by_id[item_id]["source"]
        target = by_id[item_id]["target"]
        expected_target = copy.deepcopy(source)
        expected_target["rotation_deg_pitch_yaw_roll"] = list(TEXT_ROTATION)
        station_id = item_id.removeprefix("LABEL_")
        if station_id in station_index:
            depth = (
                TARGET_PRESS_PAD_DEPTH_X
                if bool(station_index[station_id]["press_safe"])
                else SOURCE_PAD_DEPTH_X
            )
            expected_target["location_cm"] = [
                PROCESS_PAD_X - depth / 2.0 + LABEL_INSET_X,
                float(station_index[station_id]["center_y"]),
                float(source["location_cm"][2]),
            ]
        if target != expected_target:
            fail("reviewed TextRender content or inset changed: " + item_id)
        if not _close(target["rotation_deg_pitch_yaw_roll"], TEXT_ROTATION):
            fail("text rotation is not the readable saved-camera transform: " + item_id)
        if abs(float(target["rotation_deg_pitch_yaw_roll"][1])) <= NUMERIC_TOLERANCE:
            fail("yaw zero is mirrored in the saved-camera text basis")

    ordered_press = []
    for station_id, length_y in PRESS_PAD_LENGTHS_Y.items():
        station = station_index[station_id]
        pad_source = by_id["PAD_" + station_id]["source"]
        pad = by_id["PAD_" + station_id]["target"]
        key_source = by_id["PAD_KEY_" + station_id]["source"]
        key = by_id["PAD_KEY_" + station_id]["target"]
        expected_pad = _box_target(
            pad_source,
            dimensions_cm=[TARGET_PRESS_PAD_DEPTH_X, length_y, 0.8],
        )
        key_x = PROCESS_PAD_X - TARGET_PRESS_PAD_DEPTH_X / 2.0 + PAD_KEY_INSET_X
        expected_key = _box_target(
            key_source,
            location_cm=[key_x, float(key_source["location_cm"][1]), -0.3],
            dimensions_cm=[42.0, length_y - 100.0, 0.4],
        )
        if (
            pad != expected_pad
            or not _close(pad["location_cm"], [PROCESS_PAD_X, station["center_y"], -0.6])
            or _asset_path(pad["material"]) != ZONE_MATERIAL
        ):
            fail("reviewed press-pad dimensions changed: " + station_id)
        if key != expected_key or _asset_path(key["material"]) != YELLOW_MATERIAL:
            fail("reviewed station-key dimensions changed: " + station_id)
        center_y = float(pad["location_cm"][1])
        ordered_press.append((center_y - length_y / 2.0, center_y + length_y / 2.0))
    ordered_press.sort()
    if any(right[0] - left[1] < 150.0 for left, right in zip(ordered_press, ordered_press[1:])):
        fail("tightened press pads lost their safe dark gutter")

    flow_min_x = FLOW_LANE_X - TARGET_FLOW_WIDTH_X / 2.0
    press_connector_y = set()
    for index, center_y in enumerate(SOURCE_FLOW_CONNECTOR_Y, start=1):
        item_id = "FLOW_CONNECTOR_{:02d}".format(index)
        source = by_id[item_id]["source"]
        target = by_id[item_id]["target"]
        is_press = abs(float(center_y) - 10400.0) <= NUMERIC_TOLERANCE
        pad_edge_x = PROCESS_PAD_X + (
            TARGET_PRESS_PAD_DEPTH_X / 2.0 if is_press else SOURCE_PAD_DEPTH_X / 2.0
        )
        width_x = flow_min_x - pad_edge_x
        center_x = pad_edge_x + width_x / 2.0
        expected_target = _box_target(
            source,
            location_cm=[center_x, float(center_y), -0.25],
            dimensions_cm=[width_x, 58.0, 0.3],
        )
        if target != expected_target or _asset_path(target["material"]) != CREAM_MATERIAL:
            fail("reviewed existing flow connector changed: " + item_id)
        if is_press:
            press_connector_y.add(float(center_y))

    press_pad_edge_x = PROCESS_PAD_X + TARGET_PRESS_PAD_DEPTH_X / 2.0
    press_width_x = flow_min_x - press_pad_edge_x
    press_center_x = press_pad_edge_x + press_width_x / 2.0
    expected_new_ids = {"FLOW_CONNECTOR_PRESS_" + station_id for station_id in NEW_PRESS_CONNECTOR_Y}
    if {str(row.get("id")) for row in new_connectors} != expected_new_ids:
        fail("new press connector selector changed")
    for row in new_connectors:
        station_id = str(row["id"]).removeprefix("FLOW_CONNECTOR_PRESS_")
        center_y = float(NEW_PRESS_CONNECTOR_Y[station_id])
        expected_row = {
            "kind": "box",
            "id": "FLOW_CONNECTOR_PRESS_" + station_id,
            "label": "2126 OVERHEAD FLOW | cream press connector {} v004".format(station_id),
            "role": "FlowConnector",
            "material": CREAM_MATERIAL,
            "location_cm": [press_center_x, center_y, -0.25],
            "dimensions_cm": [press_width_x, 58.0, 0.3],
            "yaw_deg": 0.0,
        }
        if row != expected_row:
            fail("reviewed new press connector changed: " + station_id)
        press_connector_y.add(center_y)
    if press_connector_y != {8950.0, 10400.0, 11850.0, 13300.0}:
        fail("press connectors do not cover S03-S06 exactly")

    for item_id, expected in CAMERA_TARGETS.items():
        source = by_id[item_id]["source"]
        target = by_id[item_id]["target"]
        expected_target = copy.deepcopy(source)
        expected_target.update({
            "label": str(expected["label"]),
            "location_cm": list(expected["location_cm"]),
            "rotation_deg_pitch_yaw_roll": list(CAMERA_ROTATION),
            "ortho_width_cm": float(expected["ortho_width_cm"]),
            "role_tag": str(expected["role_tag"]),
        })
        if (
            target != expected_target
            or not _close(target["rotation_deg_pitch_yaw_roll"], CAMERA_ROTATION)
            or not _close(target["location_cm"], expected["location_cm"])
            or abs(float(target["ortho_width_cm"]) - float(expected["ortho_width_cm"]))
            > NUMERIC_TOLERANCE
        ):
            fail("reviewed camera contract changed: " + item_id)
    return {
        "existing_mutation_count": len(mutations),
        "new_connector_count": len(new_connectors),
        "box_mutation_count": sum(row["kind"] == "box" for row in mutations),
        "text_mutation_count": sum(row["kind"] == "text" for row in mutations),
        "camera_mutation_count": sum(row["kind"] == "camera" for row in mutations),
        "slate_deck_material": {
            "asset": SLATE_DECK_MATERIAL,
            "srgb_hex": SLATE_DECK_SRGB_HEX,
            "linear_rgb": list(srgb_hex_to_linear(SLATE_DECK_SRGB_HEX)),
            "shading_model": "UNLIT",
        },
        "readable_text_rotation_deg_pitch_yaw_roll": list(TEXT_ROTATION),
        "capture_rejected_text_rotations": {
            "mirrored_backface": [-90.0, 180.0, 0.0],
            "horizontal_mirrored": [-90.0, 0.0, 0.0],
            "nonmirrored_upside_down": [90.0, 0.0, 0.0],
        },
        "safe_tightened_pad_ids": sorted(PRESS_PAD_LENGTHS_Y),
        "press_connector_y_cm": sorted(press_connector_y),
        "camera_targets": copy.deepcopy(dict(CAMERA_TARGETS)),
    }


def validate_offline_contract() -> Dict[str, Any]:
    if not SOURCE_FILE.is_file():
        fail("frozen v003 source map is missing")
    if SOURCE_FILE.stat().st_size != SOURCE_FILE_BYTES:
        fail("frozen v003 source map byte count changed")
    if digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
        fail("frozen v003 source map hash changed")
    source_receipt = validate_source_receipt()
    v002_receipt = validate_v002_receipt()
    cargo_import_receipt = validate_cargo_import_receipt()
    material_hashes = validate_material_locks()
    protected_hashes = protected_snapshot()
    plan = build_polish_plan(v002_receipt)
    validation = validate_polish_plan(plan)
    return {
        "source_receipt": source_receipt,
        "v002_receipt": v002_receipt,
        "cargo_import_receipt": cargo_import_receipt,
        "material_hashes": material_hashes,
        "protected_hashes": protected_hashes,
        "plan": plan,
        "validation": validation,
    }


def _require_unreal() -> Any:
    if unreal is None:
        fail("main must run inside UnrealEditor Python")
    return unreal


def _create_slate_deck_material() -> Tuple[Any, Dict[str, Any]]:
    """Create the sole v004 content asset: an exact #36534F unlit deck."""
    ue = _require_unreal()
    if ue.EditorAssetLibrary.does_asset_exist(SLATE_DECK_MATERIAL):
        fail("v004 slate deck material already exists")
    material = ue.AssetToolsHelpers.get_asset_tools().create_asset(
        SLATE_DECK_MATERIAL_NAME,
        TARGET_MATERIAL_ROOT,
        ue.Material,
        ue.MaterialFactoryNew(),
    )
    if not isinstance(material, ue.Material):
        fail("could not create v004 slate deck material")
    material.set_editor_property("shading_model", ue.MaterialShadingModel.MSM_UNLIT)
    linear_rgb = srgb_hex_to_linear(SLATE_DECK_SRGB_HEX)
    expression = ue.MaterialEditingLibrary.create_material_expression(
        material, ue.MaterialExpressionConstant3Vector, -220, 0
    )
    if expression is None:
        fail("could not create slate deck colour expression")
    expression.set_editor_property(
        "constant",
        ue.LinearColor(linear_rgb[0], linear_rgb[1], linear_rgb[2], 1.0),
    )
    if not ue.MaterialEditingLibrary.connect_material_property(
        expression, "", ue.MaterialProperty.MP_EMISSIVE_COLOR
    ):
        fail("could not connect slate deck emissive colour")

    # Recompile once before the stabilization save, then compile the now-saved
    # package once more before the final save.  RecompileMaterial is the
    # synchronous material-editing boundary; saving immediately after only its
    # first invocation left the package dirty in the commandlet lane.
    initial_compile_errors = [
        str(value)
        for value in (ue.MaterialEditingLibrary.recompile_material(material) or [])
    ]
    if initial_compile_errors:
        fail("initial slate deck material compile failed: " + repr(initial_compile_errors))
    if not ue.EditorAssetLibrary.save_loaded_asset(
        material, only_if_is_dirty=False
    ):
        fail("could not perform slate deck material stabilization save")
    final_compile_errors = [
        str(value)
        for value in (ue.MaterialEditingLibrary.recompile_material(material) or [])
    ]
    if final_compile_errors:
        fail("final slate deck material compile failed: " + repr(final_compile_errors))

    final_save_attempts = 0
    material_dirty_after_final_save = True
    while final_save_attempts < 2 and material_dirty_after_final_save:
        final_save_attempts += 1
        if not ue.EditorAssetLibrary.save_loaded_asset(
            material, only_if_is_dirty=False
        ):
            fail(
                "could not perform slate deck material final save attempt {}".format(
                    final_save_attempts
                )
            )
        dirty_after_attempt = dirty_package_paths()
        material_dirty_after_final_save = (
            SLATE_DECK_MATERIAL in dirty_after_attempt["content"]
        )
    if material_dirty_after_final_save:
        fail(
            "slate deck material remained dirty after bounded final saves; actual_dirty="
            + json.dumps(dirty_after_attempt, sort_keys=True, separators=(",", ":"))
        )
    disk = virtual_to_uasset(SLATE_DECK_MATERIAL)
    if not disk.is_file():
        fail("v004 slate deck material package is missing after save")
    if _asset_path(material) != SLATE_DECK_MATERIAL:
        fail("v004 slate deck material registry path changed")
    return material, {
        "asset": SLATE_DECK_MATERIAL,
        "srgb_hex": SLATE_DECK_SRGB_HEX,
        "linear_rgb": list(linear_rgb),
        "shading_model": "UNLIT",
        "material_recompile_passes": 2,
        "final_save_attempts": final_save_attempts,
        "sha256": digest(disk),
        "bytes": disk.stat().st_size,
    }


def _editor_world() -> Any:
    ue = _require_unreal()
    subsystem = ue.get_editor_subsystem(ue.UnrealEditorSubsystem)
    if subsystem is None or subsystem.get_editor_world() is None:
        fail("Unreal editor world is unavailable")
    return subsystem.get_editor_world()


def _actor_subsystem() -> Any:
    ue = _require_unreal()
    subsystem = ue.get_editor_subsystem(ue.EditorActorSubsystem)
    if subsystem is None:
        fail("EditorActorSubsystem is unavailable")
    return subsystem


def _level_subsystem() -> Any:
    ue = _require_unreal()
    subsystem = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
    if subsystem is None:
        fail("LevelEditorSubsystem is unavailable")
    return subsystem


def _world_package_name(world: Any) -> str:
    return str(world.get_outermost().get_name()) if world else ""


def _world_game_mode_path(world: Any) -> str | None:
    if world is None:
        return None
    game_mode = world.get_world_settings().get_editor_property("default_game_mode")
    return str(game_mode.get_path_name()) if game_mode else None


def dirty_package_paths() -> Dict[str, List[str]]:
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


def _assert_dirty_packages(
    expected: Mapping[str, Sequence[str]], context: str
) -> Dict[str, List[str]]:
    actual = dirty_package_paths()
    normalised_expected = {
        "content": sorted(str(value) for value in expected.get("content", ())),
        "maps": sorted(str(value) for value in expected.get("maps", ())),
    }
    if actual != normalised_expected:
        fail(
            "{}; expected_dirty={}; actual_dirty={}".format(
                context,
                json.dumps(normalised_expected, sort_keys=True, separators=(",", ":")),
                json.dumps(actual, sort_keys=True, separators=(",", ":")),
            )
        )
    return actual


def _validate_post_slate_dirty_packages(
    actual: Mapping[str, Sequence[str]],
) -> Dict[str, List[str]]:
    """Accept only the two safe states observed after the material save."""
    normalised_actual = {
        "content": sorted(str(value) for value in actual.get("content", ())),
        "maps": sorted(str(value) for value in actual.get("maps", ())),
    }
    allowed = (
        {"content": [], "maps": []},
        {"content": [], "maps": [TARGET_MAP]},
    )
    if normalised_actual not in allowed:
        fail(
            "unsafe dirty packages after slate material save; allowed_dirty={}; "
            "actual_dirty={}".format(
                json.dumps(allowed, sort_keys=True, separators=(",", ":")),
                json.dumps(normalised_actual, sort_keys=True, separators=(",", ":")),
            )
        )
    return normalised_actual


def _vector(values: Sequence[float]) -> Any:
    ue = _require_unreal()
    return ue.Vector(x=float(values[0]), y=float(values[1]), z=float(values[2]))


def _rotator(values: Sequence[float]) -> Any:
    ue = _require_unreal()
    return ue.Rotator(
        pitch=float(values[0]), yaw=float(values[1]), roll=float(values[2])
    )


def _actor_transform_record(actor: Any) -> Dict[str, Any]:
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


def _actor_fingerprint_record(actor: Any) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "path": str(actor.get_path_name()),
        "label": str(actor.get_actor_label()),
        "class_path": str(actor.get_class().get_path_name()),
        "tags": sorted(str(tag) for tag in list(actor.tags or [])),
        "actor_collision_enabled": bool(actor.get_actor_enable_collision()),
        **_actor_transform_record(actor),
    }
    component = _safe_property(actor, ("static_mesh_component",))
    if component is not None:
        mesh = _safe_property(component, ("static_mesh",))
        material_count = int(component.get_num_materials())
        record["static_mesh_component"] = {
            "static_mesh": _asset_path(mesh),
            "materials": [
                _asset_path(component.get_material(index))
                for index in range(material_count)
            ],
            "visible": bool(component.is_visible()),
            "hidden_in_game": bool(component.get_editor_property("hidden_in_game")),
            "collision_enabled": str(component.get_collision_enabled()),
            "collision_profile": str(component.get_collision_profile_name()),
        }
    text_component = _safe_property(actor, ("text_render",))
    if text_component is not None:
        record["text_render"] = {
            "text": str(text_component.get_editor_property("text")),
            "world_size": float(text_component.get_editor_property("world_size")),
            "horizontal_alignment": str(text_component.get_editor_property("horizontal_alignment")),
            "vertical_alignment": str(text_component.get_editor_property("vertical_alignment")),
            "text_render_color": str(text_component.get_editor_property("text_render_color")),
        }
    camera_component = _safe_property(actor, ("camera_component",))
    if camera_component is not None:
        record["camera_component"] = {
            "projection_mode": str(camera_component.get_editor_property("projection_mode")),
            "ortho_width": float(camera_component.get_editor_property("ortho_width")),
            "aspect_ratio": float(camera_component.get_editor_property("aspect_ratio")),
            "constrain_aspect_ratio": bool(camera_component.get_editor_property("constrain_aspect_ratio")),
        }
    if record["class_path"] == VISUAL_LAYER_CLASS_PATH:
        metadata = {}
        property_names = {
            "LayerId": ("layer_id", "LayerId"),
            "AssemblyId": ("assembly_id", "AssemblyId"),
            "MachineId": ("machine_id", "MachineId"),
            "LayerRole": ("layer_role", "LayerRole"),
            "StateId": ("state_id", "StateId"),
            "MotionChannel": ("motion_channel", "MotionChannel"),
            "bHasMotionRange": ("has_motion_range", "bHasMotionRange"),
            "MotionStart": ("motion_start", "MotionStart"),
            "MotionEnd": ("motion_end", "MotionEnd"),
            "SequenceFrameIndex": ("sequence_frame_index", "SequenceFrameIndex"),
            "SequenceFrameCount": ("sequence_frame_count", "SequenceFrameCount"),
            "bSequenceLoops": ("sequence_loops", "bSequenceLoops"),
        }
        for key, names in property_names.items():
            metadata[key] = str(_safe_property(actor, names))
        record["visual_metadata"] = metadata
    return record


def _fingerprint_hash(records: Mapping[str, Mapping[str, Any]]) -> str:
    return hashlib.sha256(canonical_json_bytes(dict(sorted(records.items())))).hexdigest()


def _records_by_path(actors: Iterable[Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(actor.get_path_name()): _actor_fingerprint_record(actor)
        for actor in actors
    }


def _count_tag(records: Iterable[Mapping[str, Any]], tag: str) -> int:
    return sum(1 for row in records if tag in set(row.get("tags", ())))


def validate_source_actor_inventory(actors: Sequence[Any]) -> Dict[str, Any]:
    records = [_actor_fingerprint_record(actor) for actor in actors]
    if len(records) != EXPECTED_SOURCE_ACTOR_COUNT:
        fail("v003 source actor count changed")
    exact_tags = {
        VISUAL_LAYER_TAG: EXPECTED_COMBINED_VISUAL_LAYER_COUNT,
        CARGO_MAP_TAG: EXPECTED_CARGO_LAYER_COUNT,
        CARGO_SOURCE_TAG: EXPECTED_CARGO_LAYER_COUNT,
        PRESENTATION_PASS_TAG: EXPECTED_PRESENTATION_ACTOR_COUNT,
        PRESENTATION_CAMERA_TAG: EXPECTED_SOURCE_CAMERA_COUNT,
        PRESENTATION_ADAPTER_TAG: EXPECTED_RUNTIME_PRESENTATION_COUNT,
        BOOTSTRAP_TAG: 1,
        BUILD_AUTHORITY_TAG: 1,
        PLAYER_START_TAG: 1,
    }
    for tag, expected in exact_tags.items():
        if _count_tag(records, tag) != expected:
            fail("v003 source actor tag count changed: " + tag)
    cargo = [row for row in records if CARGO_MAP_TAG in set(row["tags"])]
    if (
        len(cargo) != EXPECTED_CARGO_LAYER_COUNT
        or any(row["class_path"] != VISUAL_LAYER_CLASS_PATH for row in cargo)
        or any(not row["label"].startswith("CARGO | ") for row in cargo)
    ):
        fail("v003 cargo actor inventory changed")
    presentation = [
        row for row in records if PRESENTATION_PASS_TAG in set(row["tags"])
    ]
    if len(presentation) != EXPECTED_PRESENTATION_ACTOR_COUNT:
        fail("v003 presentation actor inventory changed")
    return {
        "records": records,
        "cargo_labels": sorted(row["label"] for row in cargo),
        "presentation_labels": sorted(row["label"] for row in presentation),
    }


def _component_material_path(component: Any, index: int = 0) -> str | None:
    return _asset_path(component.get_material(index))


def _assert_source_actor(actor: Any, mutation: Mapping[str, Any]) -> None:
    source = mutation["source"]
    kind = str(mutation["kind"])
    if str(actor.get_actor_label()) != str(source["label"]):
        fail("source presentation label changed: " + str(mutation["id"]))
    tags = {str(tag) for tag in list(actor.tags or [])}
    if PRESENTATION_PASS_TAG not in tags:
        fail("source presentation tag missing: " + str(mutation["id"]))
    transform = _actor_transform_record(actor)
    if kind == "box":
        if str(actor.get_class().get_path_name()) != STATIC_MESH_ACTOR_CLASS_PATH:
            fail("source presentation box class changed: " + str(mutation["id"]))
        expected_rotation = [0.0, float(source["yaw_deg"]), 0.0]
        expected_scale = [float(value) / 100.0 for value in source["dimensions_cm"]]
        if (
            not _close(transform["location_cm"], source["location_cm"])
            or not _rotation_close(transform["rotation_deg_pitch_yaw_roll"], expected_rotation)
            or not _close(transform["scale3d"], expected_scale)
        ):
            fail("source presentation box transform changed: " + str(mutation["id"]))
        component = actor.get_editor_property("static_mesh_component")
        if (
            component is None
            or _asset_path(component.get_editor_property("static_mesh"))
            != _asset_path(CUBE_ASSET)
            or _component_material_path(component) != _asset_path(source["material"])
        ):
            fail("source presentation box asset assignment changed: " + str(mutation["id"]))
    elif kind == "text":
        if str(actor.get_class().get_path_name()) != TEXT_RENDER_ACTOR_CLASS_PATH:
            fail("source TextRender class changed: " + str(mutation["id"]))
        if (
            not _close(transform["location_cm"], source["location_cm"])
            or not _rotation_close(transform["rotation_deg_pitch_yaw_roll"], source["rotation_deg_pitch_yaw_roll"])
        ):
            fail("source TextRender transform changed: " + str(mutation["id"]))
        component = actor.get_editor_property("text_render")
        if (
            component is None
            or str(component.get_editor_property("text")) != str(source["text"])
            or abs(float(component.get_editor_property("world_size")) - float(source["world_size_cm"]))
            > NUMERIC_TOLERANCE
        ):
            fail("source TextRender content changed: " + str(mutation["id"]))
    elif kind == "camera":
        if str(actor.get_class().get_path_name()) != CAMERA_ACTOR_CLASS_PATH:
            fail("source camera class changed: " + str(mutation["id"]))
        component = actor.get_editor_property("camera_component")
        if (
            component is None
            or not _close(transform["location_cm"], source["location_cm"])
            or not _rotation_close(transform["rotation_deg_pitch_yaw_roll"], source["rotation_deg_pitch_yaw_roll"])
            or abs(float(component.get_editor_property("ortho_width")) - float(source["ortho_width_cm"]))
            > NUMERIC_TOLERANCE
        ):
            fail("source camera contract changed: " + str(mutation["id"]))
    else:
        fail("unknown polish mutation kind: " + kind)


def _append_unique_tags(actor: Any, values: Sequence[str]) -> None:
    ue = _require_unreal()
    tags = list(actor.tags or [])
    existing = {str(tag) for tag in tags}
    for value in values:
        if value not in existing:
            tags.append(ue.Name(value))
            existing.add(value)
    actor.tags = tags


def _apply_box_mutation(actor: Any, target: Mapping[str, Any], materials: Mapping[str, Any]) -> None:
    actor.set_actor_location(_vector(target["location_cm"]), False, False)
    actor.set_actor_rotation(_rotator([0.0, float(target["yaw_deg"]), 0.0]), False)
    actor.set_actor_scale3d(_vector([
        float(target["dimensions_cm"][0]) / 100.0,
        float(target["dimensions_cm"][1]) / 100.0,
        float(target["dimensions_cm"][2]) / 100.0,
    ]))
    component = actor.get_editor_property("static_mesh_component")
    material_path = _asset_path(target["material"])
    if material_path not in materials:
        fail("target box material was not preflighted: " + str(material_path))
    component.set_material(0, materials[str(material_path)])
    if _component_material_path(component) != material_path:
        fail("target box material readback failed: " + str(target["id"]))


def _apply_text_mutation(actor: Any, target: Mapping[str, Any]) -> None:
    actor.set_actor_location(_vector(target["location_cm"]), False, False)
    actor.set_actor_rotation(_rotator(target["rotation_deg_pitch_yaw_roll"]), False)


def _apply_camera_mutation(actor: Any, target: Mapping[str, Any]) -> None:
    ue = _require_unreal()
    actor.set_actor_label(str(target["label"]), mark_dirty=True)
    actor.set_actor_location(_vector(target["location_cm"]), False, False)
    actor.set_actor_rotation(_rotator(target["rotation_deg_pitch_yaw_roll"]), False)
    component = actor.get_editor_property("camera_component")
    component.set_editor_property("projection_mode", ue.CameraProjectionMode.ORTHOGRAPHIC)
    component.set_editor_property("ortho_width", float(target["ortho_width_cm"]))
    component.set_editor_property("aspect_ratio", CAMERA_ASPECT)
    component.set_editor_property("constrain_aspect_ratio", True)
    _append_unique_tags(actor, [CAMERA_V004_TAG, str(target["role_tag"])])


def _verify_no_collision(actor: Any, component: Any, item_id: str) -> Dict[str, Any]:
    ue = _require_unreal()
    actor.set_actor_enable_collision(False)
    # This project's named NoCollision profile carries blocking response
    # metadata.  Apply it first, then override the BodyInstance responses and
    # enabled state.  Those explicit overrides truthfully change the profile
    # readback to Custom while producing the strict inert state verified below.
    component.set_collision_profile_name(ue.Name("NoCollision"), update_overlaps=False)
    component.set_collision_response_to_all_channels(ue.CollisionResponseType.ECR_IGNORE)
    for channel_name in COLLISION_CHANNEL_NAMES:
        component.set_collision_response_to_channel(
            getattr(ue.CollisionChannel, channel_name),
            ue.CollisionResponseType.ECR_IGNORE,
        )
    component.set_collision_enabled(ue.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("generate_overlap_events", False)
    component.set_editor_property("can_ever_affect_navigation", False)
    if bool(actor.get_actor_enable_collision()):
        fail("new connector retained actor collision: " + item_id)
    enabled = str(component.get_collision_enabled())
    if "NO_COLLISION" not in enabled.upper():
        fail("new connector retained component collision: " + item_id)
    profile = str(component.get_collision_profile_name())
    normalised_profile = "".join(
        character.lower() for character in profile if character.isalnum()
    )
    if normalised_profile not in {"nocollision", "custom"}:
        fail("new connector profile is neither NoCollision nor Custom: " + item_id)
    ignored = []
    for channel_name in COLLISION_CHANNEL_NAMES:
        channel = getattr(ue.CollisionChannel, channel_name)
        response = str(component.get_collision_response_to_channel(channel))
        if "ECR_IGNORE" not in response.upper():
            fail("new connector does not ignore {}: {}".format(channel_name, item_id))
        ignored.append(channel_name)
    return {
        "actor_collision_enabled": False,
        "component_collision_enabled": enabled,
        "collision_profile": profile,
        "profile_acceptance": (
            "NativeNoCollisionWithIgnoreAll"
            if normalised_profile == "nocollision"
            else "CustomWithNoCollisionAndIgnoreAll"
        ),
        "ignored_channels": ignored,
    }


def _spawn_connector(
    actor_subsystem: Any,
    cube: Any,
    cream_material: Any,
    spec: Mapping[str, Any],
) -> Tuple[Any, Dict[str, Any]]:
    ue = _require_unreal()
    actor = actor_subsystem.spawn_actor_from_class(
        ue.StaticMeshActor,
        _vector(spec["location_cm"]),
        _rotator([0.0, float(spec["yaw_deg"]), 0.0]),
        transient=False,
    )
    if actor is None:
        fail("could not spawn new press connector: " + str(spec["id"]))
    actor.set_actor_label(str(spec["label"]), mark_dirty=True)
    actor.tags = [
        ue.Name(PRESENTATION_PASS_TAG),
        ue.Name(VISUAL_ONLY_TAG),
        ue.Name(NOT_WIP_TAG),
        ue.Name(ROOFLESS_TAG),
        ue.Name(POLISH_TAG),
        ue.Name("LB.PressShop.OverheadDeck.Role.FlowConnector"),
    ]
    component = actor.get_editor_property("static_mesh_component")
    if component is None or not component.set_static_mesh(cube):
        fail("could not assign cube to new press connector: " + str(spec["id"]))
    actor.set_actor_scale3d(_vector([
        float(spec["dimensions_cm"][0]) / 100.0,
        float(spec["dimensions_cm"][1]) / 100.0,
        float(spec["dimensions_cm"][2]) / 100.0,
    ]))
    component.set_material(0, cream_material)
    component.set_editor_property("cast_shadow", False)
    collision = _verify_no_collision(actor, component, str(spec["id"]))
    if _component_material_path(component) != CREAM_MATERIAL:
        fail("new press connector material readback failed: " + str(spec["id"]))
    return actor, {
        **copy.deepcopy(dict(spec)),
        "actor_path": str(actor.get_path_name()),
        "collision": "NoCollision",
        "collision_readback": collision,
        "cast_shadow": False,
    }


def _verify_target_actor(actor: Any, mutation: Mapping[str, Any]) -> Dict[str, Any]:
    target = mutation["target"]
    kind = str(mutation["kind"])
    transform = _actor_transform_record(actor)
    tags = {str(tag) for tag in list(actor.tags or [])}
    if POLISH_TAG not in tags:
        fail("v004 provenance tag missing: " + str(mutation["id"]))
    if kind == "box":
        expected_scale = [float(value) / 100.0 for value in target["dimensions_cm"]]
        component = actor.get_editor_property("static_mesh_component")
        if (
            not _close(transform["location_cm"], target["location_cm"])
            or not _close(transform["scale3d"], expected_scale)
            or _component_material_path(component) != _asset_path(target["material"])
        ):
            fail("v004 box readback changed: " + str(mutation["id"]))
    elif kind == "text":
        if (
            not _close(transform["location_cm"], target["location_cm"])
            or not _rotation_close(transform["rotation_deg_pitch_yaw_roll"], TEXT_ROTATION)
        ):
            fail("v004 readable text transform changed: " + str(mutation["id"]))
    elif kind == "camera":
        component = actor.get_editor_property("camera_component")
        if (
            str(actor.get_actor_label()) != str(target["label"])
            or not _close(transform["location_cm"], target["location_cm"])
            or not _rotation_close(transform["rotation_deg_pitch_yaw_roll"], CAMERA_ROTATION)
            or abs(float(component.get_editor_property("ortho_width")) - float(target["ortho_width_cm"]))
            > NUMERIC_TOLERANCE
        ):
            fail("v004 camera readback changed: " + str(mutation["id"]))
    return {
        "id": str(mutation["id"]),
        "kind": kind,
        "actor_path": str(actor.get_path_name()),
        "source_label": str(mutation["source"]["label"]),
        "target_label": str(target["label"]),
        "target_location_cm": list(target["location_cm"]),
        "target_rotation_deg_pitch_yaw_roll": (
            list(target["rotation_deg_pitch_yaw_roll"])
            if kind != "box" else [0.0, float(target["yaw_deg"]), 0.0]
        ),
        "target_dimensions_cm": (
            list(target["dimensions_cm"]) if kind == "box" else None
        ),
        "target_ortho_width_cm": (
            float(target["ortho_width_cm"]) if kind == "camera" else None
        ),
        "target_material": (
            _asset_path(target["material"]) if kind == "box" else None
        ),
    }


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(canonical_json_bytes(value))
    except FileExistsError:
        fail("v004 install receipt already exists; refusing overwrite")


def main() -> None:
    ue = _require_unreal()
    inputs = validate_offline_contract()
    plan = inputs["plan"]
    protected_before = inputs["protected_hashes"]

    if INSTALL_RECEIPT.exists():
        fail("v004 install receipt already exists; refusing rerun")
    if TARGET_FILE.exists() or TARGET_ROOT_DISK.exists():
        fail("v004 target exists on disk; refusing overwrite")
    if ue.EditorAssetLibrary.does_asset_exist(TARGET_MAP):
        fail("v004 target exists in the asset registry; refusing overwrite")
    if ue.EditorAssetLibrary.list_assets(TARGET_ROOT, recursive=True, include_folder=False):
        fail("v004 target root is not empty in the asset registry")
    _assert_dirty_packages(
        {"content": [], "maps": []},
        "editor has dirty packages before v004 target creation",
    )
    world_before = _editor_world()
    world_before_name = _world_package_name(world_before)
    if world_before_name in {SOURCE_MAP, TARGET_MAP, V002_MAP}:
        fail("run from an unrelated clean editor world")

    loaded_assets: Dict[str, Any] = {}
    for asset_path in (CUBE_ASSET, *MATERIAL_LOCKS.keys()):
        if not ue.EditorAssetLibrary.does_asset_exist(asset_path):
            fail("required presentation asset is not registered: " + asset_path)
        asset = ue.EditorAssetLibrary.load_asset(asset_path)
        if asset is None:
            fail("required presentation asset could not load: " + asset_path)
        loaded_assets[asset_path] = asset
    if str(loaded_assets[CUBE_ASSET].get_class().get_name()) != "StaticMesh":
        fail("native cube asset has the wrong class")
    for material_path in MATERIAL_LOCKS:
        if "Material" not in str(loaded_assets[material_path].get_class().get_name()):
            fail("presentation material has the wrong class: " + material_path)
    _assert_dirty_packages(
        {"content": [], "maps": []},
        "asset preflight dirtied packages",
    )
    if protected_snapshot() != protected_before:
        fail("protected maps changed during v004 asset preflight")

    level_subsystem = _level_subsystem()
    actor_subsystem = _actor_subsystem()
    # First map mutation: create a new candidate package from the unopened,
    # hash-locked v003 source.  The source package itself is never loaded/saved.
    if not level_subsystem.new_level_from_template(TARGET_MAP, SOURCE_MAP):
        fail("could not clone v003 cargo map to v004 presentation candidate")
    world = _editor_world()
    if _world_package_name(world) != TARGET_MAP:
        fail("v004 presentation target did not become the active editor world")
    game_mode_before = _world_game_mode_path(world)
    if game_mode_before != EXPECTED_GAME_MODE:
        fail("v004 clone changed the OneFactory GameMode")

    source_actors = list(actor_subsystem.get_all_level_actors() or [])
    inventory = validate_source_actor_inventory(source_actors)
    actors_by_label: Dict[str, List[Any]] = {}
    for actor in source_actors:
        label = str(actor.get_actor_label())
        actors_by_label.setdefault(label, []).append(actor)

    mutation_labels = {str(row["source"]["label"]) for row in plan["mutations"]}
    if not mutation_labels <= set(actors_by_label):
        fail("one or more exact presentation mutation targets are missing")
    duplicate_targets = sorted(
        label for label in mutation_labels if len(actors_by_label[label]) != 1
    )
    if duplicate_targets:
        fail("exact presentation mutation label is not unique: " + duplicate_targets[0])
    new_labels = {str(row["label"]) for row in plan["new_connectors"]}
    if new_labels & set(actors_by_label):
        fail("new connector label collides with a v003 source actor")
    for mutation in plan["mutations"]:
        _assert_source_actor(
            actors_by_label[str(mutation["source"]["label"])][0], mutation
        )

    preserved_nonpresentation = {
        str(actor.get_path_name()): _actor_fingerprint_record(actor)
        for actor in source_actors
        if PRESENTATION_PASS_TAG not in {str(tag) for tag in list(actor.tags or [])}
    }
    unchanged_presentation = {
        str(actor.get_path_name()): _actor_fingerprint_record(actor)
        for actor in source_actors
        if (
            PRESENTATION_PASS_TAG in {str(tag) for tag in list(actor.tags or [])}
            and str(actor.get_actor_label()) not in mutation_labels
        )
    }
    cargo_before = {
        str(actor.get_path_name()): _actor_fingerprint_record(actor)
        for actor in source_actors
        if CARGO_MAP_TAG in {str(tag) for tag in list(actor.tags or [])}
    }
    visual_before = {
        str(actor.get_path_name()): _actor_fingerprint_record(actor)
        for actor in source_actors
        if VISUAL_LAYER_TAG in {str(tag) for tag in list(actor.tags or [])}
    }
    if len(preserved_nonpresentation) != EXPECTED_PRESERVED_NONPRESENTATION_COUNT:
        fail("preserved nonpresentation actor count changed before polish")
    if len(cargo_before) != EXPECTED_CARGO_LAYER_COUNT:
        fail("cargo fingerprint count changed before polish")
    if len(visual_before) != EXPECTED_COMBINED_VISUAL_LAYER_COUNT:
        fail("visual-layer fingerprint count changed before polish")

    slate_material, slate_material_record = _create_slate_deck_material()
    loaded_assets[SLATE_DECK_MATERIAL] = slate_material
    _validate_post_slate_dirty_packages(dirty_package_paths())
    if protected_snapshot() != protected_before:
        fail("protected maps changed during v004 slate material creation")

    mutation_records: List[Dict[str, Any]] = []
    for mutation in plan["mutations"]:
        actor = actors_by_label[str(mutation["source"]["label"])][0]
        target = mutation["target"]
        if mutation["kind"] == "box":
            _apply_box_mutation(actor, target, loaded_assets)
        elif mutation["kind"] == "text":
            _apply_text_mutation(actor, target)
        elif mutation["kind"] == "camera":
            _apply_camera_mutation(actor, target)
        else:  # Offline validation should make this unreachable.
            fail("unknown polish mutation kind")
        _append_unique_tags(actor, [POLISH_TAG])
        mutation_records.append(_verify_target_actor(actor, mutation))

    new_connector_actors: List[Any] = []
    new_connector_records: List[Dict[str, Any]] = []
    for spec in plan["new_connectors"]:
        actor, record = _spawn_connector(
            actor_subsystem,
            loaded_assets[CUBE_ASSET],
            loaded_assets[CREAM_MATERIAL],
            spec,
        )
        new_connector_actors.append(actor)
        new_connector_records.append(record)

    final_actors = list(actor_subsystem.get_all_level_actors() or [])
    if len(final_actors) != EXPECTED_FINAL_ACTOR_COUNT:
        fail("v004 final actor count changed")
    final_by_path = _records_by_path(final_actors)
    for path, before in preserved_nonpresentation.items():
        if final_by_path.get(path) != before:
            fail("preserved source/cargo actor changed during polish: " + path)
    for path, before in unchanged_presentation.items():
        if final_by_path.get(path) != before:
            fail("unselected presentation actor changed during polish: " + path)
    for path, before in cargo_before.items():
        if final_by_path.get(path) != before:
            fail("cargo actor changed during presentation polish: " + path)
    for path, before in visual_before.items():
        if final_by_path.get(path) != before:
            fail("machinery/visual-layer actor changed during polish: " + path)

    final_records = list(final_by_path.values())
    exact_final_tags = {
        VISUAL_LAYER_TAG: EXPECTED_COMBINED_VISUAL_LAYER_COUNT,
        CARGO_MAP_TAG: EXPECTED_CARGO_LAYER_COUNT,
        PRESENTATION_ADAPTER_TAG: EXPECTED_RUNTIME_PRESENTATION_COUNT,
        PRESENTATION_PASS_TAG: EXPECTED_PRESENTATION_ACTOR_COUNT + EXPECTED_NEW_CONNECTOR_COUNT,
        PRESENTATION_CAMERA_TAG: EXPECTED_SOURCE_CAMERA_COUNT,
        CAMERA_V004_TAG: EXPECTED_SOURCE_CAMERA_COUNT,
        POLISH_TAG: EXPECTED_EXISTING_MUTATION_COUNT + EXPECTED_NEW_CONNECTOR_COUNT,
    }
    for tag, expected in exact_final_tags.items():
        if _count_tag(final_records, tag) != expected:
            fail("v004 final actor tag count changed: " + tag)
    if _world_game_mode_path(world) != game_mode_before:
        fail("presentation polish changed the local GameMode")

    dirty_before_save = _assert_dirty_packages(
        {"content": [], "maps": [TARGET_MAP]},
        "only the v004 target map may be dirty before save",
    )
    if not level_subsystem.save_current_level():
        fail("could not save the v004 presentation candidate")
    dirty_after_save = _assert_dirty_packages(
        {"content": [], "maps": []},
        "candidate packages remain dirty after explicit save",
    )
    if not TARGET_FILE.is_file():
        fail("v004 target map package is missing after save")

    protected_after = protected_snapshot()
    if protected_after != protected_before:
        fail("protected map changed during v004 presentation polish")
    if digest(SOURCE_FILE) != SOURCE_FILE_SHA256 or SOURCE_FILE.stat().st_size != SOURCE_FILE_BYTES:
        fail("v003 source map changed during v004 presentation polish")
    if digest(SOURCE_RECEIPT) != SOURCE_RECEIPT_SHA256:
        fail("v003 source receipt changed during v004 presentation polish")
    if digest(V002_RECEIPT) != V002_RECEIPT_SHA256:
        fail("v002 presentation receipt changed during v004 presentation polish")
    if validate_material_locks() != inputs["material_hashes"]:
        fail("presentation material changed during v004 polish")
    slate_material_disk = virtual_to_uasset(SLATE_DECK_MATERIAL)
    if (
        not slate_material_disk.is_file()
        or digest(slate_material_disk) != slate_material_record["sha256"]
        or slate_material_disk.stat().st_size != slate_material_record["bytes"]
    ):
        fail("v004 slate deck material changed after its explicit save")

    cargo_hash = _fingerprint_hash(cargo_before)
    visual_hash = _fingerprint_hash(visual_before)
    preserved_hash = _fingerprint_hash(preserved_nonpresentation)
    unchanged_presentation_hash = _fingerprint_hash(unchanged_presentation)
    receipt = {
        "schema": INSTALL_RECEIPT_SCHEMA,
        "status": INSTALL_STATUS,
        "candidate_only": True,
        "source_map": SOURCE_MAP,
        "source_map_sha256": SOURCE_FILE_SHA256,
        "source_map_bytes": SOURCE_FILE_BYTES,
        "source_receipt": SOURCE_RECEIPT.as_posix(),
        "source_receipt_sha256": SOURCE_RECEIPT_SHA256,
        "v002_presentation_receipt": V002_RECEIPT.as_posix(),
        "v002_presentation_receipt_sha256": V002_RECEIPT_SHA256,
        "cargo_import_receipt": CARGO_IMPORT_RECEIPT.as_posix(),
        "cargo_import_receipt_sha256": CARGO_IMPORT_RECEIPT_SHA256,
        "target_map": TARGET_MAP,
        "target_map_sha256": digest(TARGET_FILE),
        "target_map_bytes": TARGET_FILE.stat().st_size,
        "target_creation_api": "LevelEditorSubsystem.new_level_from_template",
        "source_actor_count": EXPECTED_SOURCE_ACTOR_COUNT,
        "final_actor_count": EXPECTED_FINAL_ACTOR_COUNT,
        "preserved_nonpresentation_actor_count": len(preserved_nonpresentation),
        "preserved_nonpresentation_actor_fingerprints_before_sha256": preserved_hash,
        "preserved_nonpresentation_actor_fingerprints_after_sha256": preserved_hash,
        "unchanged_presentation_actor_count": len(unchanged_presentation),
        "unchanged_presentation_actor_fingerprints_before_sha256": unchanged_presentation_hash,
        "unchanged_presentation_actor_fingerprints_after_sha256": unchanged_presentation_hash,
        "combined_visual_layer_count": EXPECTED_COMBINED_VISUAL_LAYER_COUNT,
        "visual_layer_actor_fingerprints_before_sha256": visual_hash,
        "visual_layer_actor_fingerprints_after_sha256": visual_hash,
        "cargo_layer_count": EXPECTED_CARGO_LAYER_COUNT,
        "cargo_actor_fingerprints_before_sha256": cargo_hash,
        "cargo_actor_fingerprints_after_sha256": cargo_hash,
        "cargo_actor_mutated_count": 0,
        "machinery_actor_mutated_count": 0,
        "source_actor_removed_count": 0,
        "source_actor_created_count": EXPECTED_NEW_CONNECTOR_COUNT,
        "mutated_existing_presentation_actor_count": len(mutation_records),
        "created_presentation_connector_count": len(new_connector_records),
        "presentation_mutations": mutation_records,
        "created_press_connectors": new_connector_records,
        "plan_validation": inputs["validation"],
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "presentation_material_hashes_before": inputs["material_hashes"],
        "presentation_material_hashes_after": validate_material_locks(),
        "created_materials": [slate_material_record],
        "deck_style": {
            "full_deck_material": SLATE_DECK_MATERIAL,
            "full_deck_srgb_hex": SLATE_DECK_SRGB_HEX,
            "station_pad_material": ZONE_MATERIAL,
            "narrow_flow_lane_material": DECK_MATERIAL,
        },
        "source_map_mutated": False,
        "protected_authority_map_mutated": False,
        "native_cpp_modified": False,
        "roof_created": False,
        "new_machinery_geometry": 0,
        "new_cargo_geometry": 0,
        "game_mode_before": game_mode_before,
        "game_mode_after": _world_game_mode_path(world),
        "dirty_packages_before_save": dirty_before_save,
        "dirty_packages_after_save": dirty_after_save,
        "runtime_validated": False,
        "packaged_build_validated": False,
        "visual_capture_validated": False,
        "steam_capture_validated": False,
        "honest_status": (
            "The isolated v004 candidate preserves all v003 machinery, runtime and cargo "
            "actors while applying the reviewed native presentation-only polish. Fresh "
            "saved-map capture, PIE lifecycle, cook, packaged behavior and Steam evidence "
            "remain required."
        ),
    }
    _write_new_json(INSTALL_RECEIPT, receipt)
    ue.log(
        "PRESSSHOP_2126_OVERHEAD_PRESENTATION_POLISH_V001_PASS map={} receipt={}".format(
            TARGET_MAP, INSTALL_RECEIPT.as_posix()
        )
    )
    ue.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
