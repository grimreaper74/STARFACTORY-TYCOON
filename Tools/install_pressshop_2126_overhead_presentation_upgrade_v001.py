"""Guarded v005 presentation upgrade for Press Shop 2126 true overhead.

This one-shot Unreal Editor Python tool clones the immutable, receipt-locked
v004 candidate into a new v005 candidate and changes presentation actors only.
It enlarges the roofless deck context, replaces the black route bar with a
dual-rail shuttle route, makes every station branch continuous to an exact
port, reshapes the station zones with three-box footprints, adds three empty
shuttle carrier silhouettes, adds a restrained unlit banded-floor treatment,
improves label plaques/contrast, and updates the three true-overhead cameras.

No source, authority, machinery, visual-layer, cargo, gameplay, or native C++
asset is moved, scaled, deleted, renamed, or saved.  The module is importable
in ordinary CPython; ``main`` is the only Unreal mutation entry point.  Fresh
1920x1080 capture, PIE, cook, packaged, and Steam quality gates remain pending.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

try:  # Ordinary CPython is the intended offline-test environment.
    import unreal  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    unreal = None  # type: ignore


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")

SOURCE_ROOT = (
    "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPresentation_v004"
)
SOURCE_MAP = (
    SOURCE_ROOT
    + "/Maps/LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v004"
)
SOURCE_FILE = (
    PROJECT / "Content/LineBoss/Candidates/PressShop"
    / "PressShop2126_OverheadPresentation_v004/Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v004.umap"
)
SOURCE_FILE_SHA256 = (
    "ab77d9bc327e65fa5bf8b8efd4d6666252247be1420070563f83bb099d98fe9f"
)
SOURCE_FILE_BYTES = 1211122
SOURCE_RECEIPT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadPresentation_v004"
    / "install_receipt_v001.json"
)
SOURCE_RECEIPT_SHA256 = (
    "9c2bca410ebb40a534cdaa65a41c433c6f535df566ae209865f6fe5053a706d4"
)
SOURCE_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.overhead_presentation_polish_install_receipt.v001"
)
SOURCE_RECEIPT_STATUS = (
    "PASS_CANDIDATE_PRESENTATION_POLISH_APPLIED__"
    "CARGO_PRESERVED__PIE_CAPTURE_PENDING"
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

V003_MAP = (
    "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadCargo_v003/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003"
)
V003_FILE = (
    PROJECT / "Content/LineBoss/Candidates/PressShop"
    / "PressShop2126_OverheadCargo_v003/Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003.umap"
)
V003_FILE_SHA256 = (
    "5eae51f2a7d3e1c72deb4fd455d57a6339dee061840b7d062c5ddf680ab6100f"
)
V003_RECEIPT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadCargo_v003"
    / "integration_receipt_v001.json"
)
V003_RECEIPT_SHA256 = (
    "0d58168d05869693aef7aaac8ddd4d5bac3e7e71785b4b4db6d6f32cd6569619"
)
V003_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.overhead_cargo_map_integration_receipt.v001"
)
V003_RECEIPT_STATUS = (
    "PASS_CANDIDATE_CARGO_MAP_INTEGRATED__"
    "S07_INTERMEDIATE_PALLET_COUNTS_DEFERRED__PIE_CAPTURE_PENDING"
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

SOURCE_CAPTURE_ROOT = (
    PROJECT / "Saved/PressShop2126"
    / "OverheadPresentation_v004_SavedMapCapture_v001"
)
SOURCE_CAPTURE_RECEIPT = SOURCE_CAPTURE_ROOT / "saved_map_capture_receipt_v001.json"
SOURCE_CAPTURE_RECEIPT_SHA256 = (
    "0c97402ebc3c25a95b89dc55da0aca3608fb28ae5d4187c827d69dd654988fdc"
)
SOURCE_CAPTURE_SCHEMA = (
    "cairnwell.press_shop.overhead_presentation_saved_map_capture_receipt.v001"
)
SOURCE_CAPTURE_STATUS = (
    "PASS_IN_ENGINE_SAVED_MAP_PRESENTATION_CAPTURE__"
    "PIE_LIFECYCLE_AND_STEAM_APPROVAL_PENDING"
)
SOURCE_CAPTURE_LOCKS: Mapping[str, Mapping[str, Any]] = {
    "PressShop2126_PresentationOverview_1920x1080_v004.png": {
        "sha256": "0e40f548094a430d808cacfef847d6534fbe696242ff9e7a88cce34bd3285fdc",
        "bytes": 1624447,
    },
    "PressShop2126_PresentationSpine_1920x1080_v004.png": {
        "sha256": "e16fb5849aa7bb8160e1c281a18cf59339e58e2bd5fa131377b8a095b1a26274",
        "bytes": 2244875,
    },
    "PressShop2126_PresentationPressHero_1920x1080_v004.png": {
        "sha256": "7b8c696065433587095690bc5017dd8eab3fe0e1d629e4a6cf581351ecde0148",
        "bytes": 2244875,
    },
}

TARGET_ROOT = (
    "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPresentation_v005"
)
TARGET_MAP = (
    TARGET_ROOT
    + "/Maps/LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v005"
)
TARGET_ROOT_DISK = (
    PROJECT / "Content/LineBoss/Candidates/PressShop"
    / "PressShop2126_OverheadPresentation_v005"
)
TARGET_FILE = (
    TARGET_ROOT_DISK / "Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v005.umap"
)
INSTALL_RECEIPT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadPresentation_v005"
    / "install_receipt_v001.json"
)
INSTALL_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.overhead_presentation_upgrade_install_receipt.v001"
)
INSTALL_STATUS = (
    "PASS_CANDIDATE_PRESENTATION_UPGRADE_APPLIED__"
    "V004_FINGERPRINTS_PRESERVED__VISUAL_CAPTURE_AND_PIE_PENDING"
)

EXPECTED_GAME_MODE = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
EXPECTED_SOURCE_ACTOR_COUNT = 247
EXPECTED_SOURCE_PRESENTATION_COUNT = 85
EXPECTED_PRESERVED_NONPRESENTATION_COUNT = 162
EXPECTED_COMBINED_VISUAL_LAYER_COUNT = 146
EXPECTED_BASE_VISUAL_LAYER_COUNT = 120
EXPECTED_CARGO_LAYER_COUNT = 26
EXPECTED_SOURCE_CAMERA_COUNT = 3
EXPECTED_RUNTIME_PRESENTATION_COUNT = 1
EXPECTED_EXISTING_MUTATION_COUNT = 61
EXPECTED_NEW_BOX_COUNT = 55
EXPECTED_FINAL_ACTOR_COUNT = 302
EXPECTED_UNCHANGED_PRESENTATION_COUNT = 24
SOURCE_PRESENTATION_CATALOG_SHA256 = (
    "bc31d992193a81ef4a94eb8f83a382570e9f4ecc6b71734ee725c491538fbabf"
)

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
V004_POLISH_TAG = "LB.PressShop.OverheadPresentationPolish.v004"
V005_UPGRADE_TAG = "LB.PressShop.OverheadPresentationUpgrade.v005"
CAMERA_V005_TAG = "LB.PressShop.OverheadDeck.Camera.v005"

V002_MATERIAL_ROOT = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v002/Materials"
)
CHARCOAL_MATERIAL = (
    V002_MATERIAL_ROOT + "/M_CA_MW_PS2126_DeckCharcoal_Unlit_v001"
)
ZONE_MATERIAL = (
    V002_MATERIAL_ROOT + "/M_CA_MW_PS2126_ZonePaleGreen_Unlit_v001"
)
CREAM_MATERIAL = (
    V002_MATERIAL_ROOT + "/M_CA_MW_PS2126_FlowCream_Unlit_v001"
)
YELLOW_MATERIAL = (
    V002_MATERIAL_ROOT + "/M_CA_MW_PS2126_SafetyYellow_Unlit_v001"
)
SLATE_MATERIAL = (
    SOURCE_ROOT + "/Materials/M_CA_MW_PS2126_DeckSlateGreen_Unlit_v004"
)
REUSED_MATERIAL_LOCKS: Mapping[str, Mapping[str, Any]] = {
    CHARCOAL_MATERIAL: {
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
    SLATE_MATERIAL: {
        "sha256": "961086fa48097c6a6a11a69a09efb4685d9dbd6dc2f973a80afbf7f76b545ebf",
        "bytes": 5366,
    },
}
REUSED_MATERIAL_SRGB_HEX: Mapping[str, str] = {
    CHARCOAL_MATERIAL: "#171D21",
    ZONE_MATERIAL: "#91AA9C",
    CREAM_MATERIAL: "#E8DEC2",
    YELLOW_MATERIAL: "#E1B94F",
    SLATE_MATERIAL: "#36534F",
}

TARGET_MATERIAL_ROOT = TARGET_ROOT + "/Materials"
NEW_MATERIAL_SPECS: Tuple[Mapping[str, Any], ...] = (
    {
        "id": "floor_band_teal",
        "name": "M_CA_MW_PS2126_FloorBandTeal_Unlit_v005",
        "asset": TARGET_MATERIAL_ROOT + "/M_CA_MW_PS2126_FloorBandTeal_Unlit_v005",
        "srgb_hex": "#294A46",
    },
    {
        "id": "route_teal",
        "name": "M_CA_MW_PS2126_RouteTeal_Unlit_v005",
        "asset": TARGET_MATERIAL_ROOT + "/M_CA_MW_PS2126_RouteTeal_Unlit_v005",
        "srgb_hex": "#3B8177",
    },
)
FLOOR_BAND_MATERIAL = str(NEW_MATERIAL_SPECS[0]["asset"])
ROUTE_TEAL_MATERIAL = str(NEW_MATERIAL_SPECS[1]["asset"])

PROTECTED_MAPS: Mapping[str, Tuple[Path, str]] = {
    "source_overhead_presentation_v005_parent": (SOURCE_FILE, SOURCE_FILE_SHA256),
    "source_overhead_presentation_v002": (V002_FILE, V002_FILE_SHA256),
    "source_overhead_cargo_v003": (V003_FILE, V003_FILE_SHA256),
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

DECK_CENTER_X = -7730.645880159617
DECK_CENTER_Y = 8840.218280826943
DECK_SIZE_X = 9700.0
DECK_SIZE_Y = 17400.0
DECK_BORDER_THICKNESS = 24.0
PROCESS_X = -8990.75
ROUTE_X = -6500.0
ROUTE_WIDTH_X = 520.0
ROUTE_LENGTH_Y = 15500.0
ROUTE_MIN_Y = DECK_CENTER_Y - ROUTE_LENGTH_Y / 2.0
ROUTE_MAX_Y = DECK_CENTER_Y + ROUTE_LENGTH_Y / 2.0
ROUTE_WEST_EDGE_X = ROUTE_X - ROUTE_WIDTH_X / 2.0
RAIL_X = (-6700.0, -6300.0)
RAIL_WIDTH_X = 54.0
TEXT_ROTATION = (90.0, 180.0, 0.0)
CAMERA_ROTATION = (-90.0, 0.0, 0.0)
CAMERA_ASPECT = 16.0 / 9.0
CAPTURE_RESOLUTION = (1920, 1080)
MAX_PROJECTED_EXTERIOR_FRACTION = 0.02
MAX_STATION_PORT_GAP_CM = 10.0
MIN_HERO_GROUP_WIDTH_FRACTION = 0.80
MIN_HERO_GROUP_HEIGHT_FRACTION = 0.55

STATION_ROWS: Tuple[Mapping[str, Any], ...] = (
    {"id": "IN01", "center_y": 1600.0, "envelope_y": 1300.0, "press": False},
    {"id": "IN02", "center_y": 3260.0, "envelope_y": 1100.0, "press": False},
    {"id": "IN03", "center_y": 4260.0, "envelope_y": 650.0, "press": False},
    {"id": "IN04_05", "center_y": 5200.0, "envelope_y": 1050.0, "press": False},
    {"id": "S01", "center_y": 6350.0, "envelope_y": 1100.0, "press": False},
    {"id": "S02", "center_y": 7500.0, "envelope_y": 1000.0, "press": False},
    {"id": "S03", "center_y": 8950.0, "envelope_y": 1350.0, "press": True},
    {"id": "S04", "center_y": 10400.0, "envelope_y": 1050.0, "press": True},
    {"id": "S05", "center_y": 11850.0, "envelope_y": 1350.0, "press": True},
    {"id": "S06", "center_y": 13300.0, "envelope_y": 1200.0, "press": True},
    {"id": "S07_INSPECT", "center_y": 14700.0, "envelope_y": 900.0, "press": False},
    {"id": "S07_PALLET", "center_y": 15900.0, "envelope_y": 1100.0, "press": False},
)

EXISTING_CONNECTOR_STATIONS: Mapping[str, str] = {
    "FLOW_CONNECTOR_01": "IN01",
    "FLOW_CONNECTOR_02": "IN04_05",
    "FLOW_CONNECTOR_03": "S02",
    "FLOW_CONNECTOR_04": "S04",
    "FLOW_CONNECTOR_05": "S07_INSPECT",
    "FLOW_CONNECTOR_06": "S07_PALLET",
    "FLOW_CONNECTOR_PRESS_S03": "S03",
    "FLOW_CONNECTOR_PRESS_S05": "S05",
    "FLOW_CONNECTOR_PRESS_S06": "S06",
}
NEW_BRANCH_STATIONS = ("IN02", "IN03", "S01")

CAMERA_TARGETS: Mapping[str, Mapping[str, Any]] = {
    "overview": {
        "label": "CAM | Press Shop 2126 | complete roofless flow overview v005",
        "location_cm": [DECK_CENTER_X, DECK_CENTER_Y, 21712.544],
        "ortho_width_cm": 17200.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.Overview.v005",
    },
    "press_spine": {
        "label": "CAM | Press Shop 2126 | connected production spine v005",
        "location_cm": [-8450.0, 11100.0, 21712.544],
        "ortho_width_cm": 10800.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.PressSpine.v005",
    },
    "steam_hero": {
        "label": "CAM | Press Shop 2126 | S03-S06 grouped Steam hero v005",
        "location_cm": [PROCESS_X, 11087.5, 21712.544],
        "ortho_width_cm": 6000.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.SteamHero.v005",
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


class PresentationUpgradeGuardError(RuntimeError):
    """Fail-closed error for the candidate-only v005 upgrade lane."""


def fail(message: str) -> None:
    raise PresentationUpgradeGuardError(
        "PRESSSHOP_2126_OVERHEAD_PRESENTATION_UPGRADE_V001_FAIL: " + message
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


def _close(left: Sequence[float], right: Sequence[float]) -> bool:
    return len(left) == len(right) and all(
        abs(float(a) - float(b)) <= NUMERIC_TOLERANCE
        for a, b in zip(left, right)
    )


def _rotation_close(left: Sequence[float], right: Sequence[float]) -> bool:
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
    return 1.0 - abs(sum(a * b for a, b in zip(left_quat, right_quat))) <= NUMERIC_TOLERANCE


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


def validate_reused_material_locks() -> Dict[str, str]:
    result: Dict[str, str] = {}
    for asset_path, expected in sorted(REUSED_MATERIAL_LOCKS.items()):
        disk = virtual_to_uasset(asset_path)
        if not disk.is_file():
            fail("reused presentation material is missing: " + asset_path)
        if disk.stat().st_size != int(expected["bytes"]):
            fail("reused presentation material byte count changed: " + asset_path)
        actual = digest(disk)
        if actual != str(expected["sha256"]):
            fail("reused presentation material hash changed: " + asset_path)
        result[asset_path] = actual
    return result


def validate_source_capture() -> Dict[str, Any]:
    receipt = load_locked_json(
        SOURCE_CAPTURE_RECEIPT,
        SOURCE_CAPTURE_RECEIPT_SHA256,
        "v004 saved-map capture receipt",
    )
    exact = {
        "schema": SOURCE_CAPTURE_SCHEMA,
        "status": SOURCE_CAPTURE_STATUS,
        "target_map": SOURCE_MAP,
        "target_map_sha256_before": SOURCE_FILE_SHA256,
        "target_map_sha256_after": SOURCE_FILE_SHA256,
        "capture_resolution": [1920, 1080],
        "actor_count": EXPECTED_SOURCE_ACTOR_COUNT,
        "visual_layer_count": EXPECTED_COMBINED_VISUAL_LAYER_COUNT,
        "cargo_layer_count": EXPECTED_CARGO_LAYER_COUNT,
        "saved_camera_count": EXPECTED_SOURCE_CAMERA_COUNT,
        "project_content_mutated": False,
        "saved_actor_layout_mutated": False,
        "saved_actor_material_assignment_mutated": False,
        "steam_visual_quality_human_approved": False,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("v004 capture receipt field changed: " + key)
    rows = _require_list(receipt.get("captures"), "v004 captures")
    if len(rows) != 3:
        fail("v004 capture receipt no longer has exactly three cameras")
    by_name = {Path(str(row.get("path"))).name: row for row in rows if isinstance(row, dict)}
    if set(by_name) != set(SOURCE_CAPTURE_LOCKS):
        fail("v004 capture inventory changed")
    for name, expected in SOURCE_CAPTURE_LOCKS.items():
        path = SOURCE_CAPTURE_ROOT / name
        row = by_name[name]
        if (
            not path.is_file()
            or path.stat().st_size != int(expected["bytes"])
            or digest(path) != str(expected["sha256"])
            or row.get("sha256") != expected["sha256"]
            or row.get("bytes") != expected["bytes"]
        ):
            fail("v004 capture evidence changed: " + name)
    return receipt


def validate_v002_receipt() -> Dict[str, Any]:
    receipt = load_locked_json(
        V002_RECEIPT, V002_RECEIPT_SHA256, "v002 presentation receipt"
    )
    exact = {
        "schema": V002_RECEIPT_SCHEMA,
        "status": (
            "PASS_CANDIDATE_PRESENTATION_MAP_ASSEMBLED__"
            "VISUAL_CAPTURE_AND_RUNTIME_PENDING"
        ),
        "candidate_only": True,
        "target_map": V002_MAP,
        "target_map_sha256": V002_FILE_SHA256,
        "target_map_bytes": 1097822,
        "created_actor_count": 82,
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
    boxes = _require_list(receipt.get("created_boxes"), "v002 created boxes")
    texts = _require_list(receipt.get("created_texts"), "v002 created texts")
    cameras = _require_list(receipt.get("cameras"), "v002 cameras")
    if (len(boxes), len(texts), len(cameras)) != (64, 15, 3):
        fail("v002 presentation inventory changed")
    expected_colours = {
        asset_path: REUSED_MATERIAL_SRGB_HEX[asset_path]
        for asset_path in (CHARCOAL_MATERIAL, ZONE_MATERIAL, CREAM_MATERIAL, YELLOW_MATERIAL)
    }
    materials = {
        _asset_path(row.get("asset")): row
        for row in _require_list(receipt.get("created_materials"), "v002 materials")
        if isinstance(row, dict)
    }
    if set(materials) != set(expected_colours):
        fail("v002 presentation material inventory changed")
    for asset_path, expected_hex in expected_colours.items():
        lock = REUSED_MATERIAL_LOCKS[asset_path]
        row = materials[asset_path]
        if (
            row.get("srgb_hex") != expected_hex
            or row.get("shading_model") != "UNLIT"
            or row.get("sha256") != lock["sha256"]
            or row.get("bytes") != lock["bytes"]
        ):
            fail("v002 presentation material contract changed: " + asset_path)
    return receipt


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


def validate_v003_receipt() -> Dict[str, Any]:
    receipt = load_locked_json(
        V003_RECEIPT, V003_RECEIPT_SHA256, "v003 cargo integration receipt"
    )
    exact = {
        "schema": V003_RECEIPT_SCHEMA,
        "status": V003_RECEIPT_STATUS,
        "candidate_only": True,
        "target_map": V003_MAP,
        "target_map_sha256": V003_FILE_SHA256,
        "target_map_bytes": 1175784,
        "cargo_import_receipt_sha256": CARGO_IMPORT_RECEIPT_SHA256,
        "cargo_layer_count": EXPECTED_CARGO_LAYER_COUNT,
        "combined_visual_layer_count": EXPECTED_COMBINED_VISUAL_LAYER_COUNT,
        "existing_camera_actor_count_preserved": EXPECTED_SOURCE_CAMERA_COUNT,
        "existing_deck_presentation_actor_count_preserved": 82,
        "existing_runtime_presentation_adapter_count_preserved": 1,
        "source_actor_mutated_count": 0,
        "source_actor_removed_count": 0,
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
    layers = _require_list(receipt.get("cargo_layers"), "v003 cargo layers")
    if len(layers) != EXPECTED_CARGO_LAYER_COUNT:
        fail("v003 cargo layer receipt inventory changed")
    for raw in layers:
        if not isinstance(raw, dict) or not isinstance(raw.get("actor"), dict):
            fail("v003 cargo layer receipt row changed")
        actor = raw["actor"]
        tags = set(actor.get("tags", ()))
        if (
            actor.get("class_path") != VISUAL_LAYER_CLASS_PATH
            or actor.get("collision_enabled") is not False
            or CARGO_MAP_TAG not in tags
            or CARGO_SOURCE_TAG not in tags
            or VISUAL_LAYER_TAG not in tags
            or not str(actor.get("label")).startswith("CARGO | ")
        ):
            fail("v003 cargo actor contract changed")
    return receipt


def validate_source_receipt() -> Dict[str, Any]:
    receipt = load_locked_json(
        SOURCE_RECEIPT, SOURCE_RECEIPT_SHA256, "v004 presentation receipt"
    )
    exact = {
        "schema": SOURCE_RECEIPT_SCHEMA,
        "status": SOURCE_RECEIPT_STATUS,
        "candidate_only": True,
        "target_map": SOURCE_MAP,
        "target_map_sha256": SOURCE_FILE_SHA256,
        "target_map_bytes": SOURCE_FILE_BYTES,
        "source_map_sha256": V003_FILE_SHA256,
        "source_receipt_sha256": V003_RECEIPT_SHA256,
        "source_actor_count": 244,
        "final_actor_count": EXPECTED_SOURCE_ACTOR_COUNT,
        "mutated_existing_presentation_actor_count": 38,
        "created_presentation_connector_count": 3,
        "preserved_nonpresentation_actor_count": EXPECTED_PRESERVED_NONPRESENTATION_COUNT,
        "combined_visual_layer_count": EXPECTED_COMBINED_VISUAL_LAYER_COUNT,
        "cargo_layer_count": EXPECTED_CARGO_LAYER_COUNT,
        "unchanged_presentation_actor_count": 44,
        "machinery_actor_mutated_count": 0,
        "cargo_actor_mutated_count": 0,
        "source_actor_created_count": 3,
        "source_actor_removed_count": 0,
        "roof_created": False,
        "runtime_validated": False,
        "visual_capture_validated": False,
        "steam_capture_validated": False,
        "protected_authority_map_mutated": False,
        "source_map_mutated": False,
        "native_cpp_modified": False,
        "new_cargo_geometry": 0,
        "new_machinery_geometry": 0,
        "game_mode_before": EXPECTED_GAME_MODE,
        "game_mode_after": EXPECTED_GAME_MODE,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("v004 presentation receipt field changed: " + key)
    if receipt.get("dirty_packages_after_save") != {"content": [], "maps": []}:
        fail("v004 presentation receipt is not clean after save")
    if receipt.get("protected_hashes_before") != receipt.get("protected_hashes_after"):
        fail("v004 presentation receipt does not prove protected hashes stable")
    mutations = _require_list(
        receipt.get("presentation_mutations"), "v004 presentation mutations"
    )
    connectors = _require_list(
        receipt.get("created_press_connectors"), "v004 press connectors"
    )
    if len(mutations) != 38 or len(connectors) != 3:
        fail("v004 presentation change inventory changed")
    created_materials = _require_list(
        receipt.get("created_materials"), "v004 created materials"
    )
    if len(created_materials) != 1:
        fail("v004 created-material inventory changed")
    slate = created_materials[0]
    slate_lock = REUSED_MATERIAL_LOCKS[SLATE_MATERIAL]
    if (
        not isinstance(slate, dict)
        or _asset_path(slate.get("asset")) != SLATE_MATERIAL
        or slate.get("srgb_hex") != "#36534F"
        or slate.get("shading_model") != "UNLIT"
        or slate.get("sha256") != slate_lock["sha256"]
        or slate.get("bytes") != slate_lock["bytes"]
    ):
        fail("v004 slate material receipt contract changed")
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


def _mutation(
    kind: str,
    item_id: str,
    source: Mapping[str, Any],
    target: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "kind": kind,
        "id": item_id,
        "source": copy.deepcopy(dict(source)),
        "target": copy.deepcopy(dict(target)),
    }


def _target(source: Mapping[str, Any], **changes: Any) -> Dict[str, Any]:
    result = copy.deepcopy(dict(source))
    result.update(changes)
    return result


def build_v004_catalog(
    v002_receipt: Mapping[str, Any],
    v004_receipt: Mapping[str, Any],
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Rebuild the exact 85-actor v004 presentation inventory from receipts."""
    catalog = {
        "box": _indexed_rows(v002_receipt.get("created_boxes"), "v002 boxes"),
        "text": _indexed_rows(v002_receipt.get("created_texts"), "v002 texts"),
        "camera": _indexed_rows(v002_receipt.get("cameras"), "v002 cameras"),
    }
    camera_targets = v004_receipt.get("plan_validation", {}).get("camera_targets", {})
    if not isinstance(camera_targets, dict) or set(camera_targets) != set(CAMERA_TARGETS):
        fail("v004 camera target inventory changed")
    for raw in _require_list(
        v004_receipt.get("presentation_mutations"), "v004 mutations"
    ):
        if not isinstance(raw, dict):
            fail("v004 mutation row changed")
        kind = str(raw.get("kind"))
        item_id = str(raw.get("id"))
        if kind not in catalog or item_id not in catalog[kind]:
            fail("v004 mutation selects an unknown presentation actor: " + item_id)
        row = catalog[kind][item_id]
        if row.get("label") != raw.get("source_label"):
            fail("v004 mutation source label changed: " + item_id)
        row["label"] = raw.get("target_label")
        field_map = {
            "target_location_cm": "location_cm",
            "target_dimensions_cm": "dimensions_cm",
            "target_rotation_deg_pitch_yaw_roll": "rotation_deg_pitch_yaw_roll",
            "target_ortho_width_cm": "ortho_width_cm",
            "target_material": "material",
        }
        for source_key, target_key in field_map.items():
            if raw.get(source_key) is not None:
                row[target_key] = copy.deepcopy(raw[source_key])
        if kind == "camera":
            row["role_tag"] = str(camera_targets[item_id]["role_tag"])
    for raw in _require_list(
        v004_receipt.get("created_press_connectors"), "v004 connectors"
    ):
        if not isinstance(raw, dict):
            fail("v004 connector row changed")
        item_id = str(raw.get("id"))
        if item_id in catalog["box"]:
            fail("v004 connector id duplicates a v002 box: " + item_id)
        row = copy.deepcopy(raw)
        row.pop("collision_readback", None)
        row.pop("actor_path", None)
        row.pop("cast_shadow", None)
        row.pop("collision", None)
        catalog["box"][item_id] = row
    if (
        len(catalog["box"]) != 67
        or len(catalog["text"]) != 15
        or len(catalog["camera"]) != 3
    ):
        fail("rebuilt v004 presentation catalog count changed")
    labels = [
        str(row.get("label"))
        for group in catalog.values()
        for row in group.values()
    ]
    if len(labels) != EXPECTED_SOURCE_PRESENTATION_COUNT or len(labels) != len(set(labels)):
        fail("rebuilt v004 presentation labels are missing or duplicated")
    return catalog


