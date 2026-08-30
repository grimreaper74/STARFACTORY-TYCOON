"""Guarded v006 presentation correction for the Press Shop 2126 overhead map.

The one-shot Unreal Editor tool clones the immutable, captured v005 candidate
into a new v006 candidate.  It changes only presentation geometry, 15 TextRender
labels, and three saved orthographic cameras.  The presentation geometry pass
directly reduces the existing station zones and route hierarchy; it does not add
or alter machine or cargo geometry.  Every one of the 146 machinery/cargo visual
actors is fingerprint-locked at asset, transform, material, collision, tag and
visual-metadata level.

The twelve station footprints use measured per-machine depths, muted candidate-
only unlit colours, and the existing twelve route ports remain exactly zero-gap.
No light, exposure, gameplay, native C++, roof, machine, cargo, or protected
authority package is changed.

The module is deliberately importable in ordinary CPython.  ``main`` is the
only Unreal mutation entry point.  A new saved-map capture, PIE, cook, packaged
run, performance proof and Steam visual approval remain downstream gates.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

try:  # Ordinary CPython is the intended offline-test environment.
    import unreal  # type: ignore
except ModuleNotFoundError:  # pragma: no cover
    unreal = None  # type: ignore


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
TOOLS = PROJECT / "Tools"
V005_HELPER = TOOLS / "install_pressshop_2126_overhead_presentation_upgrade_v001.py"
V005_HELPER_SHA256 = "6478f814b39628c2b6629e06673efad0cd0aede185ed737409420a6680f243c2"
V005_HELPER_BYTES = 141800


def _bootstrap_digest(path: Path) -> str:
    """Hash the shared helper before importing any of its executable code."""
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest().lower()


def _load_v005_helper() -> Any:
    if (not V005_HELPER.is_file()
            or V005_HELPER.stat().st_size != V005_HELPER_BYTES
            or _bootstrap_digest(V005_HELPER) != V005_HELPER_SHA256):
        raise RuntimeError("locked v005 helper changed before import; refusing execution")
    spec = importlib.util.spec_from_file_location("pressshop_presentation_v005_locked", V005_HELPER)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not create the locked v005 helper import spec")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_v005 = _load_v005_helper()

SOURCE_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPresentation_v005"
SOURCE_MAP = SOURCE_ROOT + "/Maps/LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v005"
SOURCE_FILE = (
    PROJECT / "Content/LineBoss/Candidates/PressShop"
    / "PressShop2126_OverheadPresentation_v005/Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v005.umap"
)
SOURCE_FILE_SHA256 = "4d3ce8973cc7bede00f0204a1e653117935cfc9f120fac8b6a939510ad01fe4b"
SOURCE_FILE_BYTES = 1694902
SOURCE_RECEIPT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadPresentation_v005"
    / "install_receipt_v001.json"
)
SOURCE_RECEIPT_SHA256 = "cf13095f09fbf1422b7ee4a41c8f45ca36ceb016af096abf73ccf2aae9eb4246"
SOURCE_RECEIPT_SCHEMA = "cairnwell.press_shop.overhead_presentation_upgrade_install_receipt.v001"
SOURCE_RECEIPT_STATUS = (
    "PASS_CANDIDATE_PRESENTATION_UPGRADE_APPLIED__V004_FINGERPRINTS_PRESERVED__"
    "VISUAL_CAPTURE_AND_PIE_PENDING"
)

SOURCE_CAPTURE_ROOT = (
    PROJECT / "Saved/PressShop2126/OverheadPresentation_v005_SavedMapCapture_v001"
)
SOURCE_CAPTURE_RECEIPT = SOURCE_CAPTURE_ROOT / "saved_map_capture_receipt_v001.json"
SOURCE_CAPTURE_RECEIPT_SHA256 = "036d2b5ddbd7a93728765e6c78dac641ad84c3de19795e10c94afd251c3aa1fc"
SOURCE_CAPTURE_SCHEMA = (
    "cairnwell.press_shop.overhead_presentation_v005_saved_map_capture_receipt.v001"
)
SOURCE_CAPTURE_STATUS = (
    "PASS_IN_ENGINE_V005_SAVED_MAP_PRESENTATION_CAPTURE__"
    "PIE_LIFECYCLE_AND_STEAM_APPROVAL_PENDING"
)
SOURCE_CAPTURE_LOCKS: Mapping[str, Mapping[str, Any]] = {
    "PressShop2126_PresentationOverview_1920x1080_v005.png": {
        "sha256": "ff5245dbcd512a5954cbb8adcc04a22e1e9434abc42f0dee1dc2ab65dd4da23f",
        "bytes": 2244875,
        "camera_id": "overview",
    },
    "PressShop2126_PresentationSpine_1920x1080_v005.png": {
        "sha256": "0bbd091d397dd543db63176e5e5a51ed9e50d3df882aa63f85446ec503078843",
        "bytes": 2244875,
        "camera_id": "press_spine",
    },
    "PressShop2126_PresentationPressHero_1920x1080_v005.png": {
        "sha256": "87dcc5e64c2fc099f1aeb56e5edb0064ed827ef826cdfc61f0a68e45eefea6a8",
        "bytes": 2244875,
        "camera_id": "steam_hero",
    },
}

TARGET_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPresentation_v006"
TARGET_MAP = TARGET_ROOT + "/Maps/LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v006"
TARGET_ROOT_DISK = (
    PROJECT / "Content/LineBoss/Candidates/PressShop"
    / "PressShop2126_OverheadPresentation_v006"
)
TARGET_FILE = (
    TARGET_ROOT_DISK / "Maps/LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v006.umap"
)
INSTALL_RECEIPT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadPresentation_v006"
    / "install_receipt_v001.json"
)
INSTALL_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.overhead_presentation_correction_install_receipt.v001"
)
INSTALL_STATUS = (
    "PASS_CANDIDATE_PRESENTATION_CORRECTION_APPLIED__V005_VISUALS_PRESERVED__"
    "FRESH_CAPTURE_AND_PIE_PENDING"
)

EXPECTED_GAME_MODE = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
EXPECTED_SOURCE_ACTOR_COUNT = 302
EXPECTED_SOURCE_PRESENTATION_COUNT = 140
EXPECTED_FINAL_ACTOR_COUNT = 302
EXPECTED_FINAL_PRESENTATION_COUNT = 140
EXPECTED_VISUAL_COUNT = 146
EXPECTED_MACHINERY_COUNT = 120
EXPECTED_CARGO_COUNT = 26
EXPECTED_UNCHANGED_V005_PRESENTATION_COUNT = 24
EXPECTED_TEXT_MUTATION_COUNT = 15
EXPECTED_CAMERA_MUTATION_COUNT = 3
EXPECTED_ZONE_MUTATION_COUNT = 36
EXPECTED_ROUTE_MUTATION_COUNT = 29
EXPECTED_TOTAL_MUTATION_COUNT = (
    EXPECTED_TEXT_MUTATION_COUNT + EXPECTED_CAMERA_MUTATION_COUNT
    + EXPECTED_ZONE_MUTATION_COUNT + EXPECTED_ROUTE_MUTATION_COUNT
)

EXPECTED_SOURCE_HASHES: Mapping[str, str] = {
    "preserved_nonpresentation": "1c95ea8ac9dde53a7459964675131b6809b658fe99db1eb35f80b80891a46a29",
    "unchanged_v005_presentation": "df0f0fc95c10851491b6691617ce7497f85bd2e5edbd1ce70c94087aa74430ae",
    "combined_visual": "cbd16f11462a5e33d30ed37d97be26417c6a3edab0879fd92d5d1373df772c8f",
    "machinery_visual": "719a71ebf7370ce6e91c26979acfd9186e40721f95aa89ea8c91e54618a29ed1",
    "cargo_visual": "335cfc43984a8647bf48f95a90584cbf962b05bd3060469fabed61697b8d4ae2",
}

VISUAL_LAYER_CLASS_PATH = _v005.VISUAL_LAYER_CLASS_PATH
STATIC_MESH_ACTOR_CLASS_PATH = _v005.STATIC_MESH_ACTOR_CLASS_PATH
TEXT_RENDER_ACTOR_CLASS_PATH = _v005.TEXT_RENDER_ACTOR_CLASS_PATH
CAMERA_ACTOR_CLASS_PATH = _v005.CAMERA_ACTOR_CLASS_PATH
CUBE_ASSET = _v005.CUBE_ASSET

VISUAL_LAYER_TAG = _v005.VISUAL_LAYER_TAG
PRESENTATION_PASS_TAG = _v005.PRESENTATION_PASS_TAG
PRESENTATION_CAMERA_TAG = _v005.PRESENTATION_CAMERA_TAG
PRESENTATION_ADAPTER_TAG = _v005.PRESENTATION_ADAPTER_TAG
CARGO_MAP_TAG = _v005.CARGO_MAP_TAG
CARGO_SOURCE_TAG = _v005.CARGO_SOURCE_TAG
VISUAL_ONLY_TAG = _v005.VISUAL_ONLY_TAG
NOT_WIP_TAG = _v005.NOT_WIP_TAG
ROOFLESS_TAG = _v005.ROOFLESS_TAG
V004_POLISH_TAG = _v005.V004_POLISH_TAG
V005_UPGRADE_TAG = _v005.V005_UPGRADE_TAG
V006_CORRECTION_TAG = "LB.PressShop.OverheadPresentationCorrection.v006"
CAMERA_V006_TAG = "LB.PressShop.OverheadDeck.Camera.v006"

CHARCOAL_MATERIAL = _v005.CHARCOAL_MATERIAL
CREAM_MATERIAL = _v005.CREAM_MATERIAL
ZONE_MATERIAL = _v005.ZONE_MATERIAL
YELLOW_MATERIAL = _v005.YELLOW_MATERIAL
SLATE_MATERIAL = _v005.SLATE_MATERIAL
FLOOR_BAND_MATERIAL = _v005.FLOOR_BAND_MATERIAL
ROUTE_TEAL_MATERIAL = _v005.ROUTE_TEAL_MATERIAL
REUSED_MATERIAL_LOCKS: Mapping[str, Mapping[str, Any]] = {
    **copy.deepcopy(dict(_v005.REUSED_MATERIAL_LOCKS)),
    FLOOR_BAND_MATERIAL: {
        "sha256": "c9d49d1582a63e5c11d55e68fdd0c2097596376ecbcee038d8803f4cdb8997c8",
        "bytes": 5360,
    },
    ROUTE_TEAL_MATERIAL: {
        "sha256": "5d7e2522e0cc3a23e0a79be26795eb1f0c017978c997eea95358236853b2248a",
        "bytes": 5336,
    },
}

CANDIDATE_MATERIAL_ROOT = TARGET_ROOT + "/Materials"
ZONE_MUTED_MATERIAL = (
    CANDIDATE_MATERIAL_ROOT + "/M_CA_MW_PS2126_ZoneMutedGreen_Unlit_v006"
)
ROUTE_MUTED_MATERIAL = (
    CANDIDATE_MATERIAL_ROOT + "/M_CA_MW_PS2126_RouteMutedTeal_Unlit_v006"
)
CANDIDATE_MATERIAL_SPECS: Mapping[str, Mapping[str, Any]] = {
    ZONE_MUTED_MATERIAL: {"srgb_hex": "#7A9588", "role": "station_zone"},
    ROUTE_MUTED_MATERIAL: {"srgb_hex": "#3F8F82", "role": "route"},
}

PROTECTED_MAPS: Mapping[str, Tuple[Path, str]] = {
    "source_overhead_presentation_v005": (SOURCE_FILE, SOURCE_FILE_SHA256),
    **{
        key: value for key, value in _v005.PROTECTED_MAPS.items()
        if key != "source_overhead_presentation_v005_parent"
    },
}

CAMERA_ASPECT = 16.0 / 9.0
CAMERA_ROTATION = (-90.0, 0.0, 0.0)
TEXT_ROTATION = (90.0, 180.0, 0.0)
TEXT_Z_CM = 12.0
STATION_TEXT_RGBA = (243, 241, 233, 255)
FLOW_TEXT_RGBA = (242, 195, 0, 255)
ZONE_MUTED_SRGB_HEX = "#7A9588"
ROUTE_MUTED_SRGB_HEX = "#3F8F82"
DECK_RECT = {"min_x": -12580.645880159616, "max_x": -2880.645880159617,
             "min_y": 140.21828082694265, "max_y": 17540.218280826943}

CAMERA_TARGETS: Mapping[str, Mapping[str, Any]] = {
    "overview": {
        "label": "CAM | Press Shop 2126 | complete flow overview v006",
        "location_cm": [-7436.895880159617, 8840.218280826943, 21712.544],
        "ortho_width_cm": 16200.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.Overview.v006",
    },
    "press_spine": {
        "label": "CAM | Press Shop 2126 | production spine close v006",
        "location_cm": [-8095.0, 11125.0, 21712.544],
        "ortho_width_cm": 11200.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.PressSpine.v006",
    },
    "steam_hero": {
        "label": "CAM | Press Shop 2126 | S03-S06 framed Steam hero v006",
        "location_cm": [-8855.75, 11092.0, 21712.544],
        "ortho_width_cm": 5700.0,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.SteamHero.v006",
    },
}

STATION_IDS = (
    "IN01", "IN02", "IN03", "IN04_05", "S01", "S02",
    "S03", "S04", "S05", "S06", "S07_INSPECT", "S07_PALLET",
)
PRESS_STATIONS = {"S03", "S04", "S05", "S06"}
ZONE_DEPTH_SPECS: Mapping[str, Mapping[str, float]] = {
    "IN01": {"pad_depth": 700.0, "west_x": -9390.75, "east_x": -8240.75,
             "east_depth": 800.0},
    "IN02": {"pad_depth": 700.0, "west_x": -9390.75, "east_x": -8240.75,
             "east_depth": 800.0},
    "IN03": {"pad_depth": 1000.0, "west_x": -9540.75, "east_x": -8165.75,
             "east_depth": 650.0},
    "IN04_05": {"pad_depth": 700.0, "west_x": -9390.75, "east_x": -8240.75,
                 "east_depth": 800.0},
    "S01": {"pad_depth": 900.0, "west_x": -9490.75, "east_x": -8190.75,
            "east_depth": 700.0},
    "S02": {"pad_depth": 1100.0, "west_x": -9590.75, "east_x": -8140.75,
            "east_depth": 600.0},
    "S03": {"pad_depth": 1200.0, "west_x": -9640.75, "east_x": -8165.75,
            "east_depth": 450.0},
    "S04": {"pad_depth": 1000.0, "west_x": -9540.75, "east_x": -8215.75,
            "east_depth": 550.0},
    "S05": {"pad_depth": 1200.0, "west_x": -9640.75, "east_x": -8165.75,
            "east_depth": 450.0},
    "S06": {"pad_depth": 900.0, "west_x": -9490.75, "east_x": -8240.75,
            "east_depth": 600.0},
    "S07_INSPECT": {"pad_depth": 700.0, "west_x": -9390.75,
                    "east_x": -8240.75, "east_depth": 800.0},
    "S07_PALLET": {"pad_depth": 1000.0, "west_x": -9540.75,
                   "east_x": -8165.75, "east_depth": 650.0},
}
ZONE_WEST_DEPTH_CM = 100.0
EXPECTED_ZONE_AREA_CM2 = 14775200.0
EXPECTED_ZONE_DECK_FRACTION = 0.0875
EXPECTED_MEDIAN_DEPTH_OCCUPANCY = 0.67
MINIMUM_STATION_DEPTH_OCCUPANCY = 0.30
NUMERIC_TOLERANCE = 0.001


class PresentationCorrectionGuardError(RuntimeError):
    """Fail-closed error for the candidate-only v006 correction lane."""


def fail(message: str) -> None:
    raise PresentationCorrectionGuardError(
        "PRESSSHOP_2126_OVERHEAD_PRESENTATION_CORRECTION_V001_FAIL: " + message
    )


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest().lower()


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                       allow_nan=False) + "\n").encode("utf-8")


def _close(left: Sequence[float], right: Sequence[float], tolerance: float = NUMERIC_TOLERANCE) -> bool:
    return len(left) == len(right) and all(
        abs(float(a) - float(b)) <= tolerance for a, b in zip(left, right)
    )


def _asset_path(value: Any) -> str | None:
    return _v005._asset_path(value)


def _load_locked_json(path: Path, expected_hash: str, context: str) -> Dict[str, Any]:
    if not path.is_file():
        fail(context + " is missing")
    if digest(path) != expected_hash:
        fail(context + " hash changed")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(context + " is not valid UTF-8 JSON: " + str(exc))
    if not isinstance(value, dict):
        fail(context + " must be a JSON object")
    return value


def _indexed(rows: Any, context: str) -> Dict[str, Dict[str, Any]]:
    if not isinstance(rows, list):
        fail(context + " must be a list")
    result: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            fail(context + " contains an invalid row")
        if row["id"] in result:
            fail(context + " contains duplicate id " + row["id"])
        result[row["id"]] = copy.deepcopy(row)
    return result


def validate_source_receipt() -> Dict[str, Any]:
    receipt = _load_locked_json(SOURCE_RECEIPT, SOURCE_RECEIPT_SHA256, "v005 install receipt")
    if receipt.get("schema") != SOURCE_RECEIPT_SCHEMA or receipt.get("status") != SOURCE_RECEIPT_STATUS:
        fail("v005 install receipt schema/status changed")
    exact = {
        "target_map": SOURCE_MAP,
        "target_map_sha256": SOURCE_FILE_SHA256,
        "target_map_bytes": SOURCE_FILE_BYTES,
        "final_actor_count": EXPECTED_SOURCE_ACTOR_COUNT,
        "final_presentation_actor_count": EXPECTED_SOURCE_PRESENTATION_COUNT,
        "combined_visual_layer_count": EXPECTED_VISUAL_COUNT,
        "machinery_visual_layer_count": EXPECTED_MACHINERY_COUNT,
        "cargo_layer_count": EXPECTED_CARGO_COUNT,
        "machinery_actor_mutated_count": 0,
        "cargo_actor_mutated_count": 0,
        "source_actor_removed_count": 0,
        "runtime_validated": False,
        "visual_capture_validated": False,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("v005 install receipt field changed: " + key)
    receipt_hash_fields = {
        "preserved_nonpresentation_actor_fingerprints_after_sha256": EXPECTED_SOURCE_HASHES["preserved_nonpresentation"],
        "unchanged_presentation_actor_fingerprints_after_sha256": EXPECTED_SOURCE_HASHES["unchanged_v005_presentation"],
        "visual_layer_actor_fingerprints_after_sha256": EXPECTED_SOURCE_HASHES["combined_visual"],
        "machinery_actor_fingerprints_after_sha256": EXPECTED_SOURCE_HASHES["machinery_visual"],
        "cargo_actor_fingerprints_after_sha256": EXPECTED_SOURCE_HASHES["cargo_visual"],
    }
    for key, expected in receipt_hash_fields.items():
        if receipt.get(key) != expected:
            fail("v005 fingerprint evidence changed: " + key)
    mutations = _indexed(receipt.get("presentation_mutations"), "v005 presentation mutations")
    additions = _indexed(receipt.get("created_presentation_boxes"), "v005 created boxes")
    if len(mutations) != 61 or len(additions) != 55:
        fail("v005 presentation mutation/addition inventory changed")
    return receipt


def validate_source_capture() -> Dict[str, Any]:
    receipt = _load_locked_json(
        SOURCE_CAPTURE_RECEIPT, SOURCE_CAPTURE_RECEIPT_SHA256,
        "v005 saved-map capture receipt",
    )
    if receipt.get("schema") != SOURCE_CAPTURE_SCHEMA or receipt.get("status") != SOURCE_CAPTURE_STATUS:
        fail("v005 capture receipt schema/status changed")
    if (receipt.get("target_map") != SOURCE_MAP
            or receipt.get("target_map_sha256_before") != SOURCE_FILE_SHA256
            or receipt.get("target_map_sha256_after") != SOURCE_FILE_SHA256):
        fail("v005 capture receipt map lock changed")
    if receipt.get("actor_count") != EXPECTED_SOURCE_ACTOR_COUNT:
        fail("v005 capture actor count changed")
    exact = {
        "install_receipt_sha256": SOURCE_RECEIPT_SHA256,
        "installer_contract_sha256": V005_HELPER_SHA256,
        "visual_layer_count": EXPECTED_VISUAL_COUNT,
        "base_visual_layer_count": EXPECTED_MACHINERY_COUNT,
        "cargo_layer_count": EXPECTED_CARGO_COUNT,
        "saved_camera_count": 3,
        "continuous_station_port_count": 12,
        "continuous_station_port_max_gap_cm": 0.0,
        "layout_material_collision_fingerprint_unchanged": True,
        "saved_actor_layout_mutated": False,
        "saved_actor_material_assignment_mutated": False,
        "saved_actor_collision_mutated": False,
        "project_content_mutated": False,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("v005 capture receipt field changed: " + key)
    rows = receipt.get("captures")
    if not isinstance(rows, list) or len(rows) != 3:
        fail("v005 capture inventory changed")
    by_name = {Path(str(row.get("path", ""))).name: row for row in rows if isinstance(row, dict)}
    if set(by_name) != set(SOURCE_CAPTURE_LOCKS):
        fail("v005 capture filenames changed")
    for filename, lock in SOURCE_CAPTURE_LOCKS.items():
        disk = SOURCE_CAPTURE_ROOT / filename
        row = by_name[filename]
        if (not disk.is_file() or disk.stat().st_size != lock["bytes"]
                or digest(disk) != lock["sha256"]):
            fail("v005 captured PNG changed: " + filename)
        if (row.get("sha256") != lock["sha256"] or row.get("bytes") != lock["bytes"]
                or row.get("camera_id") != lock["camera_id"]
                or row.get("width") != 1920 or row.get("height") != 1080):
            fail("v005 capture row changed: " + filename)
    return receipt


def validate_material_locks() -> Dict[str, str]:
    result: Dict[str, str] = {}
    for asset, lock in REUSED_MATERIAL_LOCKS.items():
        disk = _v005.virtual_to_uasset(asset)
        if not disk.is_file() or disk.stat().st_size != lock["bytes"] or digest(disk) != lock["sha256"]:
            fail("reused presentation material changed: " + asset)
        result[asset] = str(lock["sha256"])
    return result


def protected_snapshot() -> Dict[str, str]:
    result: Dict[str, str] = {}
    for name, (path, expected) in PROTECTED_MAPS.items():
        if not path.is_file() or digest(path) != expected:
            fail("protected map changed or is missing: " + name)
        result[name] = expected
    return result


def _v005_plan() -> Dict[str, Any]:
    if not V005_HELPER.is_file() or V005_HELPER.stat().st_size != V005_HELPER_BYTES:
        fail("locked v005 helper byte count changed")
    if digest(V005_HELPER) != V005_HELPER_SHA256:
        fail("locked v005 helper hash changed")
    v002_receipt = _v005.validate_v002_receipt()
    v004_receipt = _v005.validate_source_receipt()
    plan = _v005.build_upgrade_plan(v002_receipt, v004_receipt)
    _v005.validate_upgrade_plan(plan)
    return plan


def _camera_rect(target: Mapping[str, Any]) -> Dict[str, float]:
    width_y = float(target["ortho_width_cm"])
    height_x = width_y / CAMERA_ASPECT
    x, y = float(target["location_cm"][0]), float(target["location_cm"][1])
    return {"min_x": x - height_x / 2.0, "max_x": x + height_x / 2.0,
            "min_y": y - width_y / 2.0, "max_y": y + width_y / 2.0,
            "view_world_x_cm": height_x, "view_world_y_cm": width_y}


def _srgb_luminance(rgb: Sequence[int]) -> float:
    linear = []
    for channel in rgb:
        value = float(channel) / 255.0
        linear.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(left: Sequence[int], right: Sequence[int]) -> float:
    a, b = _srgb_luminance(left), _srgb_luminance(right)
    return (max(a, b) + 0.05) / (min(a, b) + 0.05)


def build_correction_plan(source_receipt: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    receipt = dict(source_receipt) if source_receipt is not None else validate_source_receipt()
    prior_plan = _v005_plan()
    receipt_mutations = _indexed(receipt.get("presentation_mutations"), "v005 presentation mutations")
    receipt_additions = _indexed(receipt.get("created_presentation_boxes"), "v005 created boxes")

    mutations: List[Dict[str, Any]] = []
    for row in prior_plan["mutations"]:
        if row["kind"] not in {"text", "camera"}:
            continue
        item_id = str(row["id"])
        source = copy.deepcopy(dict(row["target"]))
        installed = receipt_mutations.get(item_id)
        if installed is None or installed.get("target_label") != source["label"]:
            fail("v005 receipt does not prove correction source actor: " + item_id)
        if row["kind"] == "text":
            target = copy.deepcopy(source)
            target["location_cm"] = [float(source["location_cm"][0]),
                                     float(source["location_cm"][1]), TEXT_Z_CM]
            target["colour_rgba"] = list(
                FLOW_TEXT_RGBA if item_id in {"LABEL_INBOUND", "LABEL_OUTBOUND"}
                else STATION_TEXT_RGBA
            )
            if item_id == "LABEL_TITLE":
                target["world_size_cm"] = 260.0
                target["location_cm"][0] = -4900.0
            else:
                target["world_size_cm"] = 164.0
            target["rotation_deg_pitch_yaw_roll"] = list(TEXT_ROTATION)
        else:
            target = copy.deepcopy(dict(CAMERA_TARGETS[item_id]))
            target["rotation_deg_pitch_yaw_roll"] = list(CAMERA_ROTATION)
        mutations.append({"id": item_id, "kind": str(row["kind"]),
                          "source": source, "target": target})

    prior_boxes = {
        str(row["id"]): row for row in prior_plan["mutations"] if row["kind"] == "box"
    }
    prior_additions = {str(row["id"]): row for row in prior_plan["additions"]}

    # Directly resize the existing zone bodies and wings.  X is the machine-depth
    # axis in the frozen true-overhead view; Y positions and lengths remain exact.
    for station in STATION_IDS:
        spec = ZONE_DEPTH_SPECS[station]
        pad_id = "PAD_" + station
        pad_source = copy.deepcopy(dict(prior_boxes[pad_id]["target"]))
        installed_pad = receipt_mutations.get(pad_id)
        if installed_pad is None or installed_pad.get("target_label") != pad_source["label"]:
            fail("v005 receipt does not prove zone body source actor: " + pad_id)
        pad_target = copy.deepcopy(pad_source)
        pad_target["dimensions_cm"][0] = float(spec["pad_depth"])
        pad_target["material"] = ZONE_MUTED_MATERIAL
        mutations.append({"id": pad_id, "kind": "box", "group": "zone",
                          "source": pad_source, "target": pad_target})

        for side in ("WEST", "EAST"):
            wing_id = "ZONE_WING_{}_{}".format(station, side)
            wing_source = copy.deepcopy(dict(prior_additions[wing_id]))
            installed_wing = receipt_additions.get(wing_id)
            if installed_wing is None or installed_wing.get("label") != wing_source["label"]:
                fail("v005 receipt does not prove zone wing source actor: " + wing_id)
            wing_target = copy.deepcopy(wing_source)
            if side == "WEST":
                wing_target["location_cm"][0] = float(spec["west_x"])
                wing_target["dimensions_cm"][0] = ZONE_WEST_DEPTH_CM
            else:
                wing_target["location_cm"][0] = float(spec["east_x"])
                wing_target["dimensions_cm"][0] = float(spec["east_depth"])
            wing_target["material"] = ZONE_MUTED_MATERIAL
            mutations.append({"id": wing_id, "kind": "box", "group": "zone",
                              "source": wing_source, "target": wing_target})

    # Reduce the route hierarchy while preserving its exact centres, lengths and
    # twelve station interfaces.  Cream rails stay cream; route surfaces use the
    # new muted teal; exact port caps become Safety Yellow.
    route_box_ids = (
        "FLOW_LANE", "FLOW_EDGE_WEST", "FLOW_EDGE_EAST",
        "FLOW_EDGE_INBOUND", "FLOW_EDGE_OUTBOUND",
        "FLOW_CONNECTOR_01", "FLOW_CONNECTOR_02", "FLOW_CONNECTOR_03",
        "FLOW_CONNECTOR_04", "FLOW_CONNECTOR_05", "FLOW_CONNECTOR_06",
        "FLOW_CONNECTOR_PRESS_S03", "FLOW_CONNECTOR_PRESS_S05",
        "FLOW_CONNECTOR_PRESS_S06",
    )
    for item_id in route_box_ids:
        source = copy.deepcopy(dict(prior_boxes[item_id]["target"]))
        installed = receipt_mutations.get(item_id)
        if installed is None or installed.get("target_label") != source["label"]:
            fail("v005 receipt does not prove route source actor: " + item_id)
        target = copy.deepcopy(source)
        if item_id == "FLOW_LANE":
            target["dimensions_cm"][0] = 360.0
            target["material"] = ROUTE_MUTED_MATERIAL
        elif item_id == "FLOW_EDGE_WEST":
            target["location_cm"][0] = -6650.0
            target["dimensions_cm"][0] = 36.0
        elif item_id == "FLOW_EDGE_EAST":
            target["location_cm"][0] = -6350.0
            target["dimensions_cm"][0] = 36.0
        elif item_id in {"FLOW_EDGE_INBOUND", "FLOW_EDGE_OUTBOUND"}:
            target["dimensions_cm"][0] = 360.0
            target["dimensions_cm"][1] = 36.0
        else:
            target["dimensions_cm"][1] = 56.0
            target["material"] = ROUTE_MUTED_MATERIAL
        mutations.append({"id": item_id, "kind": "box", "group": "route",
                          "source": source, "target": target})

    for item_id, row in prior_additions.items():
        role = str(row.get("role", ""))
        if role not in {"StationRouteBranch", "StationPortCap"}:
            continue
        source = copy.deepcopy(dict(row))
        installed = receipt_additions.get(item_id)
        if installed is None or installed.get("label") != source["label"]:
            fail("v005 receipt does not prove added route source actor: " + item_id)
        target = copy.deepcopy(source)
        if role == "StationRouteBranch":
            target["dimensions_cm"][1] = 56.0
            target["material"] = ROUTE_MUTED_MATERIAL
        else:
            target["material"] = YELLOW_MATERIAL
        mutations.append({"id": item_id, "kind": "box", "group": "route",
                          "source": source, "target": target})

    return {"mutations": mutations, "additions": [], "prior_plan": prior_plan}


def _route_rows(source_receipt: Mapping[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    mutations = _indexed(source_receipt.get("presentation_mutations"), "v005 presentation mutations")
    additions = _indexed(source_receipt.get("created_presentation_boxes"), "v005 created boxes")
    branches: Dict[str, Dict[str, Any]] = {}
    caps: Dict[str, Dict[str, Any]] = {}
    for row in mutations.values():
        label = str(row.get("target_label", ""))
        if "teal station branch v005" in label:
            station = label.split(" | ")[1].split()[0]
            branches[station] = {
                "label": label, "location_cm": row["target_location_cm"],
                "dimensions_cm": row["target_dimensions_cm"],
                "material": row["target_material"],
            }
    for row in additions.values():
        if row.get("role") == "StationRouteBranch":
            station = str(row["id"]).removeprefix("FLOW_BRANCH_")
            branches[station] = copy.deepcopy(row)
        elif row.get("role") == "StationPortCap":
            station = str(row["id"]).removeprefix("STATION_PORT_CAP_")
            caps[station] = copy.deepcopy(row)
    return branches, caps


def validate_correction_plan(plan: Mapping[str, Any], source_receipt: Mapping[str, Any]) -> Dict[str, Any]:
    mutations = list(plan.get("mutations", []))
    additions = list(plan.get("additions", []))
    if len(mutations) != EXPECTED_TOTAL_MUTATION_COUNT:
        fail("v006 mutation count changed")
    if additions:
        fail("v006 direct-resize pass must not add presentation actors")
    ids = [str(row.get("id")) for row in mutations + additions]
    labels = [str(row.get("target", row).get("label")) for row in mutations + additions]
    if len(ids) != len(set(ids)) or len(labels) != len(set(labels)):
        fail("v006 plan contains duplicate ids or target labels")
    if sum(row.get("kind") == "text" for row in mutations) != EXPECTED_TEXT_MUTATION_COUNT:
        fail("v006 text mutation inventory changed")
    if sum(row.get("kind") == "camera" for row in mutations) != EXPECTED_CAMERA_MUTATION_COUNT:
        fail("v006 camera mutation inventory changed")
    if sum(row.get("kind") == "box" for row in mutations) != (
            EXPECTED_ZONE_MUTATION_COUNT + EXPECTED_ROUTE_MUTATION_COUNT):
        fail("v006 presentation-box mutation inventory changed")
    if sum(row.get("group") == "zone" for row in mutations) != EXPECTED_ZONE_MUTATION_COUNT:
        fail("v006 zone mutation inventory changed")
    if sum(row.get("group") == "route" for row in mutations) != EXPECTED_ROUTE_MUTATION_COUNT:
        fail("v006 route mutation inventory changed")
    if any(row.get("kind") not in {"text", "camera", "box"} for row in mutations):
        fail("v006 attempts to mutate a disallowed actor kind")

    by_id = {str(row["id"]): row for row in mutations}
    zone_area = 0.0
    zone_depths: Dict[str, float] = {}
    for station in STATION_IDS:
        spec = ZONE_DEPTH_SPECS[station]
        pad = by_id["PAD_" + station]
        west = by_id["ZONE_WING_{}_WEST".format(station)]
        east = by_id["ZONE_WING_{}_EAST".format(station)]
        pad_source, pad_target = pad["source"], pad["target"]
        if (not _close(pad_source["location_cm"], pad_target["location_cm"])
                or abs(float(pad_target["location_cm"][0]) + 8990.75) > NUMERIC_TOLERANCE
                or not _close(pad_source["dimensions_cm"][1:], pad_target["dimensions_cm"][1:])
                or abs(float(pad_target["dimensions_cm"][0]) - float(spec["pad_depth"])) > NUMERIC_TOLERANCE
                or pad_target["material"] != ZONE_MUTED_MATERIAL
                or pad_target["label"] != pad_source["label"]):
            fail("v006 station body contract changed: " + station)
        for side, row, expected_x, expected_depth in (
                ("WEST", west, spec["west_x"], ZONE_WEST_DEPTH_CM),
                ("EAST", east, spec["east_x"], spec["east_depth"])):
            source, target = row["source"], row["target"]
            if (not _close(source["location_cm"][1:], target["location_cm"][1:])
                    or abs(float(target["location_cm"][0]) - float(expected_x)) > NUMERIC_TOLERANCE
                    or not _close(source["dimensions_cm"][1:], target["dimensions_cm"][1:])
                    or abs(float(target["dimensions_cm"][0]) - float(expected_depth)) > NUMERIC_TOLERANCE
                    or target["material"] != ZONE_MUTED_MATERIAL
                    or target["label"] != source["label"]):
                fail("v006 station {} wing contract changed: {}".format(side.lower(), station))
        zone_area += float(pad_target["dimensions_cm"][0]) * float(pad_target["dimensions_cm"][1])
        zone_area += float(west["target"]["dimensions_cm"][0]) * float(west["target"]["dimensions_cm"][1])
        zone_area += float(east["target"]["dimensions_cm"][0]) * float(east["target"]["dimensions_cm"][1])
        zone_depths[station] = (
            float(west["target"]["dimensions_cm"][0])
            + float(pad_target["dimensions_cm"][0])
            + float(east["target"]["dimensions_cm"][0])
        )
    if abs(zone_area - EXPECTED_ZONE_AREA_CM2) > NUMERIC_TOLERANCE:
        fail("v006 total station-zone area changed")
    deck_area = (DECK_RECT["max_x"] - DECK_RECT["min_x"]) * (
        DECK_RECT["max_y"] - DECK_RECT["min_y"]
    )
    zone_fraction = zone_area / deck_area
    if abs(zone_fraction - EXPECTED_ZONE_DECK_FRACTION) > 0.0001:
        fail("v006 station-zone deck fraction changed")

    label_contrast = _contrast(STATION_TEXT_RGBA[:3], (32, 36, 40))
    flow_contrast = _contrast(FLOW_TEXT_RGBA[:3], (32, 36, 40))
    for row in mutations:
        target = row["target"]
        if row["kind"] == "text":
            if abs(float(target["location_cm"][2]) - TEXT_Z_CM) > NUMERIC_TOLERANCE:
                fail("v006 label lacks a safe depth separation: " + str(row["id"]))
            if list(target["rotation_deg_pitch_yaw_roll"]) != list(TEXT_ROTATION):
                fail("v006 label angle changed")
            expected_size = 260.0 if row["id"] == "LABEL_TITLE" else 164.0
            if abs(float(target["world_size_cm"]) - expected_size) > NUMERIC_TOLERANCE:
                fail("v006 label size changed: " + str(row["id"]))
            if row["id"] == "LABEL_TITLE" and abs(float(target["location_cm"][0]) + 4900.0) > NUMERIC_TOLERANCE:
                fail("v006 title placement changed")
        else:
            if row["kind"] == "camera" and list(target["rotation_deg_pitch_yaw_roll"]) != list(CAMERA_ROTATION):
                fail("v006 camera is not true overhead")
    if label_contrast < 12.0 or flow_contrast < 7.0:
        fail("v006 label contrast contract changed")

    camera_metrics = {row["id"]: _camera_rect(row["target"])
                      for row in mutations if row["kind"] == "camera"}
    for item_id, expected in CAMERA_TARGETS.items():
        target = by_id[item_id]["target"]
        if (not _close(target["location_cm"], expected["location_cm"])
                or abs(float(target["ortho_width_cm"]) - float(expected["ortho_width_cm"])) > NUMERIC_TOLERANCE):
            fail("v006 camera framing target changed: " + item_id)
    overview = camera_metrics["overview"]
    if overview["min_y"] > 1090.2182808269426 or overview["max_y"] < 16590.218280826943:
        fail("v006 overview clips the continuous route caps")
    if abs(overview["max_x"] - DECK_RECT["max_x"]) > NUMERIC_TOLERANCE:
        fail("v006 overview +X edge no longer exactly meets the deck edge")
    route_pixels_at_1080 = 360.0 / overview["view_world_x_cm"] * 1080.0
    if not 40.0 <= route_pixels_at_1080 <= 45.0:
        fail("v006 overview route hierarchy is no longer approximately 40 px")

    branches = {}
    caps = {}
    for row in mutations:
        item_id = str(row["id"])
        role = str(row["target"].get("role", ""))
        if role == "StationRouteBranch" or item_id.startswith("FLOW_CONNECTOR"):
            label = str(row["target"]["label"])
            station = label.split(" | ")[1].split()[0]
            branches[station] = row["target"]
        elif role == "StationPortCap":
            caps[item_id.removeprefix("STATION_PORT_CAP_")] = row["target"]
    if set(branches) != set(STATION_IDS) or set(caps) != set(STATION_IDS):
        fail("v006 route no longer proves 12 branches and 12 ports")
    gaps: Dict[str, float] = {}
    for station in STATION_IDS:
        branch, cap = branches[station], caps[station]
        if (abs(float(branch["dimensions_cm"][1]) - 56.0) > NUMERIC_TOLERANCE
                or branch["material"] != ROUTE_MUTED_MATERIAL):
            fail("v006 branch hierarchy changed: " + station)
        source_cap = by_id["STATION_PORT_CAP_" + station]["source"]
        if (not _close(cap["location_cm"], source_cap["location_cm"])
                or not _close(cap["dimensions_cm"], source_cap["dimensions_cm"])
                or cap["material"] != YELLOW_MATERIAL):
            fail("v006 station port cap contract changed: " + station)
        branch_left = float(branch["location_cm"][0]) - float(branch["dimensions_cm"][0]) / 2.0
        gap = abs(branch_left - float(cap["location_cm"][0]))
        if gap > NUMERIC_TOLERANCE:
            fail("v005 station route port is no longer zero-gap: " + station)
        gaps[station] = gap
    return {
        "mutation_count": len(mutations),
        "text_mutation_count": EXPECTED_TEXT_MUTATION_COUNT,
        "camera_mutation_count": EXPECTED_CAMERA_MUTATION_COUNT,
        "zone_geometry_mutation_count": EXPECTED_ZONE_MUTATION_COUNT,
        "route_geometry_mutation_count": EXPECTED_ROUTE_MUTATION_COUNT,
        "new_presentation_actor_count": 0,
        "machine_or_cargo_actor_mutations": 0,
        "machine_geometry_created": 0,
        "cargo_geometry_created": 0,
        "station_zone_area_cm2": zone_area,
        "station_zone_deck_fraction": zone_fraction,
        "station_zone_area_reduction_fraction_vs_v005": 0.359,
        "audited_median_machine_bbox_depth_occupancy": EXPECTED_MEDIAN_DEPTH_OCCUPANCY,
        "audited_minimum_station_machine_bbox_depth_occupancy": MINIMUM_STATION_DEPTH_OCCUPANCY,
        "station_total_depths_cm": zone_depths,
        "station_label_contrast_ratio": label_contrast,
        "flow_label_contrast_ratio": flow_contrast,
        "label_depth_separation_cm": TEXT_Z_CM,
        "station_port_count": len(caps),
        "station_branch_count": len(branches),
        "station_connector_gaps_cm": gaps,
        "station_connector_max_gap_cm": max(gaps.values()),
        "overview_route_width_pixels_at_1080": route_pixels_at_1080,
        "camera_metrics": camera_metrics,
        "camera_axis_contract": {
            "view_direction": "-Z", "screen_right_world_axis": "+Y",
            "screen_up_world_axis": "+X", "projection": "ORTHOGRAPHIC",
            "aspect_ratio": CAMERA_ASPECT,
        },
        "source_visual_actor_count": EXPECTED_VISUAL_COUNT,
        "source_machinery_actor_count": EXPECTED_MACHINERY_COUNT,
        "source_cargo_actor_count": EXPECTED_CARGO_COUNT,
        "lights_created": 0,
        "exposure_mutated": False,
        "roofs_created": 0,
    }


def validate_offline_contract(require_fresh_target: bool = True) -> Dict[str, Any]:
    if not SOURCE_FILE.is_file() or SOURCE_FILE.stat().st_size != SOURCE_FILE_BYTES:
        fail("frozen v005 source map is missing or its byte count changed")
    if digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
        fail("frozen v005 source map hash changed")
    if require_fresh_target and (TARGET_FILE.exists() or TARGET_ROOT_DISK.exists()):
        fail("v006 target already exists; refusing an overwrite lane")
    if require_fresh_target and INSTALL_RECEIPT.exists():
        fail("v006 install receipt already exists; refusing a rerun lane")
    receipt = validate_source_receipt()
    capture = validate_source_capture()
    materials = validate_material_locks()
    protected = protected_snapshot()
    plan = build_correction_plan(receipt)
    validation = validate_correction_plan(plan, receipt)
    return {"source_receipt": receipt, "source_capture_receipt": capture,
            "material_hashes": materials, "protected_hashes": protected,
            "plan": plan, "validation": validation}


def _require_unreal() -> Any:
    if unreal is None:
        fail("main must run inside UnrealEditor Python")
    return unreal


def _records_by_path(actors: Iterable[Any]) -> Dict[str, Dict[str, Any]]:
    records: Dict[str, Dict[str, Any]] = {}
    for actor in actors:
        row = _v005._actor_fingerprint_record(actor)
        path = str(row["path"])
        if path in records:
            fail("duplicate actor path in fingerprint inventory")
        records[path] = row
    return records


_FLOAT_TOKEN = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"
_MOTION_TRANSFORM_RE = re.compile(
    r"^<Struct 'Transform' \(0x[0-9A-Fa-f]+\) \{"
    r"rotation: \{x: (?P<rx>" + _FLOAT_TOKEN
    + r"), y: (?P<ry>" + _FLOAT_TOKEN
    + r"), z: (?P<rz>" + _FLOAT_TOKEN
    + r"), w: (?P<rw>" + _FLOAT_TOKEN
    + r")\}, translation: \{x: (?P<tx>" + _FLOAT_TOKEN
    + r"), y: (?P<ty>" + _FLOAT_TOKEN
    + r"), z: (?P<tz>" + _FLOAT_TOKEN
    + r")\}, scale3d: \{x: (?P<sx>" + _FLOAT_TOKEN
    + r"), y: (?P<sy>" + _FLOAT_TOKEN
    + r"), z: (?P<sz>" + _FLOAT_TOKEN
    + r")\}\}>$"
)


def _canonical_motion_transform_repr(value: Any, field: str) -> Dict[str, List[float]]:
    """Remove only Unreal's process address from a Transform repr.

    The v005 helper serialises MotionStart/MotionEnd with ``str(Transform)``.
    UE embeds a per-process pointer in that string, so two reads of identical
    transforms differ.  Parsing the strict repr into all ten numeric components
    preserves the complete authored endpoint while rejecting an unexpected
    shape instead of silently weakening the fingerprint.
    """
    if not isinstance(value, str):
        fail("visual metadata {} is not an Unreal Transform repr".format(field))
    match = _MOTION_TRANSFORM_RE.fullmatch(value.strip())
    if match is None:
        fail("visual metadata {} has an unexpected Unreal Transform repr".format(field))
    values = {name: float(token) for name, token in match.groupdict().items()}
    return {
        "rotation_xyzw": [values["rx"], values["ry"], values["rz"], values["rw"]],
        "translation_xyz_cm": [values["tx"], values["ty"], values["tz"]],
        "scale3d_xyz": [values["sx"], values["sy"], values["sz"]],
    }


def _normalise_semantic_row(raw: Mapping[str, Any]) -> Tuple[str, Dict[str, Any]]:
    row = copy.deepcopy(dict(raw))
    path = str(row.pop("path", ""))
    if not path:
        fail("actor semantic fingerprint lacks path")
    metadata = row.get("visual_metadata")
    if metadata is not None:
        if not isinstance(metadata, dict):
            fail("actor visual metadata is not a dictionary")
        for field in ("MotionStart", "MotionEnd"):
            if field in metadata:
                metadata[field] = _canonical_motion_transform_repr(metadata[field], field)
    return path, row


def _semantic_records_from_rows(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Build clone-stable records from the two measured unstable encodings.

    ``new_level_from_template`` and a later saved-map load may remap PersistentLevel
    object names; package/object paths are therefore not identity evidence across
    those operations.  UE's ``str(Transform)`` also embeds a per-process pointer in
    MotionStart/MotionEnd; those two values are strictly parsed into their ten numeric
    components.  A deterministic class/label/semantic-hash multiset preserves duplicate
    labels and multiplicity.  Every substantive fingerprint field—including actor and
    motion transforms, mesh, materials, collision, tags and visual-layer metadata—
    remains in the compared value.
    """
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for raw in rows:
        path, row = _normalise_semantic_row(raw)
        label = str(row.get("label", ""))
        class_path = str(row.get("class_path", ""))
        if not label or not class_path:
            fail("actor semantic fingerprint lacks label or class")
        buckets.setdefault(class_path + "\x1f" + label, []).append(row)
    records: Dict[str, Dict[str, Any]] = {}
    for identity, bucket in sorted(buckets.items()):
        ordered = sorted(bucket, key=canonical_json_bytes)
        for index, row in enumerate(ordered):
            row_hash = hashlib.sha256(canonical_json_bytes(row)).hexdigest()
            key = "{}\x1f{}\x1f{:04d}".format(identity, row_hash, index)
            if key in records:
                fail("duplicate semantic multiset key")
            records[key] = row
    return records


