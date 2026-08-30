"""Guarded candidate-only cargo integration for Press Shop 2126.

This tool clones the immutable ``OverheadPresentation_v002`` map to a new
``OverheadCargo_v003`` candidate, then adds only dedicated
``ALBPressShopOverheadVisualLayerActor`` instances.  It consumes the locked
CargoContinuity v001 manifest/registry and the separate guarded import receipt.

The module is deliberately importable by ordinary CPython so its contract and
layer plan can be tested without Unreal.  ``main`` is the only Unreal entry
point.  It never overwrites or deletes a map, never edits native code, and
fails before target creation when any source, receipt, dependency, candidate
asset, or protected-map lock disagrees.

S07's source art provides pallet payloads for 0/1/4/8 panels, but the current
native presentation controller exposes only PARKED/PICK/PLACE and a final
SUPPORT_FLEET/OUTBOUND phase.  The exact 1- and 4-panel accumulation states are
therefore recorded as deferred; this tool does not fabricate gameplay
thresholds for them.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

try:  # Offline tests intentionally run without the Unreal Python module.
    import unreal  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised by offline tests.
    unreal = None  # type: ignore


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
CARGO_PACKAGE = Path(
    r"C:\Users\greg_\Documents\Codex\2026-08-22\ca\outputs"
    r"\PressShop_CargoContinuity_v001"
)

SOURCE_ROOT = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v002"
)
SOURCE_MAP = (
    SOURCE_ROOT
    + "/Maps/LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v002"
)
SOURCE_FILE = (
    PROJECT
    / "Content/LineBoss/Candidates/PressShop"
    / "PressShop2126_OverheadPresentation_v002/Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v002.umap"
)
SOURCE_FILE_SHA256 = (
    "58fe57f3af0dfcf4021d6bbcd3a52d7d66de22187b561fb2db41becd83023275"
)
SOURCE_RECEIPT = (
    PROJECT
    / "Saved/Audits/PressShop2126/OverheadPresentation_v002"
    / "install_receipt_v001.json"
)
SOURCE_RECEIPT_SHA256 = (
    "eec9ebd5661e835943ceb606ba1569b209b8eb4ee2ab2836bcfb287c8634803d"
)
SOURCE_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.overhead_deck_presentation_install_receipt.v001"
)
SOURCE_RECEIPT_STATUS = (
    "PASS_CANDIDATE_PRESENTATION_MAP_ASSEMBLED__"
    "VISUAL_CAPTURE_AND_RUNTIME_PENDING"
)

TARGET_ROOT = (
    "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadCargo_v003"
)
TARGET_MAP = (
    TARGET_ROOT
    + "/Maps/LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003"
)
TARGET_ROOT_DISK = (
    PROJECT
    / "Content/LineBoss/Candidates/PressShop/PressShop2126_OverheadCargo_v003"
)
TARGET_FILE = (
    TARGET_ROOT_DISK
    / "Maps/LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003.umap"
)
INTEGRATION_RECEIPT = (
    PROJECT
    / "Saved/Audits/PressShop2126/OverheadCargo_v003"
    / "integration_receipt_v001.json"
)
INTEGRATION_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.overhead_cargo_map_integration_receipt.v001"
)

CARGO_REGISTRY = CARGO_PACKAGE / "CARGO_IMPORT_REGISTRY_v001.json"
CARGO_REGISTRY_SHA256 = (
    "03d509d4d215da809e59bbcc803f919568db1d5a993850ba77be7bd317ec15e9"
)
CARGO_REGISTRY_SCHEMA = (
    "cairnwell.press_shop.true_overhead_cargo_import_registry.v001"
)
CARGO_MANIFEST = (
    CARGO_PACKAGE / "PRESSSHOP_2126_CARGO_CONTINUITY_MANIFEST_v001.json"
)
CARGO_MANIFEST_SHA256 = (
    "7dc4d3ea654237235126a01e880d4b7f1add3f4f3e9a03d3a32c26976119184d"
)
CARGO_MANIFEST_SCHEMA = (
    "cairnwell.press_shop.true_overhead_cargo_continuity.v001"
)
CARGO_IMPORTER = (
    CARGO_PACKAGE / "import_pressshop_2126_overhead_cargo_assets_v001.py"
)
CARGO_IMPORTER_SHA256 = (
    "e7861e61acf05def2706b6ad3e61284c0aea0df359e3362f1aaa807fa69705a4"
)
CARGO_IMPORT_RECEIPT = (
    PROJECT
    / "Saved/Audits/PressShop2126/OverheadCargo_v001"
    / "import_receipt_v001.json"
)
CARGO_IMPORT_RECEIPT_SHA256 = (
    "34d5dc97701edd624b7690778e4a71f22fe9a23e90bda58de524f3fac66fc9aa"
)
CARGO_IMPORT_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.true_overhead_cargo_import_receipt.v001"
)

VISUAL_LAYER_CLASS_PATH = (
    "/Script/LineBossCarFactory.LBPressShopOverheadVisualLayerActor"
)
UNIT_PLANE = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadAssets_v001/Geometry/"
    "SM_CA_MW_PS_OverheadUnitPlane_v001"
)
EXPECTED_GAME_MODE = "/Script/LineBossCarFactory.LBOneFactoryGameMode"

VISUAL_LAYER_TAG = "LB.PressShop.Overhead.VisualLayer.v001"
PRESENTATION_TAG = "LB.PressShop.OverheadPresentation.v001"
PRESENTATION_PASS_TAG = "LB.PressShop.OverheadDeckPresentation.v002"
PRESENTATION_CAMERA_TAG = "LB.PressShop.OverheadDeck.Camera.v002"
BOOTSTRAP_TAG = "LB.OneFactory.Bootstrap.v001"
BUILD_AUTHORITY_TAG = "LB.OneFactory.MapAuthored.PressBuildAuthority.v001"
PLAYER_START_TAG = "LB.OneFactory.PlayerStart.Management.v001"
CARGO_MAP_TAG = "LB.PressShop.OverheadCargoMap.v003"
CARGO_SOURCE_TAG = "LB.PressShop.CargoContinuity.v001"

EXPECTED_SOURCE_ACTOR_COUNT = 218
EXPECTED_SOURCE_VISUAL_LAYER_COUNT = 120
EXPECTED_SOURCE_PRESENTATION_COUNT = 1
EXPECTED_SOURCE_PRESENTATION_ACTOR_COUNT = 82
EXPECTED_SOURCE_CAMERA_COUNT = 3
EXPECTED_NEW_CARGO_LAYER_COUNT = 26

SUPPORTED_ROLES = frozenset({
    "Base",
    "FrameState",
    "Workpiece",
    "MovingOverlay",
    "ContactEffect",
    "CyanTransfer",
    "BeaconGlow",
    "TaskLightGlow",
    "ConveyorMotion",
    "RobotPose",
})
USED_ROLES = frozenset({"Workpiece", "MovingOverlay", "CyanTransfer"})
SUPPORTED_MACHINE_IDS = frozenset({
    "IN01_ARTICULATED_CARRIER",
    "IN02_COIL_HANDLER_AGV",
    "IN03_COIL_STORAGE",
    "IN04_DEPACK",
    "IN05_COIL_PREP",
    "S01_DESTACK_LOAD",
    "S02_DEEP_DRAW",
    "S03_FORM",
    "S04_TRIM",
    "S05_PIERCE",
    "S06_FLANGE",
    "S07_INSPECTION",
    "S07_PALLETISER",
    "SUPPORT_FLEET",
})

# These source-authored S07 states are not exposed as StateId values by the
# current native adapter.  The base carrier is represented continuously by its
# PARKED/PICK/PLACE poses and the 8-panel visual is tied to final OUTBOUND.
# Exact 1/4-panel count progression requires a later native pallet-count state.
S07_UNREPRESENTABLE_NATIVE_STATES: Tuple[Mapping[str, str], ...] = (
    {
        "source_state_id": "PALLET_EMPTY",
        "current_visual_mapping": "S07_PALLETISER PARKED/PICK/PLACE base carrier",
        "missing_native_signal": "distinct early-PARKED empty-pallet state",
    },
    {
        "source_state_id": "PALLET_LOADED_01",
        "current_visual_mapping": "DEFERRED_NOT_SPAWNED",
        "missing_native_signal": "pallet payload count or approved threshold",
    },
    {
        "source_state_id": "PALLET_LOADED_04",
        "current_visual_mapping": "DEFERRED_NOT_SPAWNED",
        "missing_native_signal": "pallet payload count or approved threshold",
    },
    {
        "source_state_id": "PALLET_LOADED_08_DISPATCH_READY",
        "current_visual_mapping": "SUPPORT_FLEET OUTBOUND 8-panel visual",
        "missing_native_signal": "explicit dispatch-ready payload-count StateId",
    },
)

NUMERIC_TOLERANCE = 0.001


class CargoMapGuardError(RuntimeError):
    """Fail-closed error for the v003 cargo-map integration lane."""


def fail(message: str) -> None:
    raise CargoMapGuardError(
        "PRESSSHOP_2126_OVERHEAD_CARGO_MAP_V001_FAIL: " + message
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
    for item in value:
        if isinstance(item, bool) or not isinstance(item, (int, float)):
            fail(context + " contains a non-number")
        number = float(item)
        if not math.isfinite(number):
            fail(context + " contains a non-finite value")
        result.append(number)
    return tuple(result)


def _close(left: Sequence[float], right: Sequence[float]) -> bool:
    return len(left) == len(right) and all(
        abs(float(a) - float(b)) <= NUMERIC_TOLERANCE
        for a, b in zip(left, right)
    )


def virtual_to_uasset(asset_path: str) -> Path:
    if not asset_path.startswith("/Game/"):
        fail("not a /Game asset path: " + asset_path)
    result = (
        PROJECT / "Content" / (asset_path.removeprefix("/Game/") + ".uasset")
    ).resolve()
    if not result.is_relative_to((PROJECT / "Content").resolve()):
        fail("asset path escapes Content: " + asset_path)
    return result


def validate_source_receipt() -> Dict[str, Any]:
    receipt = load_locked_json(
        SOURCE_RECEIPT, SOURCE_RECEIPT_SHA256, "v002 presentation receipt"
    )
    exact = {
        "schema": SOURCE_RECEIPT_SCHEMA,
        "status": SOURCE_RECEIPT_STATUS,
        "candidate_only": True,
        "target_map": SOURCE_MAP,
        "target_map_sha256": SOURCE_FILE_SHA256,
        "target_map_bytes": 1097822,
        "protected_authority_map_mutated": False,
        "runtime_validated": False,
        "runtime_ready": False,
        "roof_created": False,
        "roof_actor_count_after": 0,
        "created_actor_count": EXPECTED_SOURCE_PRESENTATION_ACTOR_COUNT,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("v002 presentation receipt field changed: " + key)
    native = receipt.get("retained_native_contract")
    if not isinstance(native, dict):
        fail("v002 presentation receipt native contract is missing")
    expected_native = {
        "visual_layer_class": VISUAL_LAYER_CLASS_PATH,
        "visual_layer_count": EXPECTED_SOURCE_VISUAL_LAYER_COUNT,
        "presentation_adapter_count": EXPECTED_SOURCE_PRESENTATION_COUNT,
        "onefactory_bootstrap_count": 1,
        "press_build_authority_count": 1,
        "management_player_start_count": 1,
        "owns_production_state": False,
    }
    for key, expected in expected_native.items():
        if native.get(key) != expected:
            fail("v002 retained native contract changed: " + key)
    return receipt


def validate_registry_and_manifest() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    registry = load_locked_json(
        CARGO_REGISTRY, CARGO_REGISTRY_SHA256, "cargo import registry"
    )
    manifest = load_locked_json(
        CARGO_MANIFEST, CARGO_MANIFEST_SHA256, "cargo continuity manifest"
    )
    if registry.get("schema") != CARGO_REGISTRY_SCHEMA:
        fail("cargo registry schema changed")
    if registry.get("status") != "PASS__GUARDED_IMPORT_PLAN__NOT_EXECUTED":
        fail("cargo registry status changed")
    if manifest.get("schema") != CARGO_MANIFEST_SCHEMA:
        fail("cargo manifest schema changed")
    if manifest.get("status") != (
        "PASS__SOURCE_HASHED__ROUTES_AUTHORED__"
        "NOT_UNREAL_IMPORTED__NOT_MAP_INTEGRATED"
    ):
        fail("cargo manifest status changed")
    for key in ("unreal_imported", "map_integrated", "runtime_ready"):
        if manifest.get(key) is not False:
            fail("cargo manifest provenance flag changed: " + key)
    if registry.get("map_builder_must_revalidate_all_hashes") is not True:
        fail("cargo registry no longer requires map-builder hash validation")
    if registry.get("map_builder_must_not_spawn_reference_only_rows") is not True:
        fail("cargo registry reference-only policy changed")
    if registry.get("unit_plane") != UNIT_PLANE:
        fail("cargo registry unit plane changed")
    assets = _require_list(registry.get("assets"), "cargo registry assets")
    if len(assets) != 17:
        fail("cargo registry asset-row count changed")
    ids = [str(row.get("asset_id")) for row in assets if isinstance(row, dict)]
    if len(ids) != 17 or len(ids) != len(set(ids)):
        fail("cargo registry asset IDs are missing or duplicated")
    return registry, manifest


def expected_imported_assets(registry: Mapping[str, Any]) -> List[str]:
    result: List[str] = []
    for raw in _require_list(registry.get("assets"), "cargo registry assets"):
        if not isinstance(raw, dict):
            fail("cargo registry asset row is not an object")
        if raw.get("import_action") != "IMPORT_NEW_CANDIDATE_ASSET":
            continue
        result.extend((
            str(raw.get("destination_texture")),
            str(raw.get("destination_material_instance")),
        ))
    if len(result) != 30 or len(result) != len(set(result)):
        fail("cargo registry must declare 30 unique imported assets")
    return sorted(result)


def validate_import_receipt(
    registry: Mapping[str, Any], require_present: bool = True
) -> Dict[str, Any] | None:
    if not CARGO_IMPORTER.is_file():
        fail("repaired cargo importer is missing")
    if digest(CARGO_IMPORTER) != CARGO_IMPORTER_SHA256:
        fail("repaired cargo importer hash changed")
    if not CARGO_IMPORT_RECEIPT.is_file():
        if require_present:
            fail("cargo import receipt is missing; run the guarded asset importer first")
        return None
    if digest(CARGO_IMPORT_RECEIPT) != CARGO_IMPORT_RECEIPT_SHA256:
        fail("cargo import receipt hash changed")
    try:
        receipt = json.loads(CARGO_IMPORT_RECEIPT.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail("cargo import receipt is unreadable: " + str(exc))
    if not isinstance(receipt, dict):
        fail("cargo import receipt must be a JSON object")
    exact = {
        "schema": CARGO_IMPORT_RECEIPT_SCHEMA,
        "status": "PASS__ASSETS_IMPORTED__NOT_MAP_INTEGRATED",
        "registry_sha256": CARGO_REGISTRY_SHA256,
        "manifest_sha256": CARGO_MANIFEST_SHA256,
        "candidate_content_root": registry.get("candidate_content_root"),
        "map_loaded_by_tool": False,
        "map_saved_by_tool": False,
        "native_cpp_modified": False,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("cargo import receipt field changed: " + key)
    expected_assets = expected_imported_assets(registry)
    if sorted(receipt.get("created_assets", [])) != expected_assets:
        fail("cargo import receipt created-asset inventory changed")
    hashes = receipt.get("created_uasset_sha256")
    if not isinstance(hashes, dict) or set(hashes) != set(expected_assets):
        fail("cargo import receipt uasset hash inventory changed")
    for asset_path in expected_assets:
        disk = virtual_to_uasset(asset_path)
        if not disk.is_file() or digest(disk) != str(hashes[asset_path]):
            fail("cargo imported uasset is missing or changed: " + asset_path)
    expected_protected = {
        lock_id: str(row["sha256"])
        for lock_id, row in registry["protected_map_locks"].items()
    }
    if receipt.get("protected_map_sha256_after") != expected_protected:
        fail("cargo import receipt protected-map hashes changed")
    return receipt


def protected_snapshot(registry: Mapping[str, Any]) -> Dict[str, str]:
    locks: Dict[str, Tuple[Path, str]] = {
        "overhead_presentation_v002_source": (
            SOURCE_FILE, SOURCE_FILE_SHA256
        )
    }
    for lock_id, raw in registry.get("protected_map_locks", {}).items():
        if not isinstance(raw, dict):
            fail("protected-map registry row is not an object: " + str(lock_id))
        locks[str(lock_id)] = (Path(str(raw.get("path"))), str(raw.get("sha256")))
    result: Dict[str, str] = {}
    for lock_id, (path, expected) in sorted(locks.items()):
        if not path.is_file():
            fail("protected map is missing: {}: {}".format(lock_id, path))
        actual = digest(path)
        if actual != expected:
            fail("protected map changed: {}: {}".format(lock_id, actual))
        result[lock_id] = actual
    return result


def _asset_index(registry: Mapping[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        str(row["asset_id"]): dict(row)
        for row in _require_list(registry.get("assets"), "cargo registry assets")
    }


def _node_by_state(route: Mapping[str, Any], state_id: str) -> Dict[str, Any]:
    matches = [
        row for row in _require_list(route.get("nodes"), "route nodes")
        if isinstance(row, dict) and row.get("state_id") == state_id
    ]
    if len(matches) != 1:
        fail("route state must resolve exactly once: " + state_id)
    return dict(matches[0])


def _selected_anchor(node: Mapping[str, Any], context: str) -> Tuple[float, ...]:
    if "world_anchor_cm" in node:
        return _finite_vector(node["world_anchor_cm"], 3, context)
    selected = str(node.get("selected_anchor_id"))
    matches = [
        row for row in _require_list(node.get("anchor_variants"), context + " variants")
        if isinstance(row, dict) and str(row.get("socket_id")) == selected
    ]
    if len(matches) != 1:
        fail(context + " selected anchor must resolve exactly once")
    return _finite_vector(matches[0].get("world_anchor_cm"), 3, context)


def _endpoint(
    translation: Sequence[float], yaw: float, scale: Sequence[float]
) -> Dict[str, List[float]]:
    return {
        "translation_cm": list(_finite_vector(translation, 3, "motion translation")),
        "rotation_deg_pitch_yaw_roll": [0.0, float(yaw), 0.0],
        "scale3d": list(_finite_vector(scale, 3, "motion scale")),
    }


def _make_spec(
    assets: Mapping[str, Mapping[str, Any]],
    *,
    spec_id: str,
    assembly_id: str,
    machine_id: str,
    asset_id: str,
    role: str,
    state_id: str | None,
    motion_channel: str,
    anchor_cm: Sequence[float],
    source_state_ids: Sequence[str],
    motion_start_cm: Sequence[float] | None = None,
    motion_end_cm: Sequence[float] | None = None,
    z_override_cm: float | None = None,
    editor_preview_visible: bool = False,
) -> Dict[str, Any]:
    if asset_id not in assets:
        fail("layer references an unknown cargo asset: " + asset_id)
    asset = assets[asset_id]
    if asset.get("import_action") == "REFERENCE_ONLY_ZERO_ALPHA__EMPTY_STATE_USES_NO_OVERLAY":
        fail("layer attempts to spawn a reference-only asset: " + asset_id)
    card = _finite_vector(
        asset.get("unit_plane_card_size_cm"), 2, asset_id + " card size"
    )
    if min(card) <= 0.0:
        fail(asset_id + " card size must be positive")
    yaw = float(asset.get("runtime_yaw_deg"))
    if not math.isfinite(yaw):
        fail(asset_id + " runtime yaw is invalid")
    anchor = list(_finite_vector(anchor_cm, 3, spec_id + " anchor"))
    if z_override_cm is not None:
        anchor[2] = float(z_override_cm)
    scale = [card[0] / 100.0, card[1] / 100.0, 1.0]
    has_motion = motion_start_cm is not None or motion_end_cm is not None
    if has_motion and (motion_start_cm is None or motion_end_cm is None):
        fail(spec_id + " has a partial motion range")
    start = None
    end = None
    if has_motion:
        start_values = list(_finite_vector(motion_start_cm, 3, spec_id + " motion start"))
        end_values = list(_finite_vector(motion_end_cm, 3, spec_id + " motion end"))
        if z_override_cm is not None:
            start_values[2] = float(z_override_cm)
            end_values[2] = float(z_override_cm)
        anchor = start_values
        start = _endpoint(start_values, yaw, scale)
        end = _endpoint(end_values, yaw, scale)
    material = asset.get("destination_material_instance")
    if not isinstance(material, str) or not material.startswith("/Game/"):
        fail(asset_id + " has no spawnable material instance")
    return {
        "spec_id": spec_id,
        "asset_id": asset_id,
        "source_state_ids": list(source_state_ids),
        "plane_asset": UNIT_PLANE,
        "material_instance": material,
        "world_transform": {
            "translation_cm": anchor,
            "rotation_deg_pitch_yaw_roll": [0.0, yaw, 0.0],
            "scale3d_for_100cm_unit_plane": scale,
        },
        "metadata": {
            "LayerId": "CARGO_" + spec_id,
            "AssemblyId": assembly_id,
            "MachineId": machine_id,
            "LayerRole": role,
            "StateId": state_id,
            "MotionChannel": motion_channel,
            "bHasMotionRange": has_motion,
            "MotionStart": start,
            "MotionEnd": end,
            "SequenceFrameIndex": -1,
            "SequenceFrameCount": 0,
            "bSequenceLoops": False,
        },
        "editor_preview_visible": bool(editor_preview_visible),
        "collision_enabled": False,
    }


def build_layer_specs(
    registry: Mapping[str, Any], manifest: Mapping[str, Any]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, str]]]:
    """Build the exact current-native cargo binding plan from locked JSON."""
    assets = _asset_index(registry)
    route = manifest.get("route_contract")
    if not isinstance(route, dict):
        fail("cargo route contract is missing")
    wrapped = route.get("wrapped_coil")
    bare = route.get("bare_coil")
    panel = route.get("panel_process")
    s07_path = route.get("s07_panel_path_world_cm")
    outbound = route.get("outbound_pallet")
    if not all(isinstance(row, dict) for row in (wrapped, bare, panel, s07_path, outbound)):
        fail("cargo route family is incomplete")

    wrapped_nodes = {
        state: _node_by_state(wrapped, state)
        for state in wrapped.get("state_order", [])
    }
    bare_nodes = {
        state: _node_by_state(bare, state)
        for state in bare.get("state_order", [])
    }
    wa = {
        state: _selected_anchor(node, "wrapped " + state)
        for state, node in wrapped_nodes.items()
        if node.get("asset_id")
    }
    ba = {
        state: _selected_anchor(node, "bare " + state)
        for state, node in bare_nodes.items()
        if node.get("asset_id")
    }
    specs: List[Dict[str, Any]] = []

    add = specs.append
    add(_make_spec(
        assets, spec_id="WRAPPED_IN01_UNLOAD", assembly_id="CARGO_WRAPPED_COIL_FLOW",
        machine_id="IN01_ARTICULATED_CARRIER", asset_id="WRAPPED_COIL",
        role="MovingOverlay", state_id="UNLOADING", motion_channel="CARGO_IN01_UNLOAD",
        anchor_cm=wa["PACKAGED_ON_TRAILER"],
        motion_start_cm=wa["PACKAGED_ON_TRAILER"], motion_end_cm=wa["ON_COIL_HANDLER_AGV"],
        source_state_ids=("PACKAGED_ON_TRAILER", "ON_COIL_HANDLER_AGV"),
        editor_preview_visible=True,
    ))
    add(_make_spec(
        assets, spec_id="WRAPPED_IN02_STORAGE_TRANSFER", assembly_id="CARGO_WRAPPED_COIL_FLOW",
        machine_id="IN02_COIL_HANDLER_AGV", asset_id="WRAPPED_COIL",
        role="MovingOverlay", state_id="TRANSFER", motion_channel="CARGO_IN02_TO_STORAGE",
        anchor_cm=wa["ON_COIL_HANDLER_AGV"],
        motion_start_cm=wa["ON_COIL_HANDLER_AGV"], motion_end_cm=wa["BUFFERED_IN_STORAGE"],
        source_state_ids=("ON_COIL_HANDLER_AGV", "BUFFERED_IN_STORAGE"),
    ))
    add(_make_spec(
        assets, spec_id="WRAPPED_IN03_BUFFERED", assembly_id="CARGO_WRAPPED_COIL_FLOW",
        machine_id="IN03_COIL_STORAGE", asset_id="WRAPPED_COIL",
        role="Workpiece", state_id=None, motion_channel="CARGO_IN03_BUFFER",
        anchor_cm=wa["BUFFERED_IN_STORAGE"], source_state_ids=("BUFFERED_IN_STORAGE",),
    ))
    for pose, asset_id in (
        ("ROLLERS", "WRAPPED_COIL"),
        ("WRAP_REMOVE", "WRAPPED_COIL"),
        ("VISION_INSPECT", "BARE_COIL"),
    ):
        add(_make_spec(
            assets, spec_id="DEPACK_" + pose, assembly_id="CARGO_DEPACK_TRANSITION",
            machine_id="IN04_DEPACK", asset_id=asset_id,
            role="MovingOverlay", state_id=pose, motion_channel="CARGO_IN04_DEPACK_POSE",
            anchor_cm=wa["DEPACK_ACTIVE"],
            source_state_ids=("DEPACK_ACTIVE", "DEPACK_COMPLETE"),
        ))
    add(_make_spec(
        assets, spec_id="BARE_IN05_OUTPUT_TO_RACK", assembly_id="CARGO_BARE_COIL_FLOW",
        machine_id="IN05_COIL_PREP", asset_id="BARE_COIL",
        role="MovingOverlay", state_id="FEED", motion_channel="CARGO_IN05_OUTPUT_TO_RACK",
        anchor_cm=ba["ON_OUTPUT_SADDLE"], motion_start_cm=ba["ON_OUTPUT_SADDLE"],
        motion_end_cm=ba["RACKED_FOR_FEED"],
        source_state_ids=("ON_OUTPUT_SADDLE", "RACKED_FOR_FEED"),
    ))
    add(_make_spec(
        assets, spec_id="BARE_S01_CART_TO_DECOILER", assembly_id="CARGO_BARE_COIL_FLOW",
        machine_id="S01_DESTACK_LOAD", asset_id="BARE_COIL",
        role="MovingOverlay", state_id="LOAD", motion_channel="CoilTransferToDecoiler",
        anchor_cm=ba["ON_TRANSFER_CART"], motion_start_cm=ba["ON_TRANSFER_CART"],
        motion_end_cm=ba["MOUNTED_ON_DECOILER"],
        source_state_ids=("ON_TRANSFER_CART", "MOUNTED_ON_DECOILER"),
    ))

    panel_nodes = _require_list(panel.get("nodes"), "panel process nodes")
    panel_by_state = {
        str(row["state_id"]): dict(row)
        for row in panel_nodes if isinstance(row, dict)
    }
    s02 = panel_by_state["PANEL_BLANK_AT_S02"]
    add(_make_spec(
        assets, spec_id="S02_PANEL_BLANK", assembly_id="CARGO_PANEL_PROCESS",
        machine_id="S02_DEEP_DRAW", asset_id="S02_PANEL_BLANK",
        role="Workpiece", state_id=None, motion_channel="CARGO_S02_WORKPIECE",
        anchor_cm=s02["root_world_anchor_cm"], source_state_ids=("PANEL_BLANK_AT_S02",),
    ))
    for state in ("PANEL_FORMED", "PANEL_TRIMMED", "PANEL_PIERCED", "PANEL_FLANGED"):
        node = panel_by_state[state]
        add(_make_spec(
            assets, spec_id=str(node["registered_workpiece_asset_id"]),
            assembly_id="CARGO_PANEL_PROCESS", machine_id=str(node["machine_id"]),
            asset_id=str(node["registered_workpiece_asset_id"]), role="Workpiece",
            state_id=None, motion_channel="CARGO_" + str(node["machine_id"]) + "_WORKPIECE",
            anchor_cm=node["root_world_anchor_cm"], source_state_ids=(state,),
            editor_preview_visible=True,
        ))

    destination_asset = {
        "PANEL_FORMED": "S03_PANEL_TRANSFER",
        "PANEL_TRIMMED": "S04_PANEL_TRANSFER",
        "PANEL_PIERCED": "S05_PANEL_TRANSFER",
        "PANEL_FLANGED": "S06_PANEL_TRANSFER",
        "PANEL_COMPLETE_AT_S07_INSPECTION": "S07_FORMED_PANEL",
    }
    machine_for_source_state = {
        "PANEL_BLANK_AT_S02": "S02_DEEP_DRAW",
        "PANEL_FORMED": "S03_FORM",
        "PANEL_TRIMMED": "S04_TRIM",
        "PANEL_PIERCED": "S05_PIERCE",
        "PANEL_FLANGED": "S06_FLANGE",
    }
    for raw in _require_list(panel.get("segments"), "panel route segments"):
        if not isinstance(raw, dict):
            fail("panel route segment is not an object")
        segment_id = str(raw.get("segment_id"))
        if "__TO__" not in segment_id:
            fail("panel route segment ID changed: " + segment_id)
        source_state, dest_state = segment_id.split("__TO__", 1)
        add(_make_spec(
            assets, spec_id="TRANSFER_" + segment_id,
            assembly_id="CARGO_PANEL_TRANSFER", machine_id=machine_for_source_state[source_state],
            asset_id=destination_asset[dest_state], role="CyanTransfer", state_id=None,
            motion_channel="CARGO_" + segment_id,
            anchor_cm=raw["start_world_anchor_cm"],
            motion_start_cm=raw["start_world_anchor_cm"],
            motion_end_cm=raw["end_world_anchor_cm"],
            source_state_ids=(source_state, dest_state),
        ))

    s07_anchor = _finite_vector(
        panel_by_state["PANEL_COMPLETE_AT_S07_INSPECTION"]["root_world_anchor_cm"],
        3, "S07 inspection root",
    )
    s07_pick = _finite_vector(s07_path["cell_pick_m"], 3, "S07 pick")
    s07_inspect = _finite_vector(s07_path["cell_inspect_m"], 3, "S07 inspect")
    s07_place = _finite_vector(s07_path["cell_place_A_m"], 3, "S07 place A")
    for pose, anchor, start, end in (
        ("PARKED", s07_anchor, None, None),
        ("PICK", s07_anchor, s07_anchor, s07_pick),
        ("INSPECT", s07_inspect, None, None),
        ("PLACE", s07_inspect, s07_inspect, s07_place),
    ):
        add(_make_spec(
            assets, spec_id="S07_PANEL_" + pose, assembly_id="CARGO_S07_PANEL_PATH",
            machine_id="S07_INSPECTION", asset_id="S07_FORMED_PANEL",
            role="MovingOverlay", state_id=pose, motion_channel="CARGO_S07_PANEL_" + pose,
            anchor_cm=anchor, motion_start_cm=start, motion_end_cm=end,
            source_state_ids=("PANEL_COMPLETE_AT_S07_INSPECTION",),
        ))

    empty_anchor = _finite_vector(
        outbound["empty_pallet_world_anchor_cm"], 3, "empty pallet anchor"
    )
    loaded_anchor = _finite_vector(
        outbound["loaded_pallet_world_anchor_cm"], 3, "loaded pallet anchor"
    )
    for pose in ("PARKED", "PICK", "PLACE"):
        add(_make_spec(
            assets, spec_id="S07_PALLET_BASE_" + pose,
            assembly_id="CARGO_S07_OUTBOUND_PALLET", machine_id="S07_PALLETISER",
            asset_id="S07_HOVER_PALLET_EMPTY", role="MovingOverlay", state_id=pose,
            motion_channel="CARGO_S07_PALLET_EMPTY_TO_DISPATCH_READY",
            anchor_cm=empty_anchor, motion_start_cm=empty_anchor, motion_end_cm=loaded_anchor,
            source_state_ids=("PALLET_EMPTY", "PALLET_LOADED_08_DISPATCH_READY"),
            editor_preview_visible=(pose == "PARKED"),
        ))
    add(_make_spec(
        assets, spec_id="S07_DISPATCH_STACK_08", assembly_id="CARGO_S07_OUTBOUND_PALLET",
        machine_id="SUPPORT_FLEET", asset_id="S07_PALLET_STACK_08",
        role="Workpiece", state_id=None, motion_channel="CARGO_S07_DISPATCH_READY",
        anchor_cm=loaded_anchor, z_override_cm=0.4,
        source_state_ids=("PALLET_LOADED_08_DISPATCH_READY",),
    ))

    deferred = [dict(row) for row in S07_UNREPRESENTABLE_NATIVE_STATES]
    validate_layer_specs(specs, registry, manifest, deferred)
    return specs, deferred


def validate_layer_specs(
    specs: Sequence[Mapping[str, Any]],
    registry: Mapping[str, Any],
    manifest: Mapping[str, Any],
    deferred: Sequence[Mapping[str, str]],
) -> Dict[str, Any]:
    if len(specs) != EXPECTED_NEW_CARGO_LAYER_COUNT:
        fail("cargo layer count changed")
    ids = [str(row.get("spec_id")) for row in specs]
    if len(ids) != len(set(ids)):
        fail("cargo layer IDs are duplicated")
    asset_index = _asset_index(registry)
    reference_only = {
        key for key, row in asset_index.items()
        if row.get("import_action") == "REFERENCE_ONLY_ZERO_ALPHA__EMPTY_STATE_USES_NO_OVERLAY"
    }
    role_counts: Counter[str] = Counter()
    machine_counts: Counter[str] = Counter()
    motion_count = 0
    for row in specs:
        role = str(row["metadata"]["LayerRole"])
        machine = str(row["metadata"]["MachineId"])
        if role not in SUPPORTED_ROLES or role not in USED_ROLES:
            fail("cargo layer uses an unsupported or unapproved role: " + role)
        if machine not in SUPPORTED_MACHINE_IDS:
            fail("cargo layer uses an unsupported machine ID: " + machine)
        if row["asset_id"] in reference_only:
            fail("cargo plan spawns reference-only art")
        if row["plane_asset"] != UNIT_PLANE or row["collision_enabled"] is not False:
            fail("cargo layer plane or collision contract changed")
        metadata = row["metadata"]
        if metadata["bHasMotionRange"]:
            motion_count += 1
            if metadata["MotionStart"] is None or metadata["MotionEnd"] is None:
                fail("cargo layer has an incomplete motion range")
        elif metadata["MotionStart"] is not None or metadata["MotionEnd"] is not None:
            fail("static cargo layer carries motion endpoints")
        if metadata["SequenceFrameIndex"] != -1 or metadata["SequenceFrameCount"] != 0:
            fail("cargo v001 map plan must not invent sequence frames")
        role_counts[role] += 1
        machine_counts[machine] += 1
    if dict(role_counts) != {
        "MovingOverlay": 14,
        "Workpiece": 7,
        "CyanTransfer": 5,
    }:
        fail("cargo layer role distribution changed")
    if motion_count != 14:
        fail("cargo exact-motion-range count changed")
    deferred_ids = {str(row.get("source_state_id")) for row in deferred}
    if deferred_ids != {
        "PALLET_EMPTY",
        "PALLET_LOADED_01",
        "PALLET_LOADED_04",
        "PALLET_LOADED_08_DISPATCH_READY",
    }:
        fail("S07 unsupported native-state disclosure changed")
    spawned_assets = {str(row["asset_id"]) for row in specs}
    if {"S07_PALLET_STACK_01", "S07_PALLET_STACK_04"} & spawned_assets:
        fail("unsupported S07 intermediate pallet counts were spawned")

    segments = manifest["route_contract"]["panel_process"]["segments"]
    segment_by_id = {str(row["segment_id"]): row for row in segments}
    transfer_rows = [row for row in specs if row["metadata"]["LayerRole"] == "CyanTransfer"]
    if len(transfer_rows) != len(segment_by_id) or len(transfer_rows) != 5:
        fail("panel transfer route count changed")
    for row in transfer_rows:
        segment_id = str(row["spec_id"]).removeprefix("TRANSFER_")
        segment = segment_by_id.get(segment_id)
        if segment is None:
            fail("cargo transfer has no source manifest segment: " + segment_id)
        if not _close(
            row["metadata"]["MotionStart"]["translation_cm"],
            segment["start_world_anchor_cm"],
        ) or not _close(
            row["metadata"]["MotionEnd"]["translation_cm"],
            segment["end_world_anchor_cm"],
        ):
            fail("cargo transfer endpoints differ from manifest: " + segment_id)
    return {
        "layer_count": len(specs),
        "role_counts": dict(role_counts),
        "machine_counts": dict(machine_counts),
        "motion_range_count": motion_count,
        "deferred_s07_native_states": [dict(row) for row in deferred],
    }


def validate_offline_contract(require_import_receipt: bool = True) -> Dict[str, Any]:
    if not SOURCE_FILE.is_file() or digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
        fail("v002 presentation source map is missing or changed")
    source_receipt = validate_source_receipt()
    registry, manifest = validate_registry_and_manifest()
    import_receipt = validate_import_receipt(registry, require_import_receipt)
    protected = protected_snapshot(registry)
    specs, deferred = build_layer_specs(registry, manifest)
    validation = validate_layer_specs(specs, registry, manifest, deferred)
    return {
        "source_receipt": source_receipt,
        "registry": registry,
        "manifest": manifest,
        "import_receipt": import_receipt,
        "protected_hashes": protected,
        "specs": specs,
        "deferred": deferred,
        "validation": validation,
    }


def _require_unreal() -> Any:
    if unreal is None:
        fail("main must run inside UnrealEditor Python")
    return unreal


def _world_package_name(world: Any) -> str:
    return str(world.get_outermost().get_name()) if world else ""


def _world_game_mode_path(world: Any) -> str | None:
    if world is None:
        return None
    game_mode = world.get_world_settings().get_editor_property("default_game_mode")
    return str(game_mode.get_path_name()) if game_mode else None


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


def _load_class(path: str) -> Any:
    ue = _require_unreal()
    cls = ue.load_class(None, path)
    if cls is None:
        fail("native class is unavailable: " + path)
    return cls


def _asset_class_name(asset: Any) -> str:
    return str(asset.get_class().get_name()) if asset is not None else ""


def preflight_unreal_assets(
    registry: Mapping[str, Any], import_receipt: Mapping[str, Any],
    specs: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    ue = _require_unreal()
    paths = {UNIT_PLANE}
    paths.update(str(row["material_instance"]) for row in specs)
    loaded: Dict[str, Any] = {}
    for path in sorted(paths):
        if not ue.EditorAssetLibrary.does_asset_exist(path):
            fail("required cargo asset is not registered: " + path)
        asset = ue.EditorAssetLibrary.load_asset(path)
        if asset is None:
            fail("required cargo asset could not load: " + path)
        loaded[path] = asset
    if _asset_class_name(loaded[UNIT_PLANE]) != "StaticMesh":
        fail("cargo unit plane has the wrong class")

    imported_hashes = import_receipt["created_uasset_sha256"]
    asset_index = _asset_index(registry)
    master_path = str(registry["master_material"])
    master = ue.EditorAssetLibrary.load_asset(master_path)
    if master is None or _asset_class_name(master) != "Material":
        fail("cargo master material has the wrong class")
    for asset_id in sorted({str(row["asset_id"]) for row in specs}):
        source = asset_index[asset_id]
        mi_path = str(source["destination_material_instance"])
        texture_path = str(source["destination_texture"])
        mi = loaded[mi_path]
        if "MaterialInstance" not in _asset_class_name(mi):
            fail("cargo material instance has the wrong class: " + mi_path)
        if str(mi.get_base_material().get_path_name()).split(".", 1)[0] != master_path:
            fail("cargo material instance has the wrong parent: " + mi_path)
        texture = ue.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
            mi, "SpriteTexture"
        )
        if texture is None or str(texture.get_path_name()).split(".", 1)[0] != texture_path:
            fail("cargo material instance has the wrong SpriteTexture: " + mi_path)
        if source["import_action"] == "IMPORT_NEW_CANDIDATE_ASSET":
            for path in (mi_path, texture_path):
                disk = virtual_to_uasset(path)
                if digest(disk) != str(imported_hashes[path]):
                    fail("cargo imported asset hash changed during Unreal preflight: " + path)
    if dirty_package_paths() != {"content": [], "maps": []}:
        fail("asset preflight dirtied packages")
    return loaded


def _actor_record(actor: Any) -> Dict[str, Any]:
    transform = actor.get_actor_transform()
    rotation = transform.rotation.rotator()
    return {
        "path": str(actor.get_path_name()),
        "label": str(actor.get_actor_label()),
        "class_path": str(actor.get_class().get_path_name()),
        "tags": sorted(str(tag) for tag in actor.tags),
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
        "collision_enabled": bool(actor.get_actor_enable_collision()),
        "hidden_in_editor": bool(actor.is_hidden()) if hasattr(actor, "is_hidden") else False,
    }


def _count_tag(records: Iterable[Mapping[str, Any]], tag: str) -> int:
    return sum(1 for row in records if tag in set(row.get("tags", ())))


def validate_source_actor_inventory(records: Sequence[Mapping[str, Any]]) -> None:
    if len(records) != EXPECTED_SOURCE_ACTOR_COUNT:
        fail("v002 source actor count changed")
    exact_tags = {
        VISUAL_LAYER_TAG: EXPECTED_SOURCE_VISUAL_LAYER_COUNT,
        PRESENTATION_TAG: EXPECTED_SOURCE_PRESENTATION_COUNT,
        PRESENTATION_PASS_TAG: EXPECTED_SOURCE_PRESENTATION_ACTOR_COUNT,
        PRESENTATION_CAMERA_TAG: EXPECTED_SOURCE_CAMERA_COUNT,
        BOOTSTRAP_TAG: 1,
        BUILD_AUTHORITY_TAG: 1,
        PLAYER_START_TAG: 1,
    }
    for tag, expected in exact_tags.items():
        if _count_tag(records, tag) != expected:
            fail("v002 source actor tag count changed: " + tag)


def _vector(values: Sequence[float]) -> Any:
    ue = _require_unreal()
    return ue.Vector(x=float(values[0]), y=float(values[1]), z=float(values[2]))


def _rotator(values: Sequence[float]) -> Any:
    ue = _require_unreal()
    return ue.Rotator(pitch=float(values[0]), yaw=float(values[1]), roll=float(values[2]))


def _transform(record: Mapping[str, Any]) -> Any:
    ue = _require_unreal()
    return ue.Transform(
        location=_vector(record["translation_cm"]),
        rotation=_rotator(record["rotation_deg_pitch_yaw_roll"]),
        scale=_vector(record["scale3d"]),
    )


def _role_enum(role: str) -> Any:
    ue = _require_unreal()
    enum_type = getattr(ue, "LBPressShopOverheadLayerRole", None)
    if enum_type is None:
        fail("native cargo role enum is not reflected")
    enum_name = re.sub(r"(?<!^)(?=[A-Z])", "_", role).upper()
    value = getattr(enum_type, enum_name, None)
    if value is None:
        fail("native cargo role enum entry is missing: " + enum_name)
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


def _property_name(actor: Any, source_name: str) -> str:
    for candidate in PROPERTY_CANDIDATES[source_name]:
        try:
            actor.get_editor_property(candidate)
            return candidate
        except Exception:
            continue
    fail("native reflected property is missing: " + source_name)


def _set_metadata(actor: Any, metadata: Mapping[str, Any]) -> Dict[str, Any]:
    ue = _require_unreal()
    readback: Dict[str, Any] = {}
    for key in (
        "LayerId", "AssemblyId", "MachineId", "LayerRole", "StateId",
        "MotionChannel", "bHasMotionRange", "SequenceFrameIndex",
        "SequenceFrameCount", "bSequenceLoops",
    ):
        prop = _property_name(actor, key)
        value = metadata[key]
        if key in {"LayerId", "AssemblyId", "MachineId", "StateId", "MotionChannel"}:
            value = ue.Name("None" if value is None else str(value))
        elif key == "LayerRole":
            value = _role_enum(str(value))
        actor.set_editor_property(prop, value)
        actual = actor.get_editor_property(prop)
        if key in {"bHasMotionRange", "SequenceFrameIndex", "SequenceFrameCount", "bSequenceLoops", "LayerRole"}:
            if actual != value:
                fail("cargo metadata readback changed: " + key)
            readback[key] = actual if key != "LayerRole" else str(actual)
        else:
            expected = "None" if metadata[key] is None else str(metadata[key])
            if str(actual) != expected:
                fail("cargo FName metadata readback changed: " + key)
            readback[key] = str(actual)
    if metadata["bHasMotionRange"]:
        for key in ("MotionStart", "MotionEnd"):
            prop = _property_name(actor, key)
            expected = metadata[key]
            value = _transform(expected)
            actor.set_editor_property(prop, value)
            actual = actor.get_editor_property(prop)
            actual_rotation = actual.rotation.rotator()
            actual_record = {
                "translation_cm": [actual.translation.x, actual.translation.y, actual.translation.z],
                "rotation_deg_pitch_yaw_roll": [
                    actual_rotation.pitch, actual_rotation.yaw, actual_rotation.roll
                ],
                "scale3d": [actual.scale3d.x, actual.scale3d.y, actual.scale3d.z],
            }
            for field in expected:
                if not _close(actual_record[field], expected[field]):
                    fail("cargo motion-transform readback changed: " + key + "/" + field)
            readback[key] = actual_record
    else:
        readback["MotionStart"] = None
        readback["MotionEnd"] = None
    return readback


def spawn_cargo_layers(
    actor_subsystem: Any,
    visual_class: Any,
    specs: Sequence[Mapping[str, Any]],
    loaded_assets: Mapping[str, Any],
) -> Tuple[List[Any], List[Dict[str, Any]]]:
    actors: List[Any] = []
    records: List[Dict[str, Any]] = []
    for spec in specs:
        world = spec["world_transform"]
        label = "CARGO | " + str(spec["spec_id"])
        actor = actor_subsystem.spawn_actor_from_class(
            visual_class,
            _vector(world["translation_cm"]),
            _rotator(world["rotation_deg_pitch_yaw_roll"]),
            transient=False,
        )
        if actor is None:
            fail("could not spawn cargo actor: " + label)
        actor.set_actor_label(label, mark_dirty=True)
        actor.set_actor_scale3d(_vector(world["scale3d_for_100cm_unit_plane"]))
        actor.set_actor_enable_collision(False)
        mesh = actor.get_editor_property("static_mesh_component")
        if mesh is None:
            fail(label + " has no static mesh component")
        result = mesh.set_static_mesh(loaded_assets[spec["plane_asset"]])
        if result is False:
            fail(label + " rejected the unit plane")
        mesh.set_material(0, loaded_assets[spec["material_instance"]])
        metadata = _set_metadata(actor, spec["metadata"])
        tags = list(actor.tags)
        for tag in (CARGO_MAP_TAG, CARGO_SOURCE_TAG):
            name = _require_unreal().Name(tag)
            if name not in tags:
                tags.append(name)
        actor.tags = tags
        actor.apply_presentation_state(bool(spec["editor_preview_visible"]), 0.0)
        if actor.get_actor_enable_collision():
            fail(label + " collision was enabled")
        assigned = mesh.get_material(0)
        if assigned is None or str(assigned.get_path_name()).split(".", 1)[0] != spec["material_instance"]:
            fail(label + " material readback changed")
        actual = _actor_record(actor)
        if not _close(actual["location_cm"], world["translation_cm"]):
            fail(label + " location readback changed")
        if not _close(actual["scale3d"], world["scale3d_for_100cm_unit_plane"]):
            fail(label + " scale readback changed")
        actors.append(actor)
        records.append({
            "spec_id": spec["spec_id"],
            "asset_id": spec["asset_id"],
            "source_state_ids": spec["source_state_ids"],
            "actor": actual,
            "plane_asset": spec["plane_asset"],
            "material_instance": spec["material_instance"],
            "metadata_readback": metadata,
            "editor_preview_visible": bool(spec["editor_preview_visible"]),
        })
    return actors, records


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(canonical_json_bytes(value))
    except FileExistsError:
        fail("integration receipt already exists; refusing overwrite")


def main() -> None:
    ue = _require_unreal()
    inputs = validate_offline_contract(require_import_receipt=True)
    registry = inputs["registry"]
    manifest = inputs["manifest"]
    import_receipt = inputs["import_receipt"]
    specs = inputs["specs"]
    protected_before = inputs["protected_hashes"]

    if INTEGRATION_RECEIPT.exists():
        fail("integration receipt already exists; refusing rerun")
    if TARGET_FILE.exists() or TARGET_ROOT_DISK.exists():
        fail("v003 target exists on disk; refusing overwrite")
    if ue.EditorAssetLibrary.does_asset_exist(TARGET_MAP):
        fail("v003 target exists in the asset registry; refusing overwrite")
    if ue.EditorAssetLibrary.list_assets(TARGET_ROOT, recursive=True, include_folder=False):
        fail("v003 target root is not empty in the asset registry")
    if dirty_package_paths() != {"content": [], "maps": []}:
        fail("editor has dirty packages before v003 target creation")
    world_before = _editor_world()
    world_before_name = _world_package_name(world_before)
    if world_before_name in {SOURCE_MAP, TARGET_MAP}:
        fail("run from an unrelated clean editor world")

    loaded_assets = preflight_unreal_assets(registry, import_receipt, specs)
    visual_class = _load_class(VISUAL_LAYER_CLASS_PATH)
    if protected_snapshot(registry) != protected_before:
        fail("protected maps changed during asset preflight")
    if digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
        fail("v002 source map changed during asset preflight")

    level_subsystem = _level_subsystem()
    actor_subsystem = _actor_subsystem()
    # First map mutation: create a new candidate package from the unopened,
    # hash-locked v002 source.  No source actor is destroyed or edited.
    if not level_subsystem.new_level_from_template(TARGET_MAP, SOURCE_MAP):
        fail("could not clone v002 presentation map to v003 cargo candidate")
    world = _editor_world()
    if _world_package_name(world) != TARGET_MAP:
        fail("v003 cargo target did not become the active editor world")
    game_mode_before = _world_game_mode_path(world)
    if game_mode_before != EXPECTED_GAME_MODE:
        fail("v003 clone changed the OneFactory GameMode")

    existing_actors = list(actor_subsystem.get_all_level_actors())
    existing_records = [_actor_record(actor) for actor in existing_actors]
    validate_source_actor_inventory(existing_records)
    existing_by_path_before = {row["path"]: row for row in existing_records}
    existing_labels = {row["label"] for row in existing_records}
    cargo_labels = {"CARGO | " + str(row["spec_id"]) for row in specs}
    if existing_labels & cargo_labels:
        fail("cargo actor label collides with a preserved v002 actor")

    cargo_actors, cargo_records = spawn_cargo_layers(
        actor_subsystem, visual_class, specs, loaded_assets
    )
    if len(cargo_actors) != EXPECTED_NEW_CARGO_LAYER_COUNT:
        fail("not all cargo layers were spawned")

    final_actors = list(actor_subsystem.get_all_level_actors())
    final_records = [_actor_record(actor) for actor in final_actors]
    if len(final_records) != EXPECTED_SOURCE_ACTOR_COUNT + EXPECTED_NEW_CARGO_LAYER_COUNT:
        fail("v003 final actor count changed")
    final_by_path = {row["path"]: row for row in final_records}
    for path, before in existing_by_path_before.items():
        if final_by_path.get(path) != before:
            fail("preserved v002 actor changed during cargo integration: " + path)
    validate_source_actor_inventory([
        row for row in final_records if CARGO_MAP_TAG not in set(row["tags"])
    ])
    if _count_tag(final_records, CARGO_MAP_TAG) != EXPECTED_NEW_CARGO_LAYER_COUNT:
        fail("cargo provenance tag count changed")
    if _count_tag(final_records, VISUAL_LAYER_TAG) != (
        EXPECTED_SOURCE_VISUAL_LAYER_COUNT + EXPECTED_NEW_CARGO_LAYER_COUNT
    ):
        fail("combined native visual-layer count changed")
    if _world_game_mode_path(world) != game_mode_before:
        fail("cargo integration changed the local GameMode")

    dirty_before_save = dirty_package_paths()
    if dirty_before_save != {"content": [], "maps": [TARGET_MAP]}:
        fail("only the v003 target map may be dirty before save")
    if not level_subsystem.save_current_level():
        fail("could not save the v003 cargo candidate map")
    if dirty_package_paths() != {"content": [], "maps": []}:
        fail("candidate packages remain dirty after explicit save")
    if not TARGET_FILE.is_file():
        fail("v003 target map package is missing after save")
    protected_after = protected_snapshot(registry)
    if protected_after != protected_before:
        fail("protected map changed during v003 cargo integration")
    if digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
        fail("v002 source map changed during v003 cargo integration")

    receipt = {
        "schema": INTEGRATION_RECEIPT_SCHEMA,
        "status": (
            "PASS_CANDIDATE_CARGO_MAP_INTEGRATED__"
            "S07_INTERMEDIATE_PALLET_COUNTS_DEFERRED__PIE_CAPTURE_PENDING"
        ),
        "candidate_only": True,
        "source_map": SOURCE_MAP,
        "source_map_sha256": SOURCE_FILE_SHA256,
        "source_receipt": SOURCE_RECEIPT.as_posix(),
        "source_receipt_sha256": SOURCE_RECEIPT_SHA256,
        "cargo_registry": CARGO_REGISTRY.as_posix(),
        "cargo_registry_sha256": CARGO_REGISTRY_SHA256,
        "cargo_manifest": CARGO_MANIFEST.as_posix(),
        "cargo_manifest_sha256": CARGO_MANIFEST_SHA256,
        "cargo_importer": CARGO_IMPORTER.as_posix(),
        "cargo_importer_sha256": CARGO_IMPORTER_SHA256,
        "cargo_import_receipt": CARGO_IMPORT_RECEIPT.as_posix(),
        "cargo_import_receipt_sha256": CARGO_IMPORT_RECEIPT_SHA256,
        "target_map": TARGET_MAP,
        "target_map_sha256": digest(TARGET_FILE),
        "target_map_bytes": TARGET_FILE.stat().st_size,
        "target_creation_api": "LevelEditorSubsystem.new_level_from_template",
        "source_actor_count": EXPECTED_SOURCE_ACTOR_COUNT,
        "source_actor_mutated_count": 0,
        "source_actor_removed_count": 0,
        "cargo_layer_count": len(cargo_records),
        "combined_visual_layer_count": (
            EXPECTED_SOURCE_VISUAL_LAYER_COUNT + len(cargo_records)
        ),
        "cargo_layers": cargo_records,
        "layer_plan_validation": inputs["validation"],
        "s07_unrepresentable_native_states": inputs["deferred"],
        "s07_intermediate_payload_assets_spawned": False,
        "native_extension_required_for_exact_s07_counts": True,
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "protected_authority_map_mutated": False,
        "source_map_mutated": False,
        "native_cpp_modified": False,
        "existing_camera_actor_count_preserved": EXPECTED_SOURCE_CAMERA_COUNT,
        "existing_deck_presentation_actor_count_preserved": (
            EXPECTED_SOURCE_PRESENTATION_ACTOR_COUNT
        ),
        "existing_runtime_presentation_adapter_count_preserved": 1,
        "collision_enabled_on_cargo_layers": False,
        "game_mode_before": game_mode_before,
        "game_mode_after": _world_game_mode_path(world),
        "dirty_packages_before_save": dirty_before_save,
        "dirty_packages_after_save": dirty_package_paths(),
        "runtime_validated": False,
        "packaged_build_validated": False,
        "visual_capture_validated": False,
        "steam_capture_validated": False,
        "honest_status": (
            "Cargo art and exact source-authored endpoints are integrated in an isolated "
            "candidate map. Exact S07 1/4-panel accumulation states, PIE lifecycle proof, "
            "packaged behavior, performance and Steam screenshot evidence remain open."
        ),
    }
    _write_new_json(INTEGRATION_RECEIPT, receipt)
    ue.log(
        "PRESSSHOP_2126_OVERHEAD_CARGO_MAP_V001_PASS map={} receipt={}".format(
            TARGET_MAP, INTEGRATION_RECEIPT.as_posix()
        )
    )
    ue.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