def _station_index() -> Dict[str, Mapping[str, Any]]:
    return {str(row["id"]): row for row in STATION_ROWS}


def _station_body_depth(station: Mapping[str, Any]) -> float:
    return 1700.0 if bool(station["press"]) else 1900.0


def _station_footprint_depth(station: Mapping[str, Any]) -> float:
    return _station_body_depth(station) + 400.0


def _station_body_length(station: Mapping[str, Any]) -> float:
    return round(float(station["envelope_y"]) * 0.88, 3)


def _station_port_x(station: Mapping[str, Any]) -> float:
    return PROCESS_X + _station_footprint_depth(station) / 2.0


def _box_spec(
    item_id: str,
    label: str,
    role: str,
    material: str,
    location: Sequence[float],
    dimensions: Sequence[float],
) -> Dict[str, Any]:
    return {
        "kind": "box",
        "id": item_id,
        "label": label,
        "role": role,
        "material": material,
        "location_cm": [float(value) for value in location],
        "dimensions_cm": [float(value) for value in dimensions],
        "yaw_deg": 0.0,
    }


def _build_floor_bands() -> List[Dict[str, Any]]:
    result = [
        _box_spec(
            "FLOOR_BAND_LONG_{:02d}".format(index),
            "2126 OVERHEAD FLOOR | longitudinal structural band {:02d} v005".format(index),
            "FloorBandLongitudinal",
            FLOOR_BAND_MATERIAL,
            [x_value, DECK_CENTER_Y, -0.75],
            [90.0, 16900.0, 0.2],
        )
        for index, x_value in enumerate((-10850.0, -4800.0), start=1)
    ]
    result.extend(
        _box_spec(
            "FLOOR_BAND_CROSS_{:02d}".format(index),
            "2126 OVERHEAD FLOOR | transverse bay band {:02d} v005".format(index),
            "FloorBandTransverse",
            FLOOR_BAND_MATERIAL,
            [DECK_CENTER_X, y_value, -0.75],
            [9300.0, 80.0, 0.2],
        )
        for index, y_value in enumerate(
            (2700.0, 5700.0, 8700.0, 11700.0, 14700.0), start=1
        )
    )
    return result


def _build_zone_wings() -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for station in STATION_ROWS:
        station_id = str(station["id"])
        envelope = float(station["envelope_y"])
        center_y = float(station["center_y"])
        body_depth = _station_body_depth(station)
        for side, sign, y_factor, length_factor, role in (
            ("WEST", -1.0, -0.18, 0.32, "StationZoneWestWing"),
            ("EAST", 1.0, 0.16, 0.42, "StationZoneEastPortWing"),
        ):
            result.append(_box_spec(
                "ZONE_WING_{}_{}".format(station_id, side),
                "2126 OVERHEAD ZONE | {} | {} footprint wing v005".format(
                    station_id, side.lower()
                ),
                role,
                ZONE_MATERIAL,
                [
                    PROCESS_X + sign * (body_depth / 2.0 + 100.0),
                    center_y + y_factor * envelope,
                    -0.6,
                ],
                [200.0, round(length_factor * envelope, 3), 0.8],
            ))
    return result


def _branch_spec(station: Mapping[str, Any], item_id: str, label: str) -> Dict[str, Any]:
    port_x = _station_port_x(station)
    width_x = ROUTE_WEST_EDGE_X - port_x
    return _box_spec(
        item_id,
        label,
        "StationRouteBranch",
        ROUTE_TEAL_MATERIAL,
        [port_x + width_x / 2.0, float(station["center_y"]), -0.25],
        [width_x, 74.0, 0.3],
    )