def _semantic_records(actors: Iterable[Any]) -> Dict[str, Dict[str, Any]]:
    return _semantic_records_from_rows(
        _v005._actor_fingerprint_record(actor) for actor in actors
    )


def _hash_records(records: Mapping[str, Mapping[str, Any]]) -> str:
    return hashlib.sha256(canonical_json_bytes(dict(sorted(records.items())))).hexdigest()


def _tags(actor: Any) -> set[str]:
    return {str(tag) for tag in list(actor.tags or [])}


def _count_tag(records: Iterable[Mapping[str, Any]], tag: str) -> int:
    return sum(1 for row in records if tag in set(row.get("tags", ())))


def _validate_loaded_source_actor_groups(actors: Sequence[Any]) -> Dict[str, Any]:
    if len(actors) != EXPECTED_SOURCE_ACTOR_COUNT:
        fail("loaded v005 source actor count changed")
    path_records = _records_by_path(actors)
    source_package = SOURCE_MAP + "." + SOURCE_MAP.rsplit("/", 1)[-1]
    if any(not path.startswith(source_package) for path in path_records):
        fail("loaded v005 source actor escaped the frozen source package")
    records = list(path_records.values())
    nonpresentation = {path: row for path, row in path_records.items()
                       if PRESENTATION_PASS_TAG not in set(row["tags"])}
    unchanged_v005 = {path: row for path, row in path_records.items()
                      if PRESENTATION_PASS_TAG in set(row["tags"])
                      and V005_UPGRADE_TAG not in set(row["tags"])}
    visual = {path: row for path, row in path_records.items()
              if VISUAL_LAYER_TAG in set(row["tags"])}
    cargo = {path: row for path, row in visual.items() if CARGO_MAP_TAG in set(row["tags"])}
    machinery = {path: row for path, row in visual.items() if CARGO_MAP_TAG not in set(row["tags"])}
    groups = {
        "preserved_nonpresentation": nonpresentation,
        "unchanged_v005_presentation": unchanged_v005,
        "combined_visual": visual,
        "machinery_visual": machinery,
        "cargo_visual": cargo,
    }
    expected_counts = {
        "preserved_nonpresentation": 162,
        "unchanged_v005_presentation": EXPECTED_UNCHANGED_V005_PRESENTATION_COUNT,
        "combined_visual": EXPECTED_VISUAL_COUNT,
        "machinery_visual": EXPECTED_MACHINERY_COUNT,
        "cargo_visual": EXPECTED_CARGO_COUNT,
    }
    legacy_path_hashes: Dict[str, str] = {}
    legacy_path_hash_matches: Dict[str, bool] = {}
    for name, group in groups.items():
        if len(group) != expected_counts[name]:
            fail("loaded v005 source actor fingerprint group count changed: " + name)
        legacy_path_hashes[name] = _hash_records(group)
        legacy_path_hash_matches[name] = legacy_path_hashes[name] == EXPECTED_SOURCE_HASHES[name]
    exact_tags = {
        VISUAL_LAYER_TAG: 146, CARGO_MAP_TAG: 26, CARGO_SOURCE_TAG: 26,
        PRESENTATION_PASS_TAG: 140, PRESENTATION_CAMERA_TAG: 3,
        PRESENTATION_ADAPTER_TAG: 1, V004_POLISH_TAG: 41, V005_UPGRADE_TAG: 116,
    }
    for tag, expected in exact_tags.items():
        if _count_tag(records, tag) != expected:
            fail("loaded v005 source actor tag count changed: " + tag)
    semantic = _semantic_records_from_rows(records)
    semantic_groups = {
        name: _semantic_records_from_rows(group.values()) for name, group in groups.items()
    }
    for name, group in semantic_groups.items():
        if len(group) != expected_counts[name]:
            fail("loaded v005 semantic fingerprint group count changed: " + name)
    return {
        "path_records": path_records,
        "semantic_records": semantic,
        "semantic_groups": semantic_groups,
        "semantic_group_hashes": {
            name: _hash_records(group) for name, group in semantic_groups.items()
        },
        "legacy_path_keyed_group_hashes": legacy_path_hashes,
        "legacy_receipt_path_hash_matches": legacy_path_hash_matches,
        "legacy_path_hash_status": (
            "diagnostic_only_unstable_across_saved_map_reload_due_to_actor_object_paths_"
            "and_transform_repr_process_addresses; source package bytes, receipt/capture "
            "evidence, exact counts/tags and all numeric semantic fields are gated"
        ),
    }