def _build_port_caps() -> List[Dict[str, Any]]:
    return [
        _box_spec(
            "STATION_PORT_CAP_" + str(station["id"]),
            "2126 OVERHEAD ROUTE | {} cream station port v005".format(station["id"]),
            "StationPortCap",
            CREAM_MATERIAL,
            [_station_port_x(station), float(station["center_y"]), -0.08],
            [24.0, 128.0, 0.3],
        )
        for station in STATION_ROWS
    ]


def _build_carriers() -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for carrier_index, center_y in enumerate((3500.0, 9650.0, 15050.0), start=1):
        prefix = "EMPTY_SHUTTLE_{:02d}".format(carrier_index)
        pieces = (
            ("CHASSIS", "EmptyShuttleChassis", CHARCOAL_MATERIAL,
             [ROUTE_X, center_y, 0.04], [430.0, 560.0, 0.24]),
            ("DECK", "EmptyShuttleDeck", CREAM_MATERIAL,
             [ROUTE_X, center_y - 25.0, 0.19], [300.0, 360.0, 0.18]),
            ("NOSE", "EmptyShuttleDirectionNose", YELLOW_MATERIAL,
             [ROUTE_X, center_y + 235.0, 0.30], [300.0, 86.0, 0.18]),
        )
        for suffix, role, material, location, dimensions in pieces:
            result.append(_box_spec(
                prefix + "_" + suffix,
                "2126 OVERHEAD ROUTE | empty shuttle {:02d} {} v005".format(
                    carrier_index, suffix.lower()
                ),
                role,
                material,
                location,
                dimensions,
            ))
    return result


def build_upgrade_plan(
    v002_receipt: Mapping[str, Any],
    v004_receipt: Mapping[str, Any],
) -> Dict[str, Any]:
    catalog = build_v004_catalog(v002_receipt, v004_receipt)
    boxes, texts, cameras = catalog["box"], catalog["text"], catalog["camera"]
    mutations: List[Dict[str, Any]] = []

    deck_contract = {
        "DECK_BASE": (
            [DECK_CENTER_X, DECK_CENTER_Y, -11.0],
            [DECK_SIZE_X, DECK_SIZE_Y, 20.0],
            SLATE_MATERIAL,
        ),
        "DECK_BORDER_WEST": (
            [DECK_CENTER_X - DECK_SIZE_X / 2.0 + DECK_BORDER_THICKNESS / 2.0,
             DECK_CENTER_Y, -0.35],
            [DECK_BORDER_THICKNESS, DECK_SIZE_Y, 0.5],
            CREAM_MATERIAL,
        ),
        "DECK_BORDER_EAST": (
            [DECK_CENTER_X + DECK_SIZE_X / 2.0 - DECK_BORDER_THICKNESS / 2.0,
             DECK_CENTER_Y, -0.35],
            [DECK_BORDER_THICKNESS, DECK_SIZE_Y, 0.5],
            CREAM_MATERIAL,
        ),
        "DECK_BORDER_SOUTH": (
            [DECK_CENTER_X,
             DECK_CENTER_Y - DECK_SIZE_Y / 2.0 + DECK_BORDER_THICKNESS / 2.0,
             -0.35],
            [DECK_SIZE_X, DECK_BORDER_THICKNESS, 0.5],
            CREAM_MATERIAL,
        ),
        "DECK_BORDER_NORTH": (
            [DECK_CENTER_X,
             DECK_CENTER_Y + DECK_SIZE_Y / 2.0 - DECK_BORDER_THICKNESS / 2.0,
             -0.35],
            [DECK_SIZE_X, DECK_BORDER_THICKNESS, 0.5],
            CREAM_MATERIAL,
        ),
    }
    for item_id, (location, dimensions, material) in deck_contract.items():
        source = boxes[item_id]
        mutations.append(_mutation(
            "box", item_id, source,
            _target(source, location_cm=location, dimensions_cm=dimensions,
                    material=material),
        ))

    route_contract = {
        "FLOW_LANE": ([ROUTE_X, DECK_CENTER_Y, -0.45],
                      [ROUTE_WIDTH_X, ROUTE_LENGTH_Y, 0.6], ROUTE_TEAL_MATERIAL,
                      "DualRailRouteBed"),
        "FLOW_EDGE_WEST": ([RAIL_X[0], DECK_CENTER_Y, -0.10],
                           [RAIL_WIDTH_X, ROUTE_LENGTH_Y, 0.24], CREAM_MATERIAL,
                           "DualRailWest"),
        "FLOW_EDGE_EAST": ([RAIL_X[1], DECK_CENTER_Y, -0.10],
                           [RAIL_WIDTH_X, ROUTE_LENGTH_Y, 0.24], CREAM_MATERIAL,
                           "DualRailEast"),
        "FLOW_EDGE_INBOUND": ([ROUTE_X, ROUTE_MIN_Y, -0.10],
                              [ROUTE_WIDTH_X, RAIL_WIDTH_X, 0.24], CREAM_MATERIAL,
                              "DualRailInboundCap"),
        "FLOW_EDGE_OUTBOUND": ([ROUTE_X, ROUTE_MAX_Y, -0.10],
                               [ROUTE_WIDTH_X, RAIL_WIDTH_X, 0.24], CREAM_MATERIAL,
                               "DualRailOutboundCap"),
    }
    for item_id, (location, dimensions, material, role) in route_contract.items():
        source = boxes[item_id]
        mutations.append(_mutation(
            "box", item_id, source,
            _target(
                source,
                label="2126 OVERHEAD ROUTE | {} v005".format(role),
                role=role,
                location_cm=location,
                dimensions_cm=dimensions,
                material=material,
            ),
        ))

    station_by_id = _station_index()
    for station in STATION_ROWS:
        station_id = str(station["id"])
        body_id = "PAD_" + station_id
        body = boxes[body_id]
        body_length = _station_body_length(station)
        mutations.append(_mutation(
            "box", body_id, body,
            _target(
                body,
                label="2126 OVERHEAD ZONE | {} footprint body v005".format(station_id),
                role="StationZoneBody",
                location_cm=[PROCESS_X, float(station["center_y"]), -0.6],
                dimensions_cm=[_station_body_depth(station), body_length, 0.8],
                material=ZONE_MATERIAL,
            ),
        ))
        plaque_id = "PAD_KEY_" + station_id
        plaque = boxes[plaque_id]
        plaque_x = PROCESS_X - _station_body_depth(station) / 2.0 + 230.0
        plaque_length = max(440.0, min(body_length - 60.0, 760.0))
        mutations.append(_mutation(
            "box", plaque_id, plaque,
            _target(
                plaque,
                label="2126 OVERHEAD LABEL | {} charcoal plaque v005".format(station_id),
                role="StationLabelPlaque",
                location_cm=[plaque_x, float(station["center_y"]), -0.12],
                dimensions_cm=[320.0, plaque_length, 0.36],
                material=CHARCOAL_MATERIAL,
            ),
        ))

    for connector_id, station_id in EXISTING_CONNECTOR_STATIONS.items():
        source = boxes[connector_id]
        branch = _branch_spec(
            station_by_id[station_id],
            connector_id,
            "2126 OVERHEAD ROUTE | {} teal station branch v005".format(station_id),
        )
        mutations.append(_mutation(
            "box", connector_id, source,
            _target(
                source,
                label=branch["label"],
                role=branch["role"],
                material=branch["material"],
                location_cm=branch["location_cm"],
                dimensions_cm=branch["dimensions_cm"],
                yaw_deg=branch["yaw_deg"],
            ),
        ))

    for item_id, source in sorted(texts.items()):
        target = copy.deepcopy(source)
        target["rotation_deg_pitch_yaw_roll"] = list(TEXT_ROTATION)
        target["colour_rgba"] = [232, 222, 194, 255]
        target["location_cm"] = list(source["location_cm"])
        target["location_cm"][2] = 0.20
        if item_id.startswith("LABEL_") and item_id.removeprefix("LABEL_") in station_by_id:
            station = station_by_id[item_id.removeprefix("LABEL_")]
            target["location_cm"] = [
                PROCESS_X - _station_body_depth(station) / 2.0 + 230.0,
                float(station["center_y"]),
                0.20,
            ]
            target["world_size_cm"] = 128.0
        elif item_id == "LABEL_TITLE":
            target.update({
                "location_cm": [-4500.0, DECK_CENTER_Y, 0.20],
                "world_size_cm": 220.0,
            })
        elif item_id == "LABEL_INBOUND":
            target.update({
                "location_cm": [-5500.0, 1500.0, 0.20],
                "world_size_cm": 140.0,
                "colour_rgba": [225, 185, 79, 255],
            })
        elif item_id == "LABEL_OUTBOUND":
            target.update({
                "location_cm": [-5500.0, 16000.0, 0.20],
                "world_size_cm": 140.0,
                "colour_rgba": [225, 185, 79, 255],
            })
        mutations.append(_mutation("text", item_id, source, target))

    for item_id, target_values in CAMERA_TARGETS.items():
        source = cameras[item_id]
        camera_preview = {
            "location_cm": list(target_values["location_cm"]),
            "ortho_width_cm": float(target_values["ortho_width_cm"]),
        }
        camera_rect = _camera_world_rect(camera_preview)
        mutations.append(_mutation(
            "camera", item_id, source,
            _target(
                source,
                label=str(target_values["label"]),
                location_cm=list(target_values["location_cm"]),
                rotation_deg_pitch_yaw_roll=list(CAMERA_ROTATION),
                ortho_width_cm=float(target_values["ortho_width_cm"]),
                role_tag=str(target_values["role_tag"]),
                aspect_ratio=CAMERA_ASPECT,
                projection="ORTHOGRAPHIC",
                camera_axis_contract={
                    "screen_right": "+Y", "screen_up": "+X", "view": "-Z"
                },
                declared_bounds_min_xy_cm=[
                    DECK_CENTER_X - DECK_SIZE_X / 2.0,
                    DECK_CENTER_Y - DECK_SIZE_Y / 2.0,
                ],
                declared_bounds_max_xy_cm=[
                    DECK_CENTER_X + DECK_SIZE_X / 2.0,
                    DECK_CENTER_Y + DECK_SIZE_Y / 2.0,
                ],
                margins={
                    "deck_backing_min_x_cm": camera_rect["min_x"]
                    - (DECK_CENTER_X - DECK_SIZE_X / 2.0),
                    "deck_backing_max_x_cm": (DECK_CENTER_X + DECK_SIZE_X / 2.0)
                    - camera_rect["max_x"],
                    "deck_backing_min_y_cm": camera_rect["min_y"]
                    - (DECK_CENTER_Y - DECK_SIZE_Y / 2.0),
                    "deck_backing_max_y_cm": (DECK_CENTER_Y + DECK_SIZE_Y / 2.0)
                    - camera_rect["max_y"],
                },
            ),
        ))

    additions = _build_floor_bands() + _build_zone_wings()
    additions.extend(
        _branch_spec(
            station_by_id[station_id],
            "FLOW_BRANCH_" + station_id,
            "2126 OVERHEAD ROUTE | {} teal station branch v005".format(station_id),
        )
        for station_id in NEW_BRANCH_STATIONS
    )
    additions.extend(_build_port_caps())
    additions.extend(_build_carriers())
    return {
        "mutations": tuple(mutations),
        "additions": tuple(additions),
        "catalog": catalog,
    }


def _axis_interval(center: float, size: float) -> Tuple[float, float]:
    return center - size / 2.0, center + size / 2.0


def _camera_world_rect(camera: Mapping[str, Any]) -> Dict[str, float]:
    width_y = float(camera["ortho_width_cm"])
    height_x = width_y / CAMERA_ASPECT
    center_x, center_y = (float(value) for value in camera["location_cm"][:2])
    min_x, max_x = _axis_interval(center_x, height_x)
    min_y, max_y = _axis_interval(center_y, width_y)
    return {
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "size_x": height_x,
        "size_y": width_y,
    }


def _rect_overlap_fraction(
    outer: Mapping[str, float], inner: Mapping[str, float]
) -> float:
    overlap_x = max(
        0.0,
        min(float(outer["max_x"]), float(inner["max_x"]))
        - max(float(outer["min_x"]), float(inner["min_x"])),
    )
    overlap_y = max(
        0.0,
        min(float(outer["max_y"]), float(inner["max_y"]))
        - max(float(outer["min_y"]), float(inner["min_y"])),
    )
    area = float(inner["size_x"]) * float(inner["size_y"])
    if area <= 0.0:
        fail("cannot measure a non-positive rectangle")
    return overlap_x * overlap_y / area


def _srgb_luminance(rgb: Sequence[int]) -> float:
    if len(rgb) < 3:
        fail("colour does not contain RGB channels")
    linear = []
    for value in rgb[:3]:
        channel = float(value) / 255.0
        linear.append(
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
        )
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast_ratio(left: Sequence[int], right: Sequence[int]) -> float:
    first, second = sorted((_srgb_luminance(left), _srgb_luminance(right)))
    return (second + 0.05) / (first + 0.05)


def _hex_rgb8(value: str) -> Tuple[int, int, int]:
    if len(value) != 7 or not value.startswith("#"):
        fail("invalid locked sRGB colour: " + value)
    try:
        return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5))  # type: ignore[return-value]
    except ValueError:
        fail("invalid locked sRGB colour: " + value)


def validate_upgrade_plan(plan: Mapping[str, Any]) -> Dict[str, Any]:
    mutations = list(plan.get("mutations", ()))
    additions = list(plan.get("additions", ()))
    catalog = plan.get("catalog")
    if not isinstance(catalog, dict):
        fail("upgrade plan has no rebuilt source catalog")
    catalog_sha256 = hashlib.sha256(canonical_json_bytes(catalog)).hexdigest()
    if catalog_sha256 != SOURCE_PRESENTATION_CATALOG_SHA256:
        fail("rebuilt v004 presentation catalog changed: " + catalog_sha256)
    if len(mutations) != EXPECTED_EXISTING_MUTATION_COUNT:
        fail("upgrade plan existing-mutation count changed")
    if len(additions) != EXPECTED_NEW_BOX_COUNT:
        fail("upgrade plan new-box count changed")
    if any(row.get("kind") not in {"box", "text", "camera"} for row in mutations):
        fail("upgrade plan contains an unsupported mutation kind")
    if any(row.get("kind") != "box" for row in additions):
        fail("upgrade additions must remain native cube boxes only")

    mutation_ids = [str(row.get("id")) for row in mutations]
    addition_ids = [str(row.get("id")) for row in additions]
    if len(mutation_ids) != len(set(mutation_ids)):
        fail("upgrade mutation ids are duplicated")
    if len(addition_ids) != len(set(addition_ids)):
        fail("upgrade addition ids are duplicated")
    if set(mutation_ids) & set(addition_ids):
        fail("upgrade mutation/addition ids overlap")
    source_labels = [str(row.get("source", {}).get("label")) for row in mutations]
    target_labels = [str(row.get("target", {}).get("label")) for row in mutations]
    new_labels = [str(row.get("label")) for row in additions]
    if len(source_labels) != len(set(source_labels)):
        fail("upgrade source actor selectors are duplicated")
    if len(target_labels + new_labels) != len(set(target_labels + new_labels)):
        fail("upgrade target actor labels are duplicated")
    if any(label.startswith(("VIS | ", "CARGO | ")) for label in source_labels):
        fail("upgrade plan illegally selects machinery or cargo")
    if any(
        label.upper().startswith(("VIS | ", "CARGO | ", "MACHINE | ", "WIP | "))
        for label in target_labels
    ):
        fail("upgrade target labels impersonate machinery, cargo, or WIP")
    forbidden_mutation_semantics = (
        "MACHINE", "CARGO", "WIP", "ROOF", "LIGHT", "EXPOSURE", "TEXTURE"
    )
    for mutation in mutations:
        semantic = "{} {}".format(
            mutation.get("id", ""), mutation.get("target", {}).get("role", "")
        ).upper()
        if any(term in semantic for term in forbidden_mutation_semantics):
            fail("upgrade mutation introduces forbidden scope: " + str(mutation.get("id")))
    allowed_changes = {
        "box": {"label", "role", "material", "location_cm", "dimensions_cm", "yaw_deg"},
        "text": {
            "label", "location_cm", "rotation_deg_pitch_yaw_roll",
            "world_size_cm", "colour_rgba",
        },
        "camera": {
            "label", "location_cm", "rotation_deg_pitch_yaw_roll",
            "ortho_width_cm", "role_tag", "aspect_ratio", "projection",
            "camera_axis_contract", "declared_bounds_min_xy_cm",
            "declared_bounds_max_xy_cm", "margins",
        },
    }
    for mutation in mutations:
        kind = str(mutation["kind"])
        source = mutation["source"]
        target = mutation["target"]
        expected_source = catalog.get(kind, {}).get(str(mutation["id"]))
        if not isinstance(expected_source, dict) or source != expected_source:
            fail("upgrade mutation source receipt row changed: " + str(mutation["id"]))
        if set(source) != set(target):
            fail("upgrade mutation added or removed receipt fields: " + str(mutation["id"]))
        for key in set(source) - allowed_changes[kind]:
            if source[key] != target[key]:
                fail("upgrade mutation changed an out-of-scope field: {}:{}".format(
                    mutation["id"], key
                ))

    expected_box_ids = {
        "DECK_BASE", "DECK_BORDER_WEST", "DECK_BORDER_EAST",
        "DECK_BORDER_SOUTH", "DECK_BORDER_NORTH",
        "FLOW_LANE", "FLOW_EDGE_WEST", "FLOW_EDGE_EAST",
        "FLOW_EDGE_INBOUND", "FLOW_EDGE_OUTBOUND",
        *("PAD_" + str(row["id"]) for row in STATION_ROWS),
        *("PAD_KEY_" + str(row["id"]) for row in STATION_ROWS),
        *EXISTING_CONNECTOR_STATIONS.keys(),
    }
    expected_text_ids = {
        *("LABEL_" + str(row["id"]) for row in STATION_ROWS),
        "LABEL_TITLE", "LABEL_INBOUND", "LABEL_OUTBOUND",
    }
    expected_camera_ids = set(CAMERA_TARGETS)
    actual_box_ids = {str(row["id"]) for row in mutations if row["kind"] == "box"}
    actual_text_ids = {str(row["id"]) for row in mutations if row["kind"] == "text"}
    actual_camera_ids = {str(row["id"]) for row in mutations if row["kind"] == "camera"}
    if actual_box_ids != expected_box_ids:
        fail("upgrade box mutation selector changed")
    if actual_text_ids != expected_text_ids:
        fail("upgrade text mutation selector changed")
    if actual_camera_ids != expected_camera_ids:
        fail("upgrade camera mutation selector changed")
    by_id = {str(row["id"]): row for row in mutations}
    additions_by_id = {str(row["id"]): row for row in additions}

    exact_target_labels: Dict[str, str] = {}
    for mutation in mutations:
        item_id = str(mutation["id"])
        exact_target_labels[item_id] = str(mutation["source"]["label"])
    route_roles = {
        "FLOW_LANE": "DualRailRouteBed",
        "FLOW_EDGE_WEST": "DualRailWest",
        "FLOW_EDGE_EAST": "DualRailEast",
        "FLOW_EDGE_INBOUND": "DualRailInboundCap",
        "FLOW_EDGE_OUTBOUND": "DualRailOutboundCap",
    }
    for item_id, role in route_roles.items():
        exact_target_labels[item_id] = "2126 OVERHEAD ROUTE | {} v005".format(role)
    for station in STATION_ROWS:
        station_id = str(station["id"])
        exact_target_labels["PAD_" + station_id] = (
            "2126 OVERHEAD ZONE | {} footprint body v005".format(station_id)
        )
        exact_target_labels["PAD_KEY_" + station_id] = (
            "2126 OVERHEAD LABEL | {} charcoal plaque v005".format(station_id)
        )
    for connector_id, station_id in EXISTING_CONNECTOR_STATIONS.items():
        exact_target_labels[connector_id] = (
            "2126 OVERHEAD ROUTE | {} teal station branch v005".format(station_id)
        )
    for item_id, camera in CAMERA_TARGETS.items():
        exact_target_labels[item_id] = str(camera["label"])
    for item_id, expected_label in exact_target_labels.items():
        if str(by_id[item_id]["target"]["label"]) != expected_label:
            fail("exact v005 target actor label changed: " + item_id)

    station_by_id_for_contract = _station_index()
    expected_additions = _build_floor_bands() + _build_zone_wings()
    expected_additions.extend(
        _branch_spec(
            station_by_id_for_contract[station_id],
            "FLOW_BRANCH_" + station_id,
            "2126 OVERHEAD ROUTE | {} teal station branch v005".format(station_id),
        )
        for station_id in NEW_BRANCH_STATIONS
    )
    expected_additions.extend(_build_port_caps())
    expected_additions.extend(_build_carriers())
    if additions != expected_additions:
        fail("exact v005 native-box addition contract changed")

    allowed_materials = {
        CHARCOAL_MATERIAL, ZONE_MATERIAL, CREAM_MATERIAL, YELLOW_MATERIAL,
        SLATE_MATERIAL, FLOOR_BAND_MATERIAL, ROUTE_TEAL_MATERIAL,
    }
    for row in [
        *(mutation["target"] for mutation in mutations if mutation["kind"] == "box"),
        *additions,
    ]:
        dimensions = row.get("dimensions_cm")
        if (
            not isinstance(dimensions, list)
            or len(dimensions) != 3
            or any(not math.isfinite(float(value)) or float(value) <= 0.0 for value in dimensions)
        ):
            fail("upgrade box has invalid dimensions: " + str(row.get("id")))
        if _asset_path(row.get("material")) not in allowed_materials:
            fail("upgrade box uses an unapproved material or texture: " + str(row.get("id")))
        if abs(float(row.get("yaw_deg", 0.0))) > NUMERIC_TOLERANCE:
            fail("upgrade box introduced an unreviewed rotation: " + str(row.get("id")))

    deck_rect = {
        "min_x": DECK_CENTER_X - DECK_SIZE_X / 2.0,
        "max_x": DECK_CENTER_X + DECK_SIZE_X / 2.0,
        "min_y": DECK_CENTER_Y - DECK_SIZE_Y / 2.0,
        "max_y": DECK_CENTER_Y + DECK_SIZE_Y / 2.0,
        "size_x": DECK_SIZE_X,
        "size_y": DECK_SIZE_Y,
    }
    deck = by_id["DECK_BASE"]["target"]
    if (
        not _close(deck["location_cm"], [DECK_CENTER_X, DECK_CENTER_Y, -11.0])
        or not _close(deck["dimensions_cm"], [DECK_SIZE_X, DECK_SIZE_Y, 20.0])
        or _asset_path(deck["material"]) != SLATE_MATERIAL
        or deck["role"] != "Deck"
    ):
        fail("enlarged Cairnwell slate deck contract changed")
    expected_borders = {
        "DECK_BORDER_WEST": (
            [deck_rect["min_x"] + DECK_BORDER_THICKNESS / 2.0, DECK_CENTER_Y, -0.35],
            [DECK_BORDER_THICKNESS, DECK_SIZE_Y, 0.5],
        ),
        "DECK_BORDER_EAST": (
            [deck_rect["max_x"] - DECK_BORDER_THICKNESS / 2.0, DECK_CENTER_Y, -0.35],
            [DECK_BORDER_THICKNESS, DECK_SIZE_Y, 0.5],
        ),
        "DECK_BORDER_SOUTH": (
            [DECK_CENTER_X, deck_rect["min_y"] + DECK_BORDER_THICKNESS / 2.0, -0.35],
            [DECK_SIZE_X, DECK_BORDER_THICKNESS, 0.5],
        ),
        "DECK_BORDER_NORTH": (
            [DECK_CENTER_X, deck_rect["max_y"] - DECK_BORDER_THICKNESS / 2.0, -0.35],
            [DECK_SIZE_X, DECK_BORDER_THICKNESS, 0.5],
        ),
    }
    for item_id, (location, dimensions) in expected_borders.items():
        row = by_id[item_id]["target"]
        if (
            not _close(row["location_cm"], location)
            or not _close(row["dimensions_cm"], dimensions)
            or _asset_path(row["material"]) != CREAM_MATERIAL
            or row["role"] != "DeckBorder"
        ):
            fail("enlarged deck border changed: " + item_id)

    camera_metrics: Dict[str, Dict[str, float]] = {}
    for item_id, expected in CAMERA_TARGETS.items():
        target = by_id[item_id]["target"]
        if (
            target["label"] != expected["label"]
            or not _close(target["location_cm"], expected["location_cm"])
            or not _rotation_close(target["rotation_deg_pitch_yaw_roll"], CAMERA_ROTATION)
            or abs(float(target["ortho_width_cm"]) - float(expected["ortho_width_cm"]))
            > NUMERIC_TOLERANCE
            or target["role_tag"] != expected["role_tag"]
            or target["projection"] != "ORTHOGRAPHIC"
            or abs(float(target["aspect_ratio"]) - CAMERA_ASPECT) > NUMERIC_TOLERANCE
            or target["camera_axis_contract"]
            != {"screen_right": "+Y", "screen_up": "+X", "view": "-Z"}
        ):
            fail("saved overhead camera contract changed: " + item_id)
        camera_rect = _camera_world_rect(target)
        expected_min = [deck_rect["min_x"], deck_rect["min_y"]]
        expected_max = [deck_rect["max_x"], deck_rect["max_y"]]
        expected_margins = {
            "deck_backing_min_x_cm": camera_rect["min_x"] - deck_rect["min_x"],
            "deck_backing_max_x_cm": deck_rect["max_x"] - camera_rect["max_x"],
            "deck_backing_min_y_cm": camera_rect["min_y"] - deck_rect["min_y"],
            "deck_backing_max_y_cm": deck_rect["max_y"] - camera_rect["max_y"],
        }
        if (
            not _close(target["declared_bounds_min_xy_cm"], expected_min)
            or not _close(target["declared_bounds_max_xy_cm"], expected_max)
            or set(target["margins"]) != set(expected_margins)
            or any(
                abs(float(target["margins"][key]) - value) > NUMERIC_TOLERANCE
                for key, value in expected_margins.items()
            )
        ):
            fail("saved overhead camera deck-backdrop metadata changed: " + item_id)
        frame_deck_fraction = _rect_overlap_fraction(deck_rect, camera_rect)
        exterior_fraction = 1.0 - frame_deck_fraction
        if exterior_fraction > MAX_PROJECTED_EXTERIOR_FRACTION + NUMERIC_TOLERANCE:
            fail("saved camera exposes too much black surround: " + item_id)
        if not (
            camera_rect["min_x"] >= deck_rect["min_x"] - NUMERIC_TOLERANCE
            and camera_rect["max_x"] <= deck_rect["max_x"] + NUMERIC_TOLERANCE
            and camera_rect["min_y"] >= deck_rect["min_y"] - NUMERIC_TOLERANCE
            and camera_rect["max_y"] <= deck_rect["max_y"] + NUMERIC_TOLERANCE
        ):
            fail("saved camera is not fully backed by the deck: " + item_id)
        camera_metrics[item_id] = {
            "projected_deck_fraction": frame_deck_fraction,
            "projected_exterior_fraction": exterior_fraction,
            "view_world_x_cm": camera_rect["size_x"],
            "view_world_y_cm": camera_rect["size_y"],
        }
    overview_rect = _camera_world_rect(by_id["overview"]["target"])
    overview_deck_visible = _rect_overlap_fraction(overview_rect, deck_rect)
    if 1.0 - overview_deck_visible > MAX_PROJECTED_EXTERIOR_FRACTION + NUMERIC_TOLERANCE:
        fail("overview crops more than two percent of the enlarged deck context")
    required_flow_y = [
        ROUTE_MIN_Y - RAIL_WIDTH_X / 2.0,
        ROUTE_MAX_Y + RAIL_WIDTH_X / 2.0,
        min(float(row["center_y"]) - float(row["envelope_y"]) / 2.0 for row in STATION_ROWS),
        max(float(row["center_y"]) + float(row["envelope_y"]) / 2.0 for row in STATION_ROWS),
    ]
    if min(required_flow_y) < overview_rect["min_y"] or max(required_flow_y) > overview_rect["max_y"]:
        fail("overview no longer contains the complete inbound-to-outbound flow")

    lane = by_id["FLOW_LANE"]["target"]
    if (
        lane["role"] != "DualRailRouteBed"
        or _asset_path(lane["material"]) != ROUTE_TEAL_MATERIAL
        or not _close(lane["location_cm"], [ROUTE_X, DECK_CENTER_Y, -0.45])
        or not _close(lane["dimensions_cm"], [ROUTE_WIDTH_X, ROUTE_LENGTH_Y, 0.6])
    ):
        fail("unexplained FLOW_LANE bar was not replaced by the teal route bed")
    rail_contract = {
        "FLOW_EDGE_WEST": (RAIL_X[0], "DualRailWest"),
        "FLOW_EDGE_EAST": (RAIL_X[1], "DualRailEast"),
    }
    for item_id, (rail_x, role) in rail_contract.items():
        rail = by_id[item_id]["target"]
        if (
            rail["role"] != role
            or _asset_path(rail["material"]) != CREAM_MATERIAL
            or not _close(rail["location_cm"], [rail_x, DECK_CENTER_Y, -0.10])
            or not _close(rail["dimensions_cm"], [RAIL_WIDTH_X, ROUTE_LENGTH_Y, 0.24])
        ):
            fail("dual shuttle rail contract changed: " + item_id)
    cap_contract = {
        "FLOW_EDGE_INBOUND": (ROUTE_MIN_Y, "DualRailInboundCap"),
        "FLOW_EDGE_OUTBOUND": (ROUTE_MAX_Y, "DualRailOutboundCap"),
    }
    for item_id, (center_y, role) in cap_contract.items():
        cap = by_id[item_id]["target"]
        if (
            cap["role"] != role
            or _asset_path(cap["material"]) != CREAM_MATERIAL
            or not _close(cap["location_cm"], [ROUTE_X, center_y, -0.10])
            or not _close(
                cap["dimensions_cm"], [ROUTE_WIDTH_X, RAIL_WIDTH_X, 0.24]
            )
        ):
            fail("dual shuttle route cap contract changed: " + item_id)
    if abs(RAIL_X[1] - RAIL_X[0]) < 300.0:
        fail("dual shuttle rails are no longer visually distinct")

    carrier_rows = [row for row in additions if str(row["id"]).startswith("EMPTY_SHUTTLE_")]
    carrier_groups: Dict[str, List[Mapping[str, Any]]] = {}
    for row in carrier_rows:
        carrier_groups.setdefault(str(row["id"])[0:16], []).append(row)
    if len(carrier_rows) != 9 or len(carrier_groups) != 3:
        fail("route must contain exactly three three-piece empty shuttle carriers")
    expected_carrier_roles = {
        "EmptyShuttleChassis", "EmptyShuttleDeck", "EmptyShuttleDirectionNose"
    }
    for group_id, rows in carrier_groups.items():
        if {str(row["role"]) for row in rows} != expected_carrier_roles:
            fail("empty shuttle carrier silhouette changed: " + group_id)
        for row in rows:
            min_x, max_x = _axis_interval(
                float(row["location_cm"][0]), float(row["dimensions_cm"][0])
            )
            if min_x < ROUTE_X - ROUTE_WIDTH_X / 2.0 or max_x > ROUTE_X + ROUTE_WIDTH_X / 2.0:
                fail("empty shuttle carrier leaves the reviewed route bed: " + str(row["id"]))
            min_y, max_y = _axis_interval(
                float(row["location_cm"][1]), float(row["dimensions_cm"][1])
            )
            if min_y < ROUTE_MIN_Y or max_y > ROUTE_MAX_Y:
                fail("empty shuttle carrier leaves the route length: " + str(row["id"]))
            if any(term in (str(row["id"]) + str(row["role"])).upper()
                   for term in ("CARGO", "WIP", "MACHINE")):
                fail("empty shuttle silhouette was reclassified as gameplay geometry")
        anchor_by_role = {
            str(row["role"]): (
                float(row["location_cm"][1])
                + (25.0 if row["role"] == "EmptyShuttleDeck" else 0.0)
                - (235.0 if row["role"] == "EmptyShuttleDirectionNose" else 0.0)
            )
            for row in rows
        }
        if max(anchor_by_role.values()) - min(anchor_by_role.values()) > NUMERIC_TOLERANCE:
            fail("empty shuttle pieces no longer share a reviewed silhouette anchor: " + group_id)
    carrier_centers = sorted(
        float(next(row for row in rows if row["role"] == "EmptyShuttleChassis")["location_cm"][1])
        for rows in carrier_groups.values()
    )
    if any(right - left < 2000.0 for left, right in zip(carrier_centers, carrier_centers[1:])):
        fail("empty shuttle carriers are no longer distinctly readable")

    station_by_id = _station_index()
    branch_by_station: Dict[str, Mapping[str, Any]] = {}
    for connector_id, station_id in EXISTING_CONNECTOR_STATIONS.items():
        branch_by_station[station_id] = by_id[connector_id]["target"]
    for station_id in NEW_BRANCH_STATIONS:
        branch_by_station[station_id] = additions_by_id["FLOW_BRANCH_" + station_id]
    if set(branch_by_station) != set(station_by_id):
        fail("continuous route does not address all twelve station ports")
    connector_gaps: Dict[str, float] = {}
    for station_id, station in station_by_id.items():
        branch = branch_by_station[station_id]
        if (
            branch["role"] != "StationRouteBranch"
            or _asset_path(branch["material"]) != ROUTE_TEAL_MATERIAL
            or abs(float(branch["location_cm"][1]) - float(station["center_y"]))
            > NUMERIC_TOLERANCE
        ):
            fail("station route branch style or alignment changed: " + station_id)
        branch_min, branch_max = _axis_interval(
            float(branch["location_cm"][0]), float(branch["dimensions_cm"][0])
        )
        port_x = _station_port_x(station)
        port_gap = abs(branch_min - port_x)
        route_gap = abs(branch_max - ROUTE_WEST_EDGE_X)
        if port_gap > MAX_STATION_PORT_GAP_CM or route_gap > MAX_STATION_PORT_GAP_CM:
            fail("station route branch is discontinuous: " + station_id)
        connector_gaps[station_id] = max(port_gap, route_gap)
        cap = additions_by_id["STATION_PORT_CAP_" + station_id]
        if (
            cap["role"] != "StationPortCap"
            or _asset_path(cap["material"]) != CREAM_MATERIAL
            or abs(float(cap["location_cm"][0]) - port_x) > NUMERIC_TOLERANCE
            or abs(float(cap["location_cm"][1]) - float(station["center_y"]))
            > NUMERIC_TOLERANCE
        ):
            fail("cream station port marker changed: " + station_id)

    zone_extents: Dict[str, Dict[str, float]] = {}
    for station_id, station in station_by_id.items():
        body = by_id["PAD_" + station_id]["target"]
        plaque = by_id["PAD_KEY_" + station_id]["target"]
        west = additions_by_id["ZONE_WING_{}_WEST".format(station_id)]
        east = additions_by_id["ZONE_WING_{}_EAST".format(station_id)]
        pieces = (body, west, east)
        if {str(row["role"]) for row in pieces} != {
            "StationZoneBody", "StationZoneWestWing", "StationZoneEastPortWing"
        }:
            fail("station footprint is not exactly a reviewed three-box zone: " + station_id)
        if any(_asset_path(row["material"]) != ZONE_MATERIAL for row in pieces):
            fail("station footprint lost the pale-green hierarchy: " + station_id)
        if (
            body["role"] != "StationZoneBody"
            or not _close(
                body["location_cm"],
                [PROCESS_X, float(station["center_y"]), -0.6],
            )
            or not _close(
                body["dimensions_cm"],
                [_station_body_depth(station), _station_body_length(station), 0.8],
            )
        ):
            fail("station footprint body contract changed: " + station_id)
        min_x = min(float(row["location_cm"][0]) - float(row["dimensions_cm"][0]) / 2.0 for row in pieces)
        max_x = max(float(row["location_cm"][0]) + float(row["dimensions_cm"][0]) / 2.0 for row in pieces)
        min_y = min(float(row["location_cm"][1]) - float(row["dimensions_cm"][1]) / 2.0 for row in pieces)
        max_y = max(float(row["location_cm"][1]) + float(row["dimensions_cm"][1]) / 2.0 for row in pieces)
        original_min_x = PROCESS_X - 1150.0
        original_max_x = PROCESS_X + 1150.0
        original_min_y = float(station["center_y"]) - float(station["envelope_y"]) / 2.0
        original_max_y = float(station["center_y"]) + float(station["envelope_y"]) / 2.0
        if (
            min_x < original_min_x - NUMERIC_TOLERANCE
            or max_x > original_max_x + NUMERIC_TOLERANCE
            or min_y < original_min_y - NUMERIC_TOLERANCE
            or max_y > original_max_y + NUMERIC_TOLERANCE
        ):
            fail("station footprint exceeds its frozen v002 service envelope: " + station_id)
        if abs(max_x - _station_port_x(station)) > NUMERIC_TOLERANCE:
            fail("station footprint east wing no longer defines its exact port: " + station_id)
        body_min_x, body_max_x = _axis_interval(
            float(body["location_cm"][0]), float(body["dimensions_cm"][0])
        )
        west_min_x, west_max_x = _axis_interval(
            float(west["location_cm"][0]), float(west["dimensions_cm"][0])
        )
        east_min_x, east_max_x = _axis_interval(
            float(east["location_cm"][0]), float(east["dimensions_cm"][0])
        )
        if (
            abs(west_max_x - body_min_x) > MAX_STATION_PORT_GAP_CM
            or abs(east_min_x - body_max_x) > MAX_STATION_PORT_GAP_CM
            or west_min_x >= west_max_x
            or east_min_x >= east_max_x
        ):
            fail("station footprint wings are disconnected from the body: " + station_id)
        body_min_y, body_max_y = _axis_interval(
            float(body["location_cm"][1]), float(body["dimensions_cm"][1])
        )
        for wing in (west, east):
            wing_min_y, wing_max_y = _axis_interval(
                float(wing["location_cm"][1]), float(wing["dimensions_cm"][1])
            )
            if min(body_max_y, wing_max_y) - max(body_min_y, wing_min_y) <= 0.0:
                fail("station footprint wing does not overlap its body: " + station_id)
        body_length = _station_body_length(station)
        expected_plaque_length = max(440.0, min(body_length - 60.0, 760.0))
        expected_plaque_location = [
            PROCESS_X - _station_body_depth(station) / 2.0 + 230.0,
            float(station["center_y"]),
            -0.12,
        ]
        if (
            plaque["role"] != "StationLabelPlaque"
            or _asset_path(plaque["material"]) != CHARCOAL_MATERIAL
            or not _close(plaque["location_cm"], expected_plaque_location)
            or not _close(plaque["dimensions_cm"], [320.0, expected_plaque_length, 0.36])
        ):
            fail("station label plaque contract changed: " + station_id)
        zone_extents[station_id] = {
            "min_x": min_x, "max_x": max_x, "min_y": min_y, "max_y": max_y
        }
    ordered_zones = sorted(zone_extents.values(), key=lambda row: row["min_y"])
    if any(right["min_y"] <= left["max_y"] for left, right in zip(ordered_zones, ordered_zones[1:])):
        fail("footprint-shaped station zones overlap")

    press_ids = ("S03", "S04", "S05", "S06")
    press_min_y = min(zone_extents[item_id]["min_y"] for item_id in press_ids)
    press_max_y = max(zone_extents[item_id]["max_y"] for item_id in press_ids)
    press_min_x = min(zone_extents[item_id]["min_x"] for item_id in press_ids)
    press_max_x = max(zone_extents[item_id]["max_x"] for item_id in press_ids)
    hero_rect = _camera_world_rect(by_id["steam_hero"]["target"])
    hero_width_fraction = (press_max_y - press_min_y) / hero_rect["size_y"]
    hero_height_fraction = (press_max_x - press_min_x) / hero_rect["size_x"]
    if (
        press_min_x < hero_rect["min_x"] - NUMERIC_TOLERANCE
        or press_max_x > hero_rect["max_x"] + NUMERIC_TOLERANCE
        or press_min_y < hero_rect["min_y"] - NUMERIC_TOLERANCE
        or press_max_y > hero_rect["max_y"] + NUMERIC_TOLERANCE
    ):
        fail("S03-S06 zone footprint is clipped by the saved hero camera")
    if hero_width_fraction < MIN_HERO_GROUP_WIDTH_FRACTION:
        fail("S03-S06 hero group is less than eighty percent of frame width")
    if hero_height_fraction < MIN_HERO_GROUP_HEIGHT_FRACTION:
        fail("S03-S06 hero group is less than fifty-five percent of frame height")

    label_contrast = _contrast_ratio(
        _hex_rgb8(REUSED_MATERIAL_SRGB_HEX[CREAM_MATERIAL]),
        _hex_rgb8(REUSED_MATERIAL_SRGB_HEX[CHARCOAL_MATERIAL]),
    )
    if label_contrast < 4.5:
        fail("station label plaque contrast is below 4.5:1")
    minimum_projected_text_px = float("inf")
    for item_id in expected_text_ids:
        target = by_id[item_id]["target"]
        if not _rotation_close(target["rotation_deg_pitch_yaw_roll"], TEXT_ROTATION):
            fail("label is not readable in the saved-map camera basis: " + item_id)
        if _rotation_close(target["rotation_deg_pitch_yaw_roll"], (90.0, 0.0, 0.0)):
            fail("label reverted to the non-mirrored but upside-down probe transform")
        if item_id.startswith("LABEL_") and item_id.removeprefix("LABEL_") in station_by_id:
            station_id = item_id.removeprefix("LABEL_")
            plaque = by_id["PAD_KEY_" + station_id]["target"]
            if target["colour_rgba"] != [232, 222, 194, 255]:
                fail("station label lost cream-on-charcoal contrast: " + item_id)
            if abs(float(target["world_size_cm"]) - 128.0) > NUMERIC_TOLERANCE:
                fail("station label world size changed: " + item_id)
            plaque_top_z = (
                float(plaque["location_cm"][2])
                + float(plaque["dimensions_cm"][2]) / 2.0
            )
            if (
                abs(float(target["location_cm"][0]) - float(plaque["location_cm"][0]))
                > NUMERIC_TOLERANCE
                or abs(float(target["location_cm"][1]) - float(plaque["location_cm"][1]))
                > NUMERIC_TOLERANCE
                or float(target["location_cm"][2]) <= plaque_top_z
            ):
                fail("station label is not centered above its charcoal plaque: " + item_id)
            projected = (
                float(target["world_size_cm"])
                * CAPTURE_RESOLUTION[1]
                / overview_rect["size_x"]
            )
            minimum_projected_text_px = min(minimum_projected_text_px, projected)
            if projected < 14.0:
                fail("station label is too small at 1920x1080 overview scale: " + item_id)

    nonstation_label_contract = {
        "LABEL_TITLE": ([-4500.0, DECK_CENTER_Y, 0.20], 220.0, [232, 222, 194, 255]),
        "LABEL_INBOUND": ([-5500.0, 1500.0, 0.20], 140.0, [225, 185, 79, 255]),
        "LABEL_OUTBOUND": ([-5500.0, 16000.0, 0.20], 140.0, [225, 185, 79, 255]),
    }
    for item_id, (location, size, colour) in nonstation_label_contract.items():
        target = by_id[item_id]["target"]
        if (
            not _close(target["location_cm"], location)
            or abs(float(target["world_size_cm"]) - size) > NUMERIC_TOLERANCE
            or [int(value) for value in target["colour_rgba"]] != colour
            or not (
                deck_rect["min_x"] <= float(location[0]) <= deck_rect["max_x"]
                and deck_rect["min_y"] <= float(location[1]) <= deck_rect["max_y"]
                and overview_rect["min_x"] <= float(location[0]) <= overview_rect["max_x"]
                and overview_rect["min_y"] <= float(location[1]) <= overview_rect["max_y"]
            )
        ):
            fail("non-station label contrast/framing contract changed: " + item_id)

    floor_bands = [row for row in additions if str(row["id"]).startswith("FLOOR_BAND_")]
    if len(floor_bands) != 7:
        fail("baked-style industrial floor must contain exactly seven restrained bands")
    if any(_asset_path(row["material"]) != FLOOR_BAND_MATERIAL for row in floor_bands):
        fail("industrial floor bands lost the reviewed #294A46 material")
    band_area = 0.0
    for row in floor_bands:
        min_x, max_x = _axis_interval(
            float(row["location_cm"][0]), float(row["dimensions_cm"][0])
        )
        min_y, max_y = _axis_interval(
            float(row["location_cm"][1]), float(row["dimensions_cm"][1])
        )
        if (
            min_x < deck_rect["min_x"]
            or max_x > deck_rect["max_x"]
            or min_y < deck_rect["min_y"]
            or max_y > deck_rect["max_y"]
            or abs(float(row["location_cm"][2]) + 0.75) > NUMERIC_TOLERANCE
        ):
            fail("industrial floor band leaves the reviewed deck context: " + str(row["id"]))
        band_area += float(row["dimensions_cm"][0]) * float(row["dimensions_cm"][1])
    floor_band_area_fraction_upper_bound = band_area / (DECK_SIZE_X * DECK_SIZE_Y)
    if floor_band_area_fraction_upper_bound > 0.05:
        fail("industrial floor bands are no longer restrained")
    forbidden_terms = ("ROOF", "LIGHT", "EXPOSURE", "MACHINE", "CARGO", "TEXTURE")
    for row in additions:
        semantic = "{} {}".format(row.get("id", ""), row.get("role", "")).upper()
        if any(term in semantic for term in forbidden_terms):
            fail("upgrade addition introduces forbidden scope: " + str(row.get("id")))

    addition_role_counts: Dict[str, int] = {}
    for row in additions:
        role = str(row["role"])
        addition_role_counts[role] = addition_role_counts.get(role, 0) + 1
    expected_role_counts = {
        "FloorBandLongitudinal": 2,
        "FloorBandTransverse": 5,
        "StationZoneWestWing": 12,
        "StationZoneEastPortWing": 12,
        "StationRouteBranch": 3,
        "StationPortCap": 12,
        "EmptyShuttleChassis": 3,
        "EmptyShuttleDeck": 3,
        "EmptyShuttleDirectionNose": 3,
    }
    if addition_role_counts != expected_role_counts:
        fail("upgrade addition role counts changed")

    return {
        "source_presentation_actor_count": EXPECTED_SOURCE_PRESENTATION_COUNT,
        "source_presentation_catalog_sha256": catalog_sha256,
        "existing_mutation_count": len(mutations),
        "new_native_box_count": len(additions),
        "box_mutation_count": len(actual_box_ids),
        "text_mutation_count": len(actual_text_ids),
        "camera_mutation_count": len(actual_camera_ids),
        "final_actor_count": EXPECTED_FINAL_ACTOR_COUNT,
        "final_presentation_actor_count": (
            EXPECTED_SOURCE_PRESENTATION_COUNT + EXPECTED_NEW_BOX_COUNT
        ),
        "v005_provenance_actor_count": (
            EXPECTED_EXISTING_MUTATION_COUNT + EXPECTED_NEW_BOX_COUNT
        ),
        "unchanged_presentation_actor_count": EXPECTED_UNCHANGED_PRESENTATION_COUNT,
        "camera_metrics": camera_metrics,
        "overview_enlarged_deck_visible_fraction": overview_deck_visible,
        "overview_complete_flow_unclipped": True,
        "maximum_projected_exterior_fraction": MAX_PROJECTED_EXTERIOR_FRACTION,
        "hero_s03_s06_frame_width_fraction": hero_width_fraction,
        "hero_s03_s06_frame_height_fraction": hero_height_fraction,
        "hero_metric_basis": "S03-S06 footprint-shaped presentation-zone bounds",
        "hero_group_fully_contained": True,
        "station_connector_max_gap_cm": max(connector_gaps.values()),
        "station_connector_gaps_cm": connector_gaps,
        "station_port_count": len(connector_gaps),
        "station_zone_piece_count": len(STATION_ROWS) * 3,
        "station_zone_footprint_depth_cm": {
            "nonpress": _station_footprint_depth(STATION_ROWS[0]),
            "press": _station_footprint_depth(STATION_ROWS[6]),
        },
        "empty_shuttle_carrier_count": len(carrier_groups),
        "empty_shuttle_pieces_per_carrier": 3,
        "minimum_station_label_projected_height_px_1920x1080": minimum_projected_text_px,
        "cream_on_charcoal_label_contrast_ratio": label_contrast,
        "source_text_colour_readback_contract": {
            "frozen_authoring_call": "unreal.Color(R,G,B,A) positional",
            "ue_5_8_constructor_order": ["B", "G", "R", "A"],
            "immutable_source_readback_order": ["B", "G", "R", "A"],
            "v005_target_authoring": "unreal.Color(b=,g=,r=,a=) keyword",
            "target_readback_order": ["R", "G", "B", "A"],
        },
        "floor_band_area_fraction_upper_bound": floor_band_area_fraction_upper_bound,
        "readable_text_rotation_deg_pitch_yaw_roll": list(TEXT_ROTATION),
        "deck_material": {
            "asset": SLATE_MATERIAL,
            "srgb_hex": "#36534F",
            "shading_model": "UNLIT",
        },
        "new_materials": [
            {
                "asset": str(row["asset"]),
                "srgb_hex": str(row["srgb_hex"]),
                "linear_rgb": list(srgb_hex_to_linear(str(row["srgb_hex"]))),
                "shading_model": "UNLIT",
            }
            for row in NEW_MATERIAL_SPECS
        ],
        "addition_role_counts": addition_role_counts,
        "external_assets_required": False,
        "external_textures_required": False,
        "lights_created": 0,
        "roofs_created": 0,
        "machine_geometry_created": 0,
        "cargo_geometry_created": 0,
        "machine_or_cargo_actor_mutations": 0,
        "camera_axis_contract": {
            "view_direction": "-Z",
            "screen_right_world_axis": "+Y",
            "screen_up_world_axis": "+X",
            "projection": "ORTHOGRAPHIC",
            "aspect_ratio": CAMERA_ASPECT,
        },
    }