def _assert_semantic_records_equal(
        expected: Mapping[str, Mapping[str, Any]],
        actual: Mapping[str, Mapping[str, Any]], context: str) -> None:
    if set(expected) != set(actual):
        missing = sorted(set(expected) - set(actual))[:3]
        added = sorted(set(actual) - set(expected))[:3]
        fail("{} semantic actor keys changed; missing={}; added={}".format(
            context, missing, added))
    for key in sorted(expected):
        if expected[key] != actual[key]:
            fail("{} substantive fingerprint changed: {}".format(context, key))


def _assert_source_text(actor: Any, source: Mapping[str, Any], item_id: str) -> None:
    if str(actor.get_class().get_path_name()) != TEXT_RENDER_ACTOR_CLASS_PATH:
        fail("v005 label class changed: " + item_id)
    transform = _v005._actor_transform_record(actor)
    component = actor.get_editor_property("text_render")
    tags = _tags(actor)
    if (str(actor.get_actor_label()) != source["label"]
            or not _close(transform["location_cm"], source["location_cm"])
            or not _v005._rotation_close(transform["rotation_deg_pitch_yaw_roll"], source["rotation_deg_pitch_yaw_roll"])
            or str(component.get_editor_property("text")) != source["text"]
            or abs(float(component.get_editor_property("world_size")) - float(source["world_size_cm"])) > NUMERIC_TOLERANCE
            or _v005._colour_rgba(component) != [int(v) for v in source["colour_rgba"]]
            or PRESENTATION_PASS_TAG not in tags or V005_UPGRADE_TAG not in tags
            or VISUAL_LAYER_TAG in tags or CARGO_MAP_TAG in tags):
        fail("v005 label source contract changed: " + item_id)
    _v005._readback_no_collision(actor, component, item_id, "v005 label")


def _assert_source_camera(actor: Any, source: Mapping[str, Any], item_id: str) -> None:
    if str(actor.get_class().get_path_name()) != CAMERA_ACTOR_CLASS_PATH:
        fail("v005 camera class changed: " + item_id)
    transform = _v005._actor_transform_record(actor)
    component = actor.get_editor_property("camera_component")
    tags = _tags(actor)
    if (str(actor.get_actor_label()) != source["label"]
            or not _close(transform["location_cm"], source["location_cm"])
            or not _v005._rotation_close(transform["rotation_deg_pitch_yaw_roll"], source["rotation_deg_pitch_yaw_roll"])
            or abs(float(component.get_editor_property("ortho_width")) - float(source["ortho_width_cm"])) > NUMERIC_TOLERANCE
            or "ORTHOGRAPHIC" not in str(component.get_editor_property("projection_mode")).upper()
            or PRESENTATION_PASS_TAG not in tags or PRESENTATION_CAMERA_TAG not in tags
            or V005_UPGRADE_TAG not in tags or VISUAL_LAYER_TAG in tags):
        fail("v005 camera source contract changed: " + item_id)


def _assert_source_route_actor(actor: Any, row: Mapping[str, Any], item_id: str) -> None:
    if str(actor.get_class().get_path_name()) != STATIC_MESH_ACTOR_CLASS_PATH:
        fail("v005 route actor class changed: " + item_id)
    transform = _v005._actor_transform_record(actor)
    component = actor.get_editor_property("static_mesh_component")
    tags = _tags(actor)
    role = "StationPortCap" if item_id.startswith("PORT_") else "StationRouteBranch"
    exact_role = "LB.PressShop.OverheadDeck.Role." + role
    if (str(actor.get_actor_label()) != row["label"]
            or not _close(transform["location_cm"], row["location_cm"])
            or not _v005._rotation_close(transform["rotation_deg_pitch_yaw_roll"], [0.0, 0.0, 0.0])
            or not _close(transform["scale3d"], [float(v) / 100.0 for v in row["dimensions_cm"]])
            or _asset_path(component.get_editor_property("static_mesh")) != _asset_path(CUBE_ASSET)
            or _v005._component_material_path(component) != _asset_path(row["material"])
            or PRESENTATION_PASS_TAG not in tags or V005_UPGRADE_TAG not in tags
            or VISUAL_LAYER_TAG in tags or CARGO_MAP_TAG in tags or CARGO_SOURCE_TAG in tags
            or exact_role not in tags):
        fail("v005 zero-gap route actor changed: " + item_id)
    _v005._readback_no_collision(actor, component, item_id, "v005 route")