def validate_offline_contract() -> Dict[str, Any]:
    if not SOURCE_FILE.is_file():
        fail("frozen v004 source map is missing")
    if SOURCE_FILE.stat().st_size != SOURCE_FILE_BYTES:
        fail("frozen v004 source map byte count changed")
    if digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
        fail("frozen v004 source map hash changed")
    if TARGET_FILE.exists() or TARGET_ROOT_DISK.exists():
        fail("v005 target root already exists; offline freeze requires a fresh lane")
    if INSTALL_RECEIPT.exists():
        fail("v005 install receipt already exists; refusing a rerun lane")
    source_receipt = validate_source_receipt()
    v002_receipt = validate_v002_receipt()
    v003_receipt = validate_v003_receipt()
    cargo_import_receipt = validate_cargo_import_receipt()
    capture_receipt = validate_source_capture()
    material_hashes = validate_reused_material_locks()
    protected_hashes = protected_snapshot()
    plan = build_upgrade_plan(v002_receipt, source_receipt)
    validation = validate_upgrade_plan(plan)
    return {
        "source_receipt": source_receipt,
        "v002_receipt": v002_receipt,
        "v003_receipt": v003_receipt,
        "cargo_import_receipt": cargo_import_receipt,
        "source_capture_receipt": capture_receipt,
        "material_hashes": material_hashes,
        "protected_hashes": protected_hashes,
        "plan": plan,
        "validation": validation,
    }