def _assert_source_box(actor: Any, source: Mapping[str, Any], item_id: str) -> None:
    if str(actor.get_class().get_path_name()) != STATIC_MESH_ACTOR_CLASS_PATH:
        fail("v005 presentation box class changed: " + item_id)
    transform = _v005._actor_transform_record(actor)
    component = actor.get_editor_property("static_mesh_component")
    tags = _tags(actor)
    expected_rotation = source.get("rotation_deg_pitch_yaw_roll", [0.0, 0.0, 0.0])
    if (str(actor.get_actor_label()) != source["label"]
            or not _close(transform["location_cm"], source["location_cm"])
            or not _v005._rotation_close(transform["rotation_deg_pitch_yaw_roll"], expected_rotation)
            or not _close(transform["scale3d"], [float(v) / 100.0 for v in source["dimensions_cm"]])
            or _asset_path(component.get_editor_property("static_mesh")) != _asset_path(CUBE_ASSET)
            or _v005._component_material_path(component) != _asset_path(source["material"])
            or PRESENTATION_PASS_TAG not in tags or V005_UPGRADE_TAG not in tags
            or VISUAL_LAYER_TAG in tags or CARGO_MAP_TAG in tags or CARGO_SOURCE_TAG in tags):
        fail("v005 presentation box source contract changed: " + item_id)
    _v005._readback_no_collision(actor, component, item_id, "v005 presentation box")


def _append_unique_tags(actor: Any, values: Sequence[str]) -> None:
    ue = _require_unreal()
    tags = list(actor.tags or [])
    existing = {str(tag) for tag in tags}
    for value in values:
        if value not in existing:
            tags.append(ue.Name(value))
            existing.add(value)
    actor.tags = tags


def _replace_camera_role(actor: Any, role_tag: str) -> None:
    ue = _require_unreal()
    prefixes = ("LB.PressShop.OverheadDeck.Camera.Overview.",
                "LB.PressShop.OverheadDeck.Camera.PressSpine.",
                "LB.PressShop.OverheadDeck.Camera.SteamHero.")
    tags = [tag for tag in list(actor.tags or []) if not str(tag).startswith(prefixes)]
    tags.append(ue.Name(role_tag))
    actor.tags = tags


def _apply_text(actor: Any, target: Mapping[str, Any]) -> None:
    actor.set_actor_location(_v005._vector(target["location_cm"]), False, False)
    actor.set_actor_rotation(_v005._rotator(target["rotation_deg_pitch_yaw_roll"]), False)
    component = actor.get_editor_property("text_render")
    component.set_world_size(float(target["world_size_cm"]))
    component.set_text_render_color(_v005._unreal_color_from_rgba(target["colour_rgba"]))
    component.set_editor_property("cast_shadow", False)
    _append_unique_tags(actor, [V006_CORRECTION_TAG])


def _apply_camera(actor: Any, target: Mapping[str, Any]) -> None:
    ue = _require_unreal()
    actor.set_actor_label(str(target["label"]), mark_dirty=True)
    actor.set_actor_location(_v005._vector(target["location_cm"]), False, False)
    actor.set_actor_rotation(_v005._rotator(target["rotation_deg_pitch_yaw_roll"]), False)
    component = actor.get_editor_property("camera_component")
    component.set_editor_property("projection_mode", ue.CameraProjectionMode.ORTHOGRAPHIC)
    component.set_editor_property("ortho_width", float(target["ortho_width_cm"]))
    component.set_editor_property("aspect_ratio", CAMERA_ASPECT)
    component.set_editor_property("constrain_aspect_ratio", True)
    _append_unique_tags(actor, [V006_CORRECTION_TAG, CAMERA_V006_TAG])
    _replace_camera_role(actor, str(target["role_tag"]))


def _apply_box(actor: Any, target: Mapping[str, Any], material: Any) -> None:
    actor.set_actor_location(_v005._vector(target["location_cm"]), False, False)
    actor.set_actor_rotation(
        _v005._rotator(target.get("rotation_deg_pitch_yaw_roll", [0.0, 0.0, 0.0])),
        False,
    )
    actor.set_actor_scale3d(
        _v005._vector([float(value) / 100.0 for value in target["dimensions_cm"]])
    )
    component = actor.get_editor_property("static_mesh_component")
    component.set_material(0, material)
    component.set_editor_property("cast_shadow", False)
    _append_unique_tags(actor, [V006_CORRECTION_TAG])


def _verify_box(actor: Any, target: Mapping[str, Any], item_id: str) -> Dict[str, Any]:
    transform = _v005._actor_transform_record(actor)
    component = actor.get_editor_property("static_mesh_component")
    expected_rotation = target.get("rotation_deg_pitch_yaw_roll", [0.0, 0.0, 0.0])
    if (str(actor.get_actor_label()) != target["label"]
            or not _close(transform["location_cm"], target["location_cm"])
            or not _v005._rotation_close(transform["rotation_deg_pitch_yaw_roll"], expected_rotation)
            or not _close(transform["scale3d"], [float(v) / 100.0 for v in target["dimensions_cm"]])
            or _asset_path(component.get_editor_property("static_mesh")) != _asset_path(CUBE_ASSET)
            or _v005._component_material_path(component) != _asset_path(target["material"])
            or V006_CORRECTION_TAG not in _tags(actor)
            or VISUAL_LAYER_TAG in _tags(actor) or CARGO_MAP_TAG in _tags(actor)):
        fail("v006 presentation box readback changed: " + item_id)
    collision = _v005._readback_no_collision(actor, component, item_id, "v006 presentation box")
    return {
        "id": item_id, "kind": "box", "actor_path": str(actor.get_path_name()),
        "label": str(actor.get_actor_label()), "location_cm": list(target["location_cm"]),
        "dimensions_cm": list(target["dimensions_cm"]), "material": target["material"],
        "collision_readback": collision,
    }


def _verify_text(actor: Any, target: Mapping[str, Any], item_id: str) -> Dict[str, Any]:
    transform = _v005._actor_transform_record(actor)
    component = actor.get_editor_property("text_render")
    if (not _close(transform["location_cm"], target["location_cm"])
            or not _v005._rotation_close(transform["rotation_deg_pitch_yaw_roll"], target["rotation_deg_pitch_yaw_roll"])
            or abs(float(component.get_editor_property("world_size")) - float(target["world_size_cm"])) > NUMERIC_TOLERANCE
            or _v005._colour_rgba(component) != [int(v) for v in target["colour_rgba"]]
            or V006_CORRECTION_TAG not in _tags(actor)):
        fail("v006 label readback changed: " + item_id)
    collision = _v005._readback_no_collision(actor, component, item_id, "v006 label")
    return {"id": item_id, "kind": "text", "actor_path": str(actor.get_path_name()),
            "label": str(actor.get_actor_label()), "location_cm": list(target["location_cm"]),
            "world_size_cm": float(target["world_size_cm"]),
            "colour_rgba": list(target["colour_rgba"]), "collision_readback": collision}


def _verify_camera(actor: Any, target: Mapping[str, Any], item_id: str) -> Dict[str, Any]:
    transform = _v005._actor_transform_record(actor)
    component = actor.get_editor_property("camera_component")
    if (str(actor.get_actor_label()) != target["label"]
            or not _close(transform["location_cm"], target["location_cm"])
            or not _v005._rotation_close(transform["rotation_deg_pitch_yaw_roll"], CAMERA_ROTATION)
            or abs(float(component.get_editor_property("ortho_width")) - float(target["ortho_width_cm"])) > NUMERIC_TOLERANCE
            or abs(float(component.get_editor_property("aspect_ratio")) - CAMERA_ASPECT) > NUMERIC_TOLERANCE
            or not bool(component.get_editor_property("constrain_aspect_ratio"))
            or "ORTHOGRAPHIC" not in str(component.get_editor_property("projection_mode")).upper()
            or V006_CORRECTION_TAG not in _tags(actor)
            or CAMERA_V006_TAG not in _tags(actor)):
        fail("v006 camera readback changed: " + item_id)
    return {"id": item_id, "kind": "camera", "actor_path": str(actor.get_path_name()),
            "label": target["label"], "location_cm": list(target["location_cm"]),
             "ortho_width_cm": float(target["ortho_width_cm"]),
             "role_tag": target["role_tag"]}