def _require_unreal() -> Any:
    if unreal is None:
        fail("main must run inside UnrealEditor Python")
    return unreal


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


def _validate_post_material_dirty_packages(
    actual: Mapping[str, Sequence[str]], context: str
) -> Dict[str, List[str]]:
    normalised = {
        "content": sorted(str(value) for value in actual.get("content", ())),
        "maps": sorted(str(value) for value in actual.get("maps", ())),
    }
    allowed = (
        {"content": [], "maps": []},
        {"content": [], "maps": [TARGET_MAP]},
    )
    if normalised not in allowed:
        fail(
            "{}; allowed_dirty={}; actual_dirty={}".format(
                context,
                json.dumps(allowed, sort_keys=True, separators=(",", ":")),
                json.dumps(normalised, sort_keys=True, separators=(",", ":")),
            )
        )
    return normalised


def _create_unlit_material(spec: Mapping[str, Any]) -> Tuple[Any, Dict[str, Any]]:
    ue = _require_unreal()
    asset_path = str(spec["asset"])
    if ue.EditorAssetLibrary.does_asset_exist(asset_path):
        fail("v005 material already exists: " + asset_path)
    material = ue.AssetToolsHelpers.get_asset_tools().create_asset(
        str(spec["name"]), TARGET_MATERIAL_ROOT, ue.Material, ue.MaterialFactoryNew()
    )
    if not isinstance(material, ue.Material):
        fail("could not create v005 material: " + asset_path)
    material.set_editor_property("shading_model", ue.MaterialShadingModel.MSM_UNLIT)
    linear_rgb = srgb_hex_to_linear(str(spec["srgb_hex"]))
    expression = ue.MaterialEditingLibrary.create_material_expression(
        material, ue.MaterialExpressionConstant3Vector, -220, 0
    )
    if expression is None:
        fail("could not create colour expression: " + asset_path)
    expression.set_editor_property(
        "constant",
        ue.LinearColor(linear_rgb[0], linear_rgb[1], linear_rgb[2], 1.0),
    )
    if not ue.MaterialEditingLibrary.connect_material_property(
        expression, "", ue.MaterialProperty.MP_EMISSIVE_COLOR
    ):
        fail("could not connect emissive colour: " + asset_path)
    initial_errors = [
        str(value)
        for value in (ue.MaterialEditingLibrary.recompile_material(material) or [])
    ]
    if initial_errors:
        fail("initial material compile failed for {}: {}".format(asset_path, initial_errors))
    if not ue.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        fail("could not perform material stabilization save: " + asset_path)
    final_errors = [
        str(value)
        for value in (ue.MaterialEditingLibrary.recompile_material(material) or [])
    ]
    if final_errors:
        fail("final material compile failed for {}: {}".format(asset_path, final_errors))
    final_save_attempts = 0
    asset_dirty = True
    dirty_after_attempt: Dict[str, List[str]] = {"content": [], "maps": []}
    while final_save_attempts < 2 and asset_dirty:
        final_save_attempts += 1
        if not ue.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
            fail("could not perform final material save: " + asset_path)
        dirty_after_attempt = dirty_package_paths()
        asset_dirty = asset_path in dirty_after_attempt["content"]
    if asset_dirty:
        fail(
            "material remained dirty after bounded final saves: {}; actual_dirty={}".format(
                asset_path,
                json.dumps(dirty_after_attempt, sort_keys=True, separators=(",", ":")),
            )
        )
    disk = virtual_to_uasset(asset_path)
    if not disk.is_file() or _asset_path(material) != asset_path:
        fail("v005 material registry/disk path changed: " + asset_path)
    shading_model_readback = str(material.get_editor_property("shading_model"))
    if "UNLIT" not in shading_model_readback.upper():
        fail("v005 material shading-model readback is not unlit: " + asset_path)
    constant_readback = expression.get_editor_property("constant")
    linear_rgb_readback = [
        float(constant_readback.r),
        float(constant_readback.g),
        float(constant_readback.b),
    ]
    if not _close(linear_rgb_readback, linear_rgb):
        fail("v005 material colour-expression readback changed: " + asset_path)
    return material, {
        "id": str(spec["id"]),
        "asset": asset_path,
        "srgb_hex": str(spec["srgb_hex"]),
        "linear_rgb": list(linear_rgb),
        "shading_model": "UNLIT",
        "shading_model_readback": shading_model_readback,
        "linear_rgb_readback": linear_rgb_readback,
        "material_recompile_passes": 2,
        "final_save_attempts": final_save_attempts,
        "sha256": digest(disk),
        "bytes": disk.stat().st_size,
    }


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
        colour = text_component.get_editor_property("text_render_color")
        record["text_render"] = {
            "text": str(text_component.get_editor_property("text")),
            "world_size": float(text_component.get_editor_property("world_size")),
            "horizontal_alignment": str(
                text_component.get_editor_property("horizontal_alignment")
            ),
            "vertical_alignment": str(
                text_component.get_editor_property("vertical_alignment")
            ),
            "text_render_color_rgba": [
                int(colour.r), int(colour.g), int(colour.b), int(colour.a)
            ],
        }
    camera_component = _safe_property(actor, ("camera_component",))
    if camera_component is not None:
        record["camera_component"] = {
            "projection_mode": str(camera_component.get_editor_property("projection_mode")),
            "ortho_width": float(camera_component.get_editor_property("ortho_width")),
            "aspect_ratio": float(camera_component.get_editor_property("aspect_ratio")),
            "constrain_aspect_ratio": bool(
                camera_component.get_editor_property("constrain_aspect_ratio")
            ),
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
        fail("v004 source actor count changed")
    exact_tags = {
        VISUAL_LAYER_TAG: EXPECTED_COMBINED_VISUAL_LAYER_COUNT,
        CARGO_MAP_TAG: EXPECTED_CARGO_LAYER_COUNT,
        CARGO_SOURCE_TAG: EXPECTED_CARGO_LAYER_COUNT,
        PRESENTATION_PASS_TAG: EXPECTED_SOURCE_PRESENTATION_COUNT,
        PRESENTATION_CAMERA_TAG: EXPECTED_SOURCE_CAMERA_COUNT,
        PRESENTATION_ADAPTER_TAG: EXPECTED_RUNTIME_PRESENTATION_COUNT,
        V004_POLISH_TAG: 41,
        BOOTSTRAP_TAG: 1,
        BUILD_AUTHORITY_TAG: 1,
        PLAYER_START_TAG: 1,
    }
    for tag, expected in exact_tags.items():
        if _count_tag(records, tag) != expected:
            fail("v004 source actor tag count changed: " + tag)
    cargo = [row for row in records if CARGO_MAP_TAG in set(row["tags"])]
    visual = [row for row in records if VISUAL_LAYER_TAG in set(row["tags"])]
    presentation = [row for row in records if PRESENTATION_PASS_TAG in set(row["tags"])]
    if (
        len(cargo) != EXPECTED_CARGO_LAYER_COUNT
        or any(row["class_path"] != VISUAL_LAYER_CLASS_PATH for row in cargo)
        or any(not row["label"].startswith("CARGO | ") for row in cargo)
    ):
        fail("v004 cargo actor inventory changed")
    if (
        len(visual) != EXPECTED_COMBINED_VISUAL_LAYER_COUNT
        or len(presentation) != EXPECTED_SOURCE_PRESENTATION_COUNT
    ):
        fail("v004 visual/presentation actor inventory changed")
    return {
        "records": records,
        "cargo_labels": sorted(row["label"] for row in cargo),
        "visual_labels": sorted(row["label"] for row in visual),
        "presentation_labels": sorted(row["label"] for row in presentation),
    }


def _component_material_path(component: Any, index: int = 0) -> str | None:
    return _asset_path(component.get_material(index))


def _colour_rgba(component: Any) -> List[int]:
    colour = component.get_editor_property("text_render_color")
    return [int(colour.r), int(colour.g), int(colour.b), int(colour.a)]


def _legacy_positional_unreal_color_readback_rgba(
    authored_rgba: Sequence[int],
) -> List[int]:
    """Return the frozen v002/v004 readback from Unreal's (B,G,R,A) ctor.

    UE 5.8 generates ``unreal.Color.__init__(b, g, r, a)``.  The v002 tool
    supplied its receipt-intent RGBA values positionally, so the immutable
    v004 package truthfully reads those legacy colours back as B,G,R,A when
    queried through the named r/g/b/a properties.  v005 validates that exact
    source state before replacing it with correctly keyword-authored RGBA.
    """
    if len(authored_rgba) != 4:
        fail("legacy TextRender colour must contain four channels")
    return [
        int(authored_rgba[2]),
        int(authored_rgba[1]),
        int(authored_rgba[0]),
        int(authored_rgba[3]),
    ]


def _unreal_color_from_rgba(authored_rgba: Sequence[int]) -> Any:
    ue = _require_unreal()
    if len(authored_rgba) != 4:
        fail("target TextRender colour must contain four channels")
    # Keywords are mandatory: UE 5.8's positional order is b, g, r, a.
    return ue.Color(
        b=int(authored_rgba[2]),
        g=int(authored_rgba[1]),
        r=int(authored_rgba[0]),
        a=int(authored_rgba[3]),
    )


def _readback_no_collision(
    actor: Any, component: Any, item_id: str, context: str
) -> Dict[str, Any]:
    ue = _require_unreal()
    if bool(actor.get_actor_enable_collision()):
        fail("{} retained actor collision: {}".format(context, item_id))
    enabled = str(component.get_collision_enabled())
    if "NO_COLLISION" not in enabled.upper():
        fail("{} retained component collision: {}".format(context, item_id))
    profile = str(component.get_collision_profile_name())
    normalised_profile = "".join(
        character.lower() for character in profile if character.isalnum()
    )
    if normalised_profile not in {"nocollision", "custom"}:
        fail("{} profile is neither NoCollision nor Custom: {}".format(context, item_id))
    ignored = []
    for channel_name in COLLISION_CHANNEL_NAMES:
        channel = getattr(ue.CollisionChannel, channel_name)
        response = str(component.get_collision_response_to_channel(channel))
        if "ECR_IGNORE" not in response.upper():
            fail("{} does not ignore {}: {}".format(context, channel_name, item_id))
        ignored.append(channel_name)
    overlap = bool(component.get_editor_property("generate_overlap_events"))
    affects_navigation = bool(component.get_editor_property("can_ever_affect_navigation"))
    if overlap or affects_navigation:
        fail("{} retained overlap/navigation participation: {}".format(context, item_id))
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
        "generate_overlap_events": overlap,
        "can_ever_affect_navigation": affects_navigation,
    }