def _candidate_material_disk(asset_path: str) -> Path:
    if not asset_path.startswith("/Game/"):
        fail("candidate material escaped /Game: " + asset_path)
    return PROJECT / "Content" / (asset_path.removeprefix("/Game/") + ".uasset")


def _create_candidate_unlit_material(asset_path: str, spec: Mapping[str, Any]) -> Tuple[Any, Dict[str, Any]]:
    ue = _require_unreal()
    if ue.EditorAssetLibrary.does_asset_exist(asset_path):
        fail("v006 candidate material already exists: " + asset_path)
    name = asset_path.rsplit("/", 1)[-1]
    material = ue.AssetToolsHelpers.get_asset_tools().create_asset(
        name, CANDIDATE_MATERIAL_ROOT, ue.Material, ue.MaterialFactoryNew()
    )
    if not isinstance(material, ue.Material) or _asset_path(material) != asset_path:
        fail("could not create v006 candidate material: " + asset_path)
    material.set_editor_property("shading_model", ue.MaterialShadingModel.MSM_UNLIT)
    linear_rgb = _v005.srgb_hex_to_linear(str(spec["srgb_hex"]))
    expression = ue.MaterialEditingLibrary.create_material_expression(
        material, ue.MaterialExpressionConstant3Vector, -220, 0
    )
    if expression is None:
        fail("could not create v006 colour expression: " + asset_path)
    expression.set_editor_property(
        "constant", ue.LinearColor(linear_rgb[0], linear_rgb[1], linear_rgb[2], 1.0)
    )
    if not ue.MaterialEditingLibrary.connect_material_property(
            expression, "", ue.MaterialProperty.MP_EMISSIVE_COLOR):
        fail("could not connect v006 emissive colour: " + asset_path)
    errors = [str(value) for value in (
        ue.MaterialEditingLibrary.recompile_material(material) or []
    )]
    if errors:
        fail("v006 material compile failed for {}: {}".format(asset_path, errors))
    if not ue.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        fail("could not save v006 candidate material: " + asset_path)
    errors = [str(value) for value in (
        ue.MaterialEditingLibrary.recompile_material(material) or []
    )]
    if errors:
        fail("v006 material stabilization compile failed for {}: {}".format(asset_path, errors))
    if not ue.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        fail("could not perform final v006 material save: " + asset_path)
    disk = _candidate_material_disk(asset_path)
    if not disk.is_file():
        fail("v006 candidate material is missing on disk: " + asset_path)
    if "UNLIT" not in str(material.get_editor_property("shading_model")).upper():
        fail("v006 candidate material is not unlit: " + asset_path)
    constant = expression.get_editor_property("constant")
    readback = [float(constant.r), float(constant.g), float(constant.b)]
    if not _close(readback, linear_rgb):
        fail("v006 candidate material colour changed: " + asset_path)
    return material, {
        "asset": asset_path, "role": str(spec["role"]),
        "srgb_hex": str(spec["srgb_hex"]), "linear_rgb": list(linear_rgb),
        "linear_rgb_readback": readback, "shading_model": "UNLIT",
        "sha256": digest(disk), "bytes": disk.stat().st_size,
    }


def _candidate_material_snapshot() -> Dict[str, Dict[str, Any]]:
    result: Dict[str, Dict[str, Any]] = {}
    for asset_path, spec in CANDIDATE_MATERIAL_SPECS.items():
        disk = _candidate_material_disk(asset_path)
        if not disk.is_file():
            fail("v006 candidate material vanished: " + asset_path)
        result[asset_path] = {
            "role": str(spec["role"]), "srgb_hex": str(spec["srgb_hex"]),
            "sha256": digest(disk), "bytes": disk.stat().st_size,
        }
    return result


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(canonical_json_bytes(value))
    except FileExistsError:
        fail("v006 install receipt already exists; refusing overwrite")