def _assert_source_actor(actor: Any, mutation: Mapping[str, Any]) -> None:
    source = mutation["source"]
    item_id = str(mutation["id"])
    kind = str(mutation["kind"])
    if str(actor.get_actor_label()) != str(source["label"]):
        fail("source presentation label changed: " + item_id)
    tags = {str(tag) for tag in list(actor.tags or [])}
    if PRESENTATION_PASS_TAG not in tags:
        fail("source presentation tag missing: " + item_id)
    transform = _actor_transform_record(actor)
    if kind == "box":
        if str(actor.get_class().get_path_name()) != STATIC_MESH_ACTOR_CLASS_PATH:
            fail("source presentation box class changed: " + item_id)
        expected_rotation = [0.0, float(source["yaw_deg"]), 0.0]
        expected_scale = [float(value) / 100.0 for value in source["dimensions_cm"]]
        if (
            not _close(transform["location_cm"], source["location_cm"])
            or not _rotation_close(transform["rotation_deg_pitch_yaw_roll"], expected_rotation)
            or not _close(transform["scale3d"], expected_scale)
        ):
            fail("source presentation box transform changed: " + item_id)
        component = actor.get_editor_property("static_mesh_component")
        if (
            component is None
            or _asset_path(component.get_editor_property("static_mesh"))
            != _asset_path(CUBE_ASSET)
            or _component_material_path(component) != _asset_path(source["material"])
        ):
            fail("source presentation box asset assignment changed: " + item_id)
        _readback_no_collision(actor, component, item_id, "source presentation box")
    elif kind == "text":
        if str(actor.get_class().get_path_name()) != TEXT_RENDER_ACTOR_CLASS_PATH:
            fail("source TextRender class changed: " + item_id)
        component = actor.get_editor_property("text_render")
        if component is None:
            fail("source TextRender component is missing: " + item_id)
        if not _close(transform["location_cm"], source["location_cm"]):
            fail("source TextRender location changed: " + item_id)
        if not _rotation_close(
            transform["rotation_deg_pitch_yaw_roll"],
            source["rotation_deg_pitch_yaw_roll"],
        ):
            fail("source TextRender rotation changed: " + item_id)
        if str(component.get_editor_property("text")) != str(source["text"]):
            fail("source TextRender text changed: " + item_id)
        if (
            abs(
                float(component.get_editor_property("world_size"))
                - float(source["world_size_cm"])
            )
            > NUMERIC_TOLERANCE
        ):
            fail("source TextRender world size changed: " + item_id)
        expected_legacy_colour = _legacy_positional_unreal_color_readback_rgba(
            source["colour_rgba"]
        )
        actual_colour = _colour_rgba(component)
        if actual_colour != expected_legacy_colour:
            fail(
                "source TextRender legacy colour readback changed: {}; expected={}; "
                "actual={}".format(item_id, expected_legacy_colour, actual_colour)
            )
        _readback_no_collision(actor, component, item_id, "source TextRender")
    elif kind == "camera":
        if str(actor.get_class().get_path_name()) != CAMERA_ACTOR_CLASS_PATH:
            fail("source camera class changed: " + item_id)
        component = actor.get_editor_property("camera_component")
        if (
            component is None
            or not _close(transform["location_cm"], source["location_cm"])
            or not _rotation_close(
                transform["rotation_deg_pitch_yaw_roll"],
                source["rotation_deg_pitch_yaw_roll"],
            )
            or abs(float(component.get_editor_property("ortho_width")) - float(source["ortho_width_cm"]))
            > NUMERIC_TOLERANCE
        ):
            fail("source camera contract changed: " + item_id)
    else:
        fail("unknown upgrade mutation kind: " + kind)


def _append_unique_tags(actor: Any, values: Sequence[str]) -> None:
    ue = _require_unreal()
    tags = list(actor.tags or [])
    existing = {str(tag) for tag in tags}
    for value in values:
        if value not in existing:
            tags.append(ue.Name(value))
            existing.add(value)
    actor.tags = tags


def _replace_exact_role_tag(actor: Any, role: str) -> str:
    ue = _require_unreal()
    prefix = "LB.PressShop.OverheadDeck.Role."
    expected = prefix + role
    retained = [tag for tag in list(actor.tags or []) if not str(tag).startswith(prefix)]
    retained.append(ue.Name(expected))
    actor.tags = retained
    role_tags = sorted(
        str(tag) for tag in list(actor.tags or []) if str(tag).startswith(prefix)
    )
    if role_tags != [expected]:
        fail("presentation box role-tag replacement failed: " + role)
    return expected


def _replace_exact_camera_role_tag(actor: Any, role_tag: str) -> None:
    ue = _require_unreal()
    role_prefixes = (
        "LB.PressShop.OverheadDeck.Camera.Overview.",
        "LB.PressShop.OverheadDeck.Camera.PressSpine.",
        "LB.PressShop.OverheadDeck.Camera.SteamHero.",
    )
    retained = [
        tag for tag in list(actor.tags or [])
        if not str(tag).startswith(role_prefixes)
    ]
    retained.append(ue.Name(role_tag))
    actor.tags = retained
    actual = sorted(
        str(tag) for tag in list(actor.tags or []) if str(tag).startswith(role_prefixes)
    )
    if actual != [role_tag]:
        fail("saved camera role-tag replacement failed: " + role_tag)


def _apply_box_mutation(
    actor: Any, target: Mapping[str, Any], materials: Mapping[str, Any]
) -> None:
    actor.set_actor_label(str(target["label"]), mark_dirty=True)
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
    component.set_editor_property("cast_shadow", False)
    if _component_material_path(component) != material_path:
        fail("target box material readback failed: " + str(target["id"]))
    _append_unique_tags(actor, [V005_UPGRADE_TAG])
    _replace_exact_role_tag(actor, str(target["role"]))


def _apply_text_mutation(actor: Any, target: Mapping[str, Any]) -> None:
    actor.set_actor_label(str(target["label"]), mark_dirty=True)
    actor.set_actor_location(_vector(target["location_cm"]), False, False)
    actor.set_actor_rotation(_rotator(target["rotation_deg_pitch_yaw_roll"]), False)
    component = actor.get_editor_property("text_render")
    component.set_world_size(float(target["world_size_cm"]))
    rgba = [int(value) for value in target["colour_rgba"]]
    component.set_text_render_color(_unreal_color_from_rgba(rgba))
    component.set_editor_property("cast_shadow", False)
    _append_unique_tags(actor, [V005_UPGRADE_TAG])


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
    _append_unique_tags(
        actor,
        [V005_UPGRADE_TAG, CAMERA_V005_TAG],
    )
    _replace_exact_camera_role_tag(actor, str(target["role_tag"]))


def _configure_and_verify_no_collision(
    actor: Any, component: Any, item_id: str
) -> Dict[str, Any]:
    """Use the proven v004 BodyInstance order and then verify every channel."""
    ue = _require_unreal()
    actor.set_actor_enable_collision(False)
    # The project's named NoCollision profile contains blocking response metadata.
    # Apply it first, override all responses, and set NoCollision last. Unreal then
    # truthfully reads the BodyInstance profile as Custom while remaining inert.
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
    return _readback_no_collision(actor, component, item_id, "new presentation box")