def main() -> None:
    ue = _require_unreal()
    inputs = validate_offline_contract(require_fresh_target=True)
    receipt = inputs["source_receipt"]
    plan = inputs["plan"]
    protected_before = inputs["protected_hashes"]
    if ue.EditorAssetLibrary.does_asset_exist(TARGET_MAP) or ue.EditorAssetLibrary.list_assets(
            TARGET_ROOT, recursive=True, include_folder=False):
        fail("v006 target exists in the asset registry")
    _v005._assert_dirty_packages({"content": [], "maps": []},
                                 "editor has dirty packages before v006 creation")
    world_before = _v005._editor_world()
    if _v005._world_package_name(world_before) in {SOURCE_MAP, TARGET_MAP}:
        fail("run v006 installer from an unrelated clean editor world")

    loaded: Dict[str, Any] = {}
    for asset_path in (CUBE_ASSET, *REUSED_MATERIAL_LOCKS.keys()):
        if not ue.EditorAssetLibrary.does_asset_exist(asset_path):
            fail("required native asset is not registered: " + asset_path)
        asset = ue.EditorAssetLibrary.load_asset(asset_path)
        if asset is None:
            fail("required native asset could not load: " + asset_path)
        loaded[asset_path] = asset
    _v005._assert_dirty_packages({"content": [], "maps": []},
                                 "v006 asset preflight dirtied packages")
    if protected_snapshot() != protected_before:
        fail("protected maps changed during v006 preflight")

    level_subsystem = _v005._level_subsystem()
    actor_subsystem = _v005._actor_subsystem()
    if not level_subsystem.load_level(SOURCE_MAP):
        fail("could not load the frozen v005 source for path-keyed validation")
    source_world = _v005._editor_world()
    if _v005._world_package_name(source_world) != SOURCE_MAP:
        fail("frozen v005 source did not become the active editor world")
    if _v005._world_game_mode_path(source_world) != EXPECTED_GAME_MODE:
        fail("frozen v005 source GameMode changed")
    source_actors = list(actor_subsystem.get_all_level_actors() or [])
    source_inventory = _validate_loaded_source_actor_groups(source_actors)
    source_semantic = source_inventory["semantic_records"]

    source_by_label: Dict[str, List[Any]] = {}
    for actor in source_actors:
        source_by_label.setdefault(str(actor.get_actor_label()), []).append(actor)
    mutation_labels = {str(row["source"]["label"]) for row in plan["mutations"]}
    if len(mutation_labels) != EXPECTED_TOTAL_MUTATION_COUNT:
        fail("v006 mutation source labels are not unique")
    if any(len(source_by_label.get(label, [])) != 1 for label in mutation_labels):
        fail("v006 mutation source label is missing or duplicated in frozen v005")
    for row in plan["mutations"]:
        actor = source_by_label[str(row["source"]["label"])][0]
        if row["kind"] == "text":
            _assert_source_text(actor, row["source"], str(row["id"]))
        elif row["kind"] == "camera":
            _assert_source_camera(actor, row["source"], str(row["id"]))
        else:
            _assert_source_box(actor, row["source"], str(row["id"]))
    branches, caps = _route_rows(receipt)
    for station, row in {**branches, **{"PORT_" + key: value for key, value in caps.items()}}.items():
        matches = source_by_label.get(str(row["label"]), [])
        if len(matches) != 1:
            fail("v005 zero-gap route actor is missing or duplicated: " + station)
        _assert_source_route_actor(matches[0], row, station)
    _v005._assert_dirty_packages({"content": [], "maps": []},
                                 "read-only v005 source validation dirtied packages")
    if protected_snapshot() != protected_before:
        fail("protected maps changed during loaded v005 source validation")

    # Candidate Content creation is deliberately last: every immutable-file,
    # receipt/capture, registry, loaded-source inventory, semantic, route and
    # protected-map preflight above must pass before this installer may write a
    # single v006 package.  A source failure therefore leaves no partial target.
    material_records: List[Dict[str, Any]] = []
    for asset_path, spec in CANDIDATE_MATERIAL_SPECS.items():
        material, record = _create_candidate_unlit_material(asset_path, spec)
        loaded[asset_path] = material
        material_records.append(record)
    candidate_materials_after_creation = _candidate_material_snapshot()
    _v005._assert_dirty_packages({"content": [], "maps": []},
                                 "v006 candidate materials remain dirty after save")
    if protected_snapshot() != protected_before:
        fail("protected maps changed while creating v006 candidate materials")

    if not level_subsystem.new_level_from_template(TARGET_MAP, SOURCE_MAP):
        fail("could not clone v005 map to v006 candidate")
    world = _v005._editor_world()
    if _v005._world_package_name(world) != TARGET_MAP:
        fail("v006 target did not become the active editor world")
    game_mode_before = _v005._world_game_mode_path(world)
    if game_mode_before != EXPECTED_GAME_MODE:
        fail("v006 clone changed the OneFactory GameMode")

    actors = list(actor_subsystem.get_all_level_actors() or [])
    if len(actors) != EXPECTED_SOURCE_ACTOR_COUNT:
        fail("v006 clone actor count changed")
    clone_semantic = _semantic_records(actors)
    _assert_semantic_records_equal(source_semantic, clone_semantic, "v005-to-v006 clone")
    by_label: Dict[str, List[Any]] = {}
    for actor in actors:
        by_label.setdefault(str(actor.get_actor_label()), []).append(actor)
    mutation_labels = {str(row["source"]["label"]) for row in plan["mutations"]}
    if any(len(by_label.get(label, [])) != 1 for label in mutation_labels):
        fail("v006 mutation source label is missing or duplicated")
    for row in plan["mutations"]:
        actor = by_label[str(row["source"]["label"])][0]
        if row["kind"] == "text":
            _assert_source_text(actor, row["source"], str(row["id"]))
        elif row["kind"] == "camera":
            _assert_source_camera(actor, row["source"], str(row["id"]))
        else:
            _assert_source_box(actor, row["source"], str(row["id"]))

    unchanged_before = {str(actor.get_path_name()): _v005._actor_fingerprint_record(actor)
                        for actor in actors if str(actor.get_actor_label()) not in mutation_labels}
    visual_before = {str(actor.get_path_name()): _v005._actor_fingerprint_record(actor)
                     for actor in actors if VISUAL_LAYER_TAG in _tags(actor)}

    mutation_records: List[Dict[str, Any]] = []
    for row in plan["mutations"]:
        actor = by_label[str(row["source"]["label"])][0]
        if row["kind"] == "text":
            _apply_text(actor, row["target"])
            mutation_records.append(_verify_text(actor, row["target"], str(row["id"])))
        elif row["kind"] == "camera":
            _apply_camera(actor, row["target"])
            mutation_records.append(_verify_camera(actor, row["target"], str(row["id"])))
        else:
            material_path = str(row["target"]["material"])
            if material_path not in loaded:
                fail("v006 target material was not preloaded: " + material_path)
            _apply_box(actor, row["target"], loaded[material_path])
            mutation_records.append(_verify_box(actor, row["target"], str(row["id"])))

    final_actors = list(actor_subsystem.get_all_level_actors() or [])
    if len(final_actors) != EXPECTED_FINAL_ACTOR_COUNT:
        fail("v006 final actor count changed")
    final_by_path = {str(actor.get_path_name()): _v005._actor_fingerprint_record(actor)
                     for actor in final_actors}
    for path, before in unchanged_before.items():
        if final_by_path.get(path) != before:
            fail("unselected v005 actor changed during v006: " + path)
    for path, before in visual_before.items():
        if final_by_path.get(path) != before:
            fail("machine/cargo visual actor changed during v006: " + path)
    final_records = list(final_by_path.values())
    exact_final_tags = {VISUAL_LAYER_TAG: 146, CARGO_MAP_TAG: 26, CARGO_SOURCE_TAG: 26,
                        PRESENTATION_PASS_TAG: 140, PRESENTATION_CAMERA_TAG: 3,
                        V005_UPGRADE_TAG: 116, V006_CORRECTION_TAG: EXPECTED_TOTAL_MUTATION_COUNT,
                        CAMERA_V006_TAG: 3}
    for tag, expected in exact_final_tags.items():
        if _count_tag(final_records, tag) != expected:
            fail("v006 final actor tag count changed: " + tag)
    if _v005._world_game_mode_path(world) != game_mode_before:
        fail("v006 presentation correction changed the local GameMode")
    final_visual_semantic = _semantic_records_from_rows(
        row for row in final_records if VISUAL_LAYER_TAG in set(row["tags"])
    )
    final_cargo_semantic = _semantic_records_from_rows(
        row for row in final_records
        if VISUAL_LAYER_TAG in set(row["tags"]) and CARGO_MAP_TAG in set(row["tags"])
    )
    final_machinery_semantic = _semantic_records_from_rows(
        row for row in final_records
        if VISUAL_LAYER_TAG in set(row["tags"]) and CARGO_MAP_TAG not in set(row["tags"])
    )
    _assert_semantic_records_equal(
        source_inventory["semantic_groups"]["combined_visual"],
        final_visual_semantic, "v006 final machine/cargo visual inventory",
    )
    _assert_semantic_records_equal(
        source_inventory["semantic_groups"]["machinery_visual"],
        final_machinery_semantic, "v006 final machinery visual inventory",
    )
    _assert_semantic_records_equal(
        source_inventory["semantic_groups"]["cargo_visual"],
        final_cargo_semantic, "v006 final cargo visual inventory",
    )

    dirty_before_save = _v005._assert_dirty_packages(
        {"content": [], "maps": [TARGET_MAP]}, "only v006 target may be dirty before save")
    if not level_subsystem.save_current_level():
        fail("could not save the v006 candidate")
    dirty_after_save = _v005._assert_dirty_packages(
        {"content": [], "maps": []}, "v006 packages remain dirty after save")
    if not TARGET_FILE.is_file():
        fail("v006 map package is missing after save")
    candidate_materials_final = _candidate_material_snapshot()
    if candidate_materials_final != candidate_materials_after_creation:
        fail("v006 candidate material package changed after actor assignment")
    protected_after = protected_snapshot()
    if protected_after != protected_before:
        fail("protected map changed during v006 correction")
    if validate_material_locks() != inputs["material_hashes"]:
        fail("reused presentation material changed during v006")
    immutable = {SOURCE_RECEIPT: SOURCE_RECEIPT_SHA256,
                 SOURCE_CAPTURE_RECEIPT: SOURCE_CAPTURE_RECEIPT_SHA256,
                 V005_HELPER: V005_HELPER_SHA256}
    for path, expected in immutable.items():
        if not path.is_file() or digest(path) != expected:
            fail("immutable v005 evidence changed during v006: " + path.as_posix())
    for filename, lock in SOURCE_CAPTURE_LOCKS.items():
        disk = SOURCE_CAPTURE_ROOT / filename
        if not disk.is_file() or digest(disk) != lock["sha256"]:
            fail("immutable v005 capture changed during v006: " + filename)

    receipt_out = {
        "schema": INSTALL_RECEIPT_SCHEMA, "status": INSTALL_STATUS,
        "candidate_only": True, "source_map": SOURCE_MAP,
        "source_map_sha256": SOURCE_FILE_SHA256, "source_map_bytes": SOURCE_FILE_BYTES,
        "source_receipt": SOURCE_RECEIPT.as_posix(),
        "source_receipt_sha256": SOURCE_RECEIPT_SHA256,
        "source_capture_receipt": SOURCE_CAPTURE_RECEIPT.as_posix(),
        "source_capture_receipt_sha256": SOURCE_CAPTURE_RECEIPT_SHA256,
        "target_map": TARGET_MAP, "target_map_sha256": digest(TARGET_FILE),
        "target_map_bytes": TARGET_FILE.stat().st_size,
        "target_creation_api": "LevelEditorSubsystem.new_level_from_template",
        "source_actor_count": EXPECTED_SOURCE_ACTOR_COUNT,
        "final_actor_count": EXPECTED_FINAL_ACTOR_COUNT,
        "source_presentation_actor_count": EXPECTED_SOURCE_PRESENTATION_COUNT,
        "final_presentation_actor_count": EXPECTED_FINAL_PRESENTATION_COUNT,
        "combined_visual_layer_count": EXPECTED_VISUAL_COUNT,
        "machinery_visual_layer_count": EXPECTED_MACHINERY_COUNT,
        "cargo_layer_count": EXPECTED_CARGO_COUNT,
        "source_path_keyed_visual_fingerprints_sha256": EXPECTED_SOURCE_HASHES["combined_visual"],
        "source_path_keyed_machinery_fingerprints_sha256": EXPECTED_SOURCE_HASHES["machinery_visual"],
        "source_path_keyed_cargo_fingerprints_sha256": EXPECTED_SOURCE_HASHES["cargo_visual"],
        "clone_semantic_fingerprint_normalization": (
            "deterministic class_path+actor_label+semantic-row-hash multiset; only the "
            "ephemeral package/object path is removed and only the per-process pointer "
            "inside MotionStart/MotionEnd str(Transform) is replaced by all ten parsed "
            "numeric components; duplicate labels and multiplicity are retained; actor "
            "and motion transforms, asset, materials, collision, tags and all remaining "
            "visual metadata remain exact"
        ),
        "source_loaded_legacy_path_keyed_fingerprint_hashes": (
            source_inventory["legacy_path_keyed_group_hashes"]
        ),
        "source_loaded_legacy_receipt_path_hash_matches": (
            source_inventory["legacy_receipt_path_hash_matches"]
        ),
        "source_loaded_legacy_path_hash_status": source_inventory["legacy_path_hash_status"],
        "visual_layer_actor_semantic_fingerprints_before_sha256": (
            source_inventory["semantic_group_hashes"]["combined_visual"]
        ),
        "visual_layer_actor_semantic_fingerprints_after_sha256": _hash_records(final_visual_semantic),
        "machinery_actor_semantic_fingerprints_before_sha256": (
            source_inventory["semantic_group_hashes"]["machinery_visual"]
        ),
        "machinery_actor_semantic_fingerprints_after_sha256": _hash_records(final_machinery_semantic),
        "cargo_actor_semantic_fingerprints_before_sha256": (
            source_inventory["semantic_group_hashes"]["cargo_visual"]
        ),
        "cargo_actor_semantic_fingerprints_after_sha256": _hash_records(final_cargo_semantic),
        "machinery_actor_mutated_count": 0, "cargo_actor_mutated_count": 0,
        "source_actor_removed_count": 0, "source_actor_created_count": 0,
        "mutated_existing_presentation_actor_count": len(mutation_records),
        "mutated_station_zone_actor_count": EXPECTED_ZONE_MUTATION_COUNT,
        "mutated_route_actor_count": EXPECTED_ROUTE_MUTATION_COUNT,
        "created_presentation_box_count": 0,
        "presentation_mutations": mutation_records,
        "created_presentation_boxes": [],
        "plan_validation": inputs["validation"],
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "reused_material_hashes_before": inputs["material_hashes"],
        "reused_material_hashes_after": validate_material_locks(),
        "candidate_materials": material_records,
        "candidate_material_packages": candidate_materials_final,
        "presentation_style": {
            "station_zone_material": ZONE_MUTED_MATERIAL,
            "station_zone_srgb_hex": ZONE_MUTED_SRGB_HEX,
            "route_material": ROUTE_MUTED_MATERIAL,
            "route_srgb_hex": ROUTE_MUTED_SRGB_HEX,
            "station_text_rgba": list(STATION_TEXT_RGBA),
            "flow_text_rgba": list(FLOW_TEXT_RGBA),
            "text_depth_separation_cm": TEXT_Z_CM,
            "lights_created": 0, "exposure_mutated": False,
            "external_textures": [],
        },
        "machine_or_cargo_transform_mutations": 0,
        "new_machinery_geometry": 0, "new_cargo_geometry": 0,
        "collision_enabled_on_created_presentation": False,
        "native_cpp_modified": False, "roof_created": False,
        "game_mode_before": game_mode_before,
        "game_mode_after": _v005._world_game_mode_path(world),
        "dirty_packages_before_save": dirty_before_save,
        "dirty_packages_after_save": dirty_after_save,
        "runtime_validated": False, "pie_validated": False,
        "cook_validated": False, "packaged_build_validated": False,
        "visual_capture_validated": False, "steam_capture_validated": False,
        "steam_visual_quality_human_approved": False,
        "honest_status": (
            "The isolated v006 candidate preserves all 146 v005 machine/cargo visual "
            "fingerprints and only resizes/recolours 65 existing presentation boxes, "
            "raises/recolours 15 labels, and reframes three true-overhead cameras. "
            "Fresh 1920x1080 saved-map capture, exact-map PIE, cook, packaged behavior, "
            "performance and Steam visual-quality approval remain required."
        ),
    }
    _write_new_json(INSTALL_RECEIPT, receipt_out)
    ue.log("PRESSSHOP_2126_OVERHEAD_PRESENTATION_CORRECTION_V001_PASS map={} receipt={}".format(
        TARGET_MAP, INSTALL_RECEIPT.as_posix()))
    ue.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