def _spawn_presentation_box(
    actor_subsystem: Any,
    cube: Any,
    materials: Mapping[str, Any],
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
        fail("could not spawn v005 presentation box: " + str(spec["id"]))
    actor.set_actor_label(str(spec["label"]), mark_dirty=True)
    actor.tags = [
        ue.Name(PRESENTATION_PASS_TAG),
        ue.Name(VISUAL_ONLY_TAG),
        ue.Name(NOT_WIP_TAG),
        ue.Name(ROOFLESS_TAG),
        ue.Name(V005_UPGRADE_TAG),
    ]
    exact_role_tag = _replace_exact_role_tag(actor, str(spec["role"]))
    component = actor.get_editor_property("static_mesh_component")
    if component is None or not component.set_static_mesh(cube):
        fail("could not assign native cube: " + str(spec["id"]))
    actor.set_actor_scale3d(_vector([
        float(spec["dimensions_cm"][0]) / 100.0,
        float(spec["dimensions_cm"][1]) / 100.0,
        float(spec["dimensions_cm"][2]) / 100.0,
    ]))
    material_path = _asset_path(spec["material"])
    if material_path not in materials:
        fail("new presentation box material was not preflighted: " + str(spec["id"]))
    component.set_material(0, materials[str(material_path)])
    component.set_editor_property("cast_shadow", False)
    collision = _configure_and_verify_no_collision(actor, component, str(spec["id"]))
    transform = _actor_transform_record(actor)
    expected_scale = [float(value) / 100.0 for value in spec["dimensions_cm"]]
    if (
        _asset_path(component.get_editor_property("static_mesh")) != _asset_path(CUBE_ASSET)
        or _component_material_path(component) != material_path
        or not _close(transform["location_cm"], spec["location_cm"])
        or not _rotation_close(
            transform["rotation_deg_pitch_yaw_roll"],
            [0.0, float(spec["yaw_deg"]), 0.0],
        )
        or not _close(transform["scale3d"], expected_scale)
    ):
        fail("new presentation box asset/transform readback failed: " + str(spec["id"]))
    return actor, {
        **copy.deepcopy(dict(spec)),
        "actor_path": str(actor.get_path_name()),
        "mesh": _asset_path(CUBE_ASSET),
        "collision": "NoCollision",
        "collision_readback": collision,
        "cast_shadow": False,
        "visual_only": True,
        "process_wip": False,
        "cargo_geometry": False,
        "machine_geometry": False,
        "exact_role_tag": exact_role_tag,
    }


def _verify_target_actor(actor: Any, mutation: Mapping[str, Any]) -> Dict[str, Any]:
    target = mutation["target"]
    item_id = str(mutation["id"])
    kind = str(mutation["kind"])
    transform = _actor_transform_record(actor)
    tags = {str(tag) for tag in list(actor.tags or [])}
    if V005_UPGRADE_TAG not in tags:
        fail("v005 provenance tag missing: " + item_id)
    if str(actor.get_actor_label()) != str(target["label"]):
        fail("v005 actor label readback changed: " + item_id)
    collision_readback = None
    exact_role_tag = None
    if kind == "box":
        expected_scale = [float(value) / 100.0 for value in target["dimensions_cm"]]
        component = actor.get_editor_property("static_mesh_component")
        if (
            not _close(transform["location_cm"], target["location_cm"])
            or not _rotation_close(
                transform["rotation_deg_pitch_yaw_roll"],
                [0.0, float(target["yaw_deg"]), 0.0],
            )
            or not _close(transform["scale3d"], expected_scale)
            or _component_material_path(component) != _asset_path(target["material"])
        ):
            fail("v005 box readback changed: " + item_id)
        collision_readback = _readback_no_collision(
            actor, component, item_id, "mutated v005 box"
        )
        exact_role_tag = "LB.PressShop.OverheadDeck.Role." + str(target["role"])
        actual_role_tags = sorted(
            str(tag) for tag in list(actor.tags or [])
            if str(tag).startswith("LB.PressShop.OverheadDeck.Role.")
        )
        if actual_role_tags != [exact_role_tag]:
            fail("v005 box retained a stale role tag: " + item_id)
    elif kind == "text":
        component = actor.get_editor_property("text_render")
        if (
            not _close(transform["location_cm"], target["location_cm"])
            or not _rotation_close(
                transform["rotation_deg_pitch_yaw_roll"],
                target["rotation_deg_pitch_yaw_roll"],
            )
            or str(component.get_editor_property("text")) != str(target["text"])
            or abs(float(component.get_editor_property("world_size")) - float(target["world_size_cm"]))
            > NUMERIC_TOLERANCE
            or _colour_rgba(component) != [int(value) for value in target["colour_rgba"]]
        ):
            fail("v005 TextRender readback changed: " + item_id)
        collision_readback = _readback_no_collision(
            actor, component, item_id, "mutated v005 TextRender"
        )
    elif kind == "camera":
        component = actor.get_editor_property("camera_component")
        if (
            not _close(transform["location_cm"], target["location_cm"])
            or not _rotation_close(
                transform["rotation_deg_pitch_yaw_roll"], CAMERA_ROTATION
            )
            or abs(float(component.get_editor_property("ortho_width")) - float(target["ortho_width_cm"]))
            > NUMERIC_TOLERANCE
            or abs(float(component.get_editor_property("aspect_ratio")) - CAMERA_ASPECT)
            > NUMERIC_TOLERANCE
            or not bool(component.get_editor_property("constrain_aspect_ratio"))
            or "ORTHOGRAPHIC" not in str(
                component.get_editor_property("projection_mode")
            ).upper()
        ):
            fail("v005 camera readback changed: " + item_id)
    else:
        fail("unknown upgrade mutation kind: " + kind)
    return {
        "id": item_id,
        "kind": kind,
        "actor_path": str(actor.get_path_name()),
        "source_label": str(mutation["source"]["label"]),
        "target_label": str(target["label"]),
        "target_location_cm": list(target["location_cm"]),
        "target_rotation_deg_pitch_yaw_roll": (
            list(target["rotation_deg_pitch_yaw_roll"])
            if kind != "box" else [0.0, float(target["yaw_deg"]), 0.0]
        ),
        "target_dimensions_cm": list(target["dimensions_cm"]) if kind == "box" else None,
        "target_ortho_width_cm": float(target["ortho_width_cm"]) if kind == "camera" else None,
        "target_world_size_cm": float(target["world_size_cm"]) if kind == "text" else None,
        "target_colour_rgba": list(target["colour_rgba"]) if kind == "text" else None,
        "source_receipt_intent_colour_rgba": (
            list(mutation["source"]["colour_rgba"]) if kind == "text" else None
        ),
        "source_verified_legacy_colour_readback_rgba": (
            _legacy_positional_unreal_color_readback_rgba(
                mutation["source"]["colour_rgba"]
            )
            if kind == "text" else None
        ),
        "target_colour_authoring": (
            "unreal.Color(b=,g=,r=,a=) keyword" if kind == "text" else None
        ),
        "target_material": _asset_path(target["material"]) if kind == "box" else None,
        "exact_role_tag": exact_role_tag,
        "collision": "NoCollision" if collision_readback is not None else None,
        "collision_readback": collision_readback,
    }


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(canonical_json_bytes(value))
    except FileExistsError:
        fail("v005 install receipt already exists; refusing overwrite")


def main() -> None:
    ue = _require_unreal()
    inputs = validate_offline_contract()
    plan = inputs["plan"]
    protected_before = inputs["protected_hashes"]

    if INSTALL_RECEIPT.exists():
        fail("v005 install receipt already exists; refusing rerun")
    if TARGET_FILE.exists() or TARGET_ROOT_DISK.exists():
        fail("v005 target exists on disk; refusing overwrite")
    if ue.EditorAssetLibrary.does_asset_exist(TARGET_MAP):
        fail("v005 target exists in the asset registry; refusing overwrite")
    if ue.EditorAssetLibrary.list_assets(
        TARGET_ROOT, recursive=True, include_folder=False
    ):
        fail("v005 target root is not empty in the asset registry")
    _assert_dirty_packages(
        {"content": [], "maps": []},
        "editor has dirty packages before v005 target creation",
    )
    world_before = _editor_world()
    world_before_name = _world_package_name(world_before)
    if world_before_name in {SOURCE_MAP, TARGET_MAP, V002_MAP, V003_MAP}:
        fail("run the v005 installer from an unrelated clean editor world")

    loaded_assets: Dict[str, Any] = {}
    for asset_path in (CUBE_ASSET, *REUSED_MATERIAL_LOCKS.keys()):
        if not ue.EditorAssetLibrary.does_asset_exist(asset_path):
            fail("required native presentation asset is not registered: " + asset_path)
        asset = ue.EditorAssetLibrary.load_asset(asset_path)
        if asset is None:
            fail("required native presentation asset could not load: " + asset_path)
        loaded_assets[asset_path] = asset
    if str(loaded_assets[CUBE_ASSET].get_class().get_name()) != "StaticMesh":
        fail("native cube asset has the wrong class")
    for material_path in REUSED_MATERIAL_LOCKS:
        if "Material" not in str(loaded_assets[material_path].get_class().get_name()):
            fail("reused presentation material has the wrong class: " + material_path)
    _assert_dirty_packages(
        {"content": [], "maps": []},
        "v005 asset preflight dirtied packages",
    )
    if protected_snapshot() != protected_before:
        fail("protected maps changed during v005 asset preflight")

    level_subsystem = _level_subsystem()
    actor_subsystem = _actor_subsystem()
    # First map mutation: create a distinct candidate from the unopened,
    # immutable and hash-locked v004 package. The source is never saved.
    if not level_subsystem.new_level_from_template(TARGET_MAP, SOURCE_MAP):
        fail("could not clone v004 map to the v005 presentation candidate")
    world = _editor_world()
    if _world_package_name(world) != TARGET_MAP:
        fail("v005 target did not become the active editor world")
    game_mode_before = _world_game_mode_path(world)
    if game_mode_before != EXPECTED_GAME_MODE:
        fail("v005 clone changed the OneFactory GameMode")

    source_actors = list(actor_subsystem.get_all_level_actors() or [])
    inventory = validate_source_actor_inventory(source_actors)
    actors_by_label: Dict[str, List[Any]] = {}
    for actor in source_actors:
        actors_by_label.setdefault(str(actor.get_actor_label()), []).append(actor)
    mutation_labels = {str(row["source"]["label"]) for row in plan["mutations"]}
    if not mutation_labels <= set(actors_by_label):
        fail("one or more exact v004 presentation mutation targets are missing")
    duplicate_targets = sorted(
        label for label in mutation_labels if len(actors_by_label[label]) != 1
    )
    if duplicate_targets:
        fail("exact v004 presentation mutation label is not unique: " + duplicate_targets[0])
    new_labels = {str(row["label"]) for row in plan["additions"]}
    if new_labels & set(actors_by_label):
        fail("v005 presentation addition label collides with a source actor")
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
    machinery_before = {
        path: record
        for path, record in visual_before.items()
        if CARGO_MAP_TAG not in set(record["tags"])
    }
    if len(preserved_nonpresentation) != EXPECTED_PRESERVED_NONPRESENTATION_COUNT:
        fail("preserved nonpresentation actor count changed before v005 upgrade")
    if len(unchanged_presentation) != EXPECTED_UNCHANGED_PRESENTATION_COUNT:
        fail("unchanged presentation actor count changed before v005 upgrade")
    if len(cargo_before) != EXPECTED_CARGO_LAYER_COUNT:
        fail("cargo fingerprint count changed before v005 upgrade")
    if len(visual_before) != EXPECTED_COMBINED_VISUAL_LAYER_COUNT:
        fail("visual-layer fingerprint count changed before v005 upgrade")
    if len(machinery_before) != EXPECTED_BASE_VISUAL_LAYER_COUNT:
        fail("machine visual-layer fingerprint count changed before v005 upgrade")

    created_material_records: List[Dict[str, Any]] = []
    for spec in NEW_MATERIAL_SPECS:
        material, record = _create_unlit_material(spec)
        loaded_assets[str(spec["asset"])] = material
        created_material_records.append(record)
        _validate_post_material_dirty_packages(
            dirty_package_paths(),
            "unsafe dirty packages after v005 material save: " + str(spec["id"]),
        )
        if protected_snapshot() != protected_before:
            fail("protected maps changed during v005 material creation")

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
        else:  # Offline validation makes this unreachable.
            fail("unknown v005 mutation kind")
        mutation_records.append(_verify_target_actor(actor, mutation))
    mutated_primitive_records = [
        row for row in mutation_records if row["kind"] in {"box", "text"}
    ]
    if (
        len(mutated_primitive_records) != 58
        or any(row.get("collision") != "NoCollision" for row in mutated_primitive_records)
        or any(not isinstance(row.get("collision_readback"), dict)
               for row in mutated_primitive_records)
    ):
        fail("mutated presentation primitive collision evidence is incomplete")

    new_actors: List[Any] = []
    new_actor_records: List[Dict[str, Any]] = []
    for spec in plan["additions"]:
        actor, record = _spawn_presentation_box(
            actor_subsystem,
            loaded_assets[CUBE_ASSET],
            loaded_assets,
            spec,
        )
        new_actors.append(actor)
        new_actor_records.append(record)

    final_actors = list(actor_subsystem.get_all_level_actors() or [])
    if len(final_actors) != EXPECTED_FINAL_ACTOR_COUNT:
        fail("v005 final actor count changed")
    final_by_path = _records_by_path(final_actors)
    for path, before in preserved_nonpresentation.items():
        if final_by_path.get(path) != before:
            fail("preserved source/machinery/cargo actor changed during v005: " + path)
    for path, before in unchanged_presentation.items():
        if final_by_path.get(path) != before:
            fail("unselected presentation actor changed during v005: " + path)
    for path, before in cargo_before.items():
        if final_by_path.get(path) != before:
            fail("cargo actor fingerprint changed during v005: " + path)
    for path, before in visual_before.items():
        if final_by_path.get(path) != before:
            fail("machine/cargo visual fingerprint changed during v005: " + path)

    final_records = list(final_by_path.values())
    exact_final_tags = {
        VISUAL_LAYER_TAG: EXPECTED_COMBINED_VISUAL_LAYER_COUNT,
        CARGO_MAP_TAG: EXPECTED_CARGO_LAYER_COUNT,
        CARGO_SOURCE_TAG: EXPECTED_CARGO_LAYER_COUNT,
        PRESENTATION_ADAPTER_TAG: EXPECTED_RUNTIME_PRESENTATION_COUNT,
        PRESENTATION_PASS_TAG: EXPECTED_SOURCE_PRESENTATION_COUNT + EXPECTED_NEW_BOX_COUNT,
        PRESENTATION_CAMERA_TAG: EXPECTED_SOURCE_CAMERA_COUNT,
        CAMERA_V005_TAG: EXPECTED_SOURCE_CAMERA_COUNT,
        V004_POLISH_TAG: 41,
        V005_UPGRADE_TAG: EXPECTED_EXISTING_MUTATION_COUNT + EXPECTED_NEW_BOX_COUNT,
    }
    for tag, expected in exact_final_tags.items():
        if _count_tag(final_records, tag) != expected:
            fail("v005 final actor tag count changed: " + tag)
    new_paths = {str(actor.get_path_name()) for actor in new_actors}
    if len(new_paths) != EXPECTED_NEW_BOX_COUNT:
        fail("v005 new actor paths are missing or duplicated")
    for path in new_paths:
        row = final_by_path[path]
        tags = set(row["tags"])
        role_tags = sorted(
            tag for tag in tags
            if tag.startswith("LB.PressShop.OverheadDeck.Role.")
        )
        if (
            row["class_path"] != STATIC_MESH_ACTOR_CLASS_PATH
            or PRESENTATION_PASS_TAG not in tags
            or VISUAL_ONLY_TAG not in tags
            or NOT_WIP_TAG not in tags
            or V005_UPGRADE_TAG not in tags
            or CARGO_MAP_TAG in tags
            or CARGO_SOURCE_TAG in tags
            or row["actor_collision_enabled"]
            or len(role_tags) != 1
        ):
            fail("new v005 actor escaped the visual-only native-box contract: " + path)
    if _world_game_mode_path(world) != game_mode_before:
        fail("v005 presentation upgrade changed the local GameMode")

    dirty_before_save = _assert_dirty_packages(
        {"content": [], "maps": [TARGET_MAP]},
        "only the v005 target map may be dirty before save",
    )
    if not level_subsystem.save_current_level():
        fail("could not save the v005 presentation candidate")
    dirty_after_save = _assert_dirty_packages(
        {"content": [], "maps": []},
        "v005 candidate packages remain dirty after explicit save",
    )
    if not TARGET_FILE.is_file():
        fail("v005 target map package is missing after save")

    protected_after = protected_snapshot()
    if protected_after != protected_before:
        fail("protected map changed during v005 presentation upgrade")
    immutable_receipts = {
        SOURCE_RECEIPT: SOURCE_RECEIPT_SHA256,
        V003_RECEIPT: V003_RECEIPT_SHA256,
        V002_RECEIPT: V002_RECEIPT_SHA256,
        CARGO_IMPORT_RECEIPT: CARGO_IMPORT_RECEIPT_SHA256,
        SOURCE_CAPTURE_RECEIPT: SOURCE_CAPTURE_RECEIPT_SHA256,
    }
    for path, expected_hash in immutable_receipts.items():
        if not path.is_file() or digest(path) != expected_hash:
            fail("immutable source evidence changed during v005: " + path.as_posix())
    if validate_reused_material_locks() != inputs["material_hashes"]:
        fail("reused presentation material changed during v005")
    validate_cargo_import_receipt()
    for record in created_material_records:
        disk = virtual_to_uasset(str(record["asset"]))
        if (
            not disk.is_file()
            or digest(disk) != record["sha256"]
            or disk.stat().st_size != record["bytes"]
        ):
            fail("created v005 material changed after explicit save: " + str(record["asset"]))

    preserved_hash = _fingerprint_hash(preserved_nonpresentation)
    unchanged_hash = _fingerprint_hash(unchanged_presentation)
    cargo_hash = _fingerprint_hash(cargo_before)
    visual_hash = _fingerprint_hash(visual_before)
    machinery_hash = _fingerprint_hash(machinery_before)
    role_counts: Dict[str, int] = {}
    for row in new_actor_records:
        role = str(row["role"])
        role_counts[role] = role_counts.get(role, 0) + 1
    receipt = {
        "schema": INSTALL_RECEIPT_SCHEMA,
        "status": INSTALL_STATUS,
        "candidate_only": True,
        "source_map": SOURCE_MAP,
        "source_map_sha256": SOURCE_FILE_SHA256,
        "source_map_bytes": SOURCE_FILE_BYTES,
        "source_receipt": SOURCE_RECEIPT.as_posix(),
        "source_receipt_sha256": SOURCE_RECEIPT_SHA256,
        "v003_cargo_receipt": V003_RECEIPT.as_posix(),
        "v003_cargo_receipt_sha256": V003_RECEIPT_SHA256,
        "v002_presentation_receipt": V002_RECEIPT.as_posix(),
        "v002_presentation_receipt_sha256": V002_RECEIPT_SHA256,
        "cargo_import_receipt": CARGO_IMPORT_RECEIPT.as_posix(),
        "cargo_import_receipt_sha256": CARGO_IMPORT_RECEIPT_SHA256,
        "source_saved_map_capture_receipt": SOURCE_CAPTURE_RECEIPT.as_posix(),
        "source_saved_map_capture_receipt_sha256": SOURCE_CAPTURE_RECEIPT_SHA256,
        "target_map": TARGET_MAP,
        "target_map_sha256": digest(TARGET_FILE),
        "target_map_bytes": TARGET_FILE.stat().st_size,
        "target_creation_api": "LevelEditorSubsystem.new_level_from_template",
        "source_actor_count": EXPECTED_SOURCE_ACTOR_COUNT,
        "final_actor_count": EXPECTED_FINAL_ACTOR_COUNT,
        "source_presentation_actor_count": EXPECTED_SOURCE_PRESENTATION_COUNT,
        "final_presentation_actor_count": (
            EXPECTED_SOURCE_PRESENTATION_COUNT + EXPECTED_NEW_BOX_COUNT
        ),
        "preserved_nonpresentation_actor_count": len(preserved_nonpresentation),
        "preserved_nonpresentation_actor_fingerprints_before_sha256": preserved_hash,
        "preserved_nonpresentation_actor_fingerprints_after_sha256": preserved_hash,
        "unchanged_presentation_actor_count": len(unchanged_presentation),
        "unchanged_presentation_actor_fingerprints_before_sha256": unchanged_hash,
        "unchanged_presentation_actor_fingerprints_after_sha256": unchanged_hash,
        "combined_visual_layer_count": EXPECTED_COMBINED_VISUAL_LAYER_COUNT,
        "visual_layer_actor_fingerprints_before_sha256": visual_hash,
        "visual_layer_actor_fingerprints_after_sha256": visual_hash,
        "machinery_visual_layer_count": EXPECTED_BASE_VISUAL_LAYER_COUNT,
        "machinery_actor_fingerprints_before_sha256": machinery_hash,
        "machinery_actor_fingerprints_after_sha256": machinery_hash,
        "cargo_layer_count": EXPECTED_CARGO_LAYER_COUNT,
        "cargo_actor_fingerprints_before_sha256": cargo_hash,
        "cargo_actor_fingerprints_after_sha256": cargo_hash,
        "cargo_actor_mutated_count": 0,
        "machinery_actor_mutated_count": 0,
        "source_actor_removed_count": 0,
        "source_actor_created_count": EXPECTED_NEW_BOX_COUNT,
        "mutated_existing_presentation_actor_count": len(mutation_records),
        "created_presentation_box_count": len(new_actor_records),
        "presentation_mutations": mutation_records,
        "created_presentation_boxes": new_actor_records,
        "created_presentation_box_role_counts": role_counts,
        "plan_validation": inputs["validation"],
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "reused_presentation_material_hashes_before": inputs["material_hashes"],
        "reused_presentation_material_hashes_after": validate_reused_material_locks(),
        "created_materials": created_material_records,
        "presentation_style": {
            "full_deck_material": SLATE_MATERIAL,
            "full_deck_srgb_hex": REUSED_MATERIAL_SRGB_HEX[SLATE_MATERIAL],
            "floor_band_material": FLOOR_BAND_MATERIAL,
            "floor_band_srgb_hex": "#294A46",
            "route_bed_material": ROUTE_TEAL_MATERIAL,
            "route_bed_srgb_hex": "#3B8177",
            "station_zone_material": ZONE_MATERIAL,
            "station_zone_srgb_hex": REUSED_MATERIAL_SRGB_HEX[ZONE_MATERIAL],
            "route_rail_and_port_material": CREAM_MATERIAL,
            "label_plaque_material": CHARCOAL_MATERIAL,
            "new_material_shading_model": "UNLIT",
            "external_texture_assets": [],
            "lights_created": 0,
            "exposure_mutated": False,
        },
        "collision_enabled_on_created_presentation": False,
        "created_collision_readback_count": len(new_actor_records),
        "collision_enabled_on_mutated_presentation_primitives": False,
        "mutated_primitive_collision_readback_count": len(mutated_primitive_records),
        "source_map_mutated": False,
        "protected_authority_map_mutated": False,
        "native_cpp_modified": False,
        "roof_created": False,
        "new_machinery_geometry": 0,
        "new_cargo_geometry": 0,
        "empty_shuttle_visual_geometry": 9,
        "machine_or_cargo_transform_mutations": 0,
        "game_mode_before": game_mode_before,
        "game_mode_after": _world_game_mode_path(world),
        "dirty_packages_before_save": dirty_before_save,
        "dirty_packages_after_save": dirty_after_save,
        "runtime_validated": False,
        "pie_validated": False,
        "cook_validated": False,
        "packaged_build_validated": False,
        "visual_capture_validated": False,
        "steam_capture_validated": False,
        "steam_visual_quality_human_approved": False,
        "honest_status": (
            "The isolated v005 candidate preserves every v004 nonpresentation, machine "
            "and cargo actor fingerprint while installing the offline-reviewed native "
            "presentation upgrade. Camera/deck occupancy values are deterministic design "
            "metrics only. Fresh saved-map capture at 1920x1080, exact-map PIE lifecycle, "
            "cook, packaged behavior and Steam visual-quality approval remain required."
        ),
    }
    _write_new_json(INSTALL_RECEIPT, receipt)
    ue.log(
        "PRESSSHOP_2126_OVERHEAD_PRESENTATION_UPGRADE_V001_PASS map={} receipt={}".format(
            TARGET_MAP, INSTALL_RECEIPT.as_posix()
        )
    )
    ue.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
