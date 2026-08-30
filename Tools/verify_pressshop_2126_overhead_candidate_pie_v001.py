"""Fail-closed exact-map PIE proof for the Press Shop 2126 overhead candidate.

This is a read-only verification lane.  It loads one pinned candidate map,
starts regular PIE (never Simulate In Editor), proves that the real native
player controller commissioned the transient factory through the production
startup seam, drives one canonical production unit with the existing native
runtime coordinator, and observes the existing native presentation adapter.
It never saves, imports, builds, cooks, packages, or edits project content.

The v003 profile is frozen in this file.  The v004 and v006 profiles are
deliberately unrunnable until their install receipt and map SHA-256 values are
supplied in the environment after the guarded install has completed.  Output
is one new JSON receipt under Saved; an existing receipt is never overwritten.

This proves runtime binding and representative visual lifecycle behaviour in
the exact editor map.  It is not packaged-build, performance, Steam-art, or
human visual-quality approval.  The frozen v003 profile preserves the legacy
V001 no-gate proof.  The v004 profile is a separately versioned proof contract:
it requires the compiled V002 Press route, observes the completed inspection
hold, submits one passing quality result, and then proves release into
palletising/outbound.  It never rewrites historical v003 evidence.

Unreal Python 5.8 removes the leading native bool from functions that also
have output parameters.  A native success returns only the output value(s),
while a native false returns None and suppresses the output reason.  The
helpers below accept both that generated-stub shape and the older explicit
bool tuple shape, but always treat None as a native failure.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:  # Importable by the offline unit tests without an Unreal installation.
    import unreal  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised by offline tests
    unreal = None  # type: ignore


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
GAME_MODE_CLASS = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
COORDINATOR_CLASS = "/Script/LineBossCarFactory.LBOneFactoryRuntimeCoordinator"
PRESENTATION_CLASS = "/Script/LineBossCarFactory.LBPressShopOverheadPresentationActor"
VISUAL_LAYER_CLASS = "/Script/LineBossCarFactory.LBPressShopOverheadVisualLayerActor"
PLAYER_CONTROLLER_CLASS = "/Script/LineBossCarFactory.LBOneFactoryPlayerController"
PRODUCTION_AUTHORITY_CLASS = (
    "/Script/LineBossCarFactory.LBOneFactoryProductionFlowAuthority"
)
STARTER_LAYOUT_AUTHORITY_CLASSES: Mapping[str, str] = {
    "press": "/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority",
    "body_weld": (
        "/Script/LineBossCarFactory.LBOneFactoryBodyWeldStarterLayoutAuthority"
    ),
    "paint": "/Script/LineBossCarFactory.LBOneFactoryPaintStarterLayoutAuthority",
    "assembly": (
        "/Script/LineBossCarFactory.LBOneFactoryAssemblyStarterLayoutAuthority"
    ),
}
EXPECTED_STARTER_CONTRACT_IDS = (
    "CON_STARTER_1", "CON_STARTER_2", "CON_STARTER_3",
)

EXPECTED_STATION_ROUTE_PREFIX = (
    "OF_PRESS_INBOUND_RECEIVING_001",
    "OF_PRESS_WRAPPED_COIL_STORE_001",
    "OF_PRESS_BLANK_PREP_001",
    "OF_PRESS_PREPARED_BLANK_BUFFER_001",
    "OF_PRESS_TRAIN_001",
    "OF_PRESS_PANEL_INSPECTION_001",
    "OF_PRESS_PANEL_DISPATCH_001",
)
EXPECTED_ROUTE_COUNT = 57
EXPECTED_VISUAL_LAYER_COUNT = 146
EXPECTED_CARGO_LAYER_COUNT = 26
EXPECTED_BEACON_COUNT = 14
EXPECTED_TASK_LIGHT_COUNT = 4
EXPECTED_PRESENTATION_COUNT = 1
GAME_WORLD_TIMEOUT_SECONDS = 75.0
PLAYER_ACTIVATION_TIMEOUT_SECONDS = 45.0
RUN_TIMEOUT_SECONDS = 180.0
POSITION_TOLERANCE_CM = 1.0

PROFILE_ENV = "LB_PRESSSHOP_PIE_PROFILE"
RECEIPT_SHA_ENV = "LB_PRESSSHOP_PIE_EXPECTED_RECEIPT_SHA256"
MAP_SHA_ENV = "LB_PRESSSHOP_PIE_EXPECTED_MAP_SHA256"
QUALITY_PASS_EVIDENCE_ID = "OVERHEAD_PRESS_PANEL_INSPECTION_PASS_V002"


@dataclass(frozen=True)
class CandidateProfile:
    key: str
    target_map: str
    target_file: Path
    source_receipt: Path
    receipt_schema: str
    receipt_status: str
    expected_receipt_sha256: Optional[str]
    expected_map_sha256: Optional[str]
    output_receipt: Path
    output_schema: str
    runtime_route_contract: str
    expected_topology_prefix: str
    expected_inspection_semantic_stage: str
    expects_press_inspection_quality_gate: bool
    pass_status: str


@dataclass(frozen=True)
class Checkpoint:
    checkpoint_id: str
    station_id: str
    progress01: float
    machine_id: str
    cargo_layer_id: str
    expected_beacon: str
    expected_role: str
    expected_state: str = "NONE"
    require_motion: bool = False
    expected_motion_alpha: Optional[float] = None
    source_role: Optional[str] = None
    source_state: Optional[str] = None


PROFILES: Mapping[str, CandidateProfile] = {
    "v003": CandidateProfile(
        key="v003",
        target_map=(
            "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadCargo_v003/"
            "Maps/LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003"
        ),
        target_file=(
            PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
            / "PressShop2126_OverheadCargo_v003" / "Maps"
            / "LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003.umap"
        ),
        source_receipt=(
            PROJECT / "Saved" / "Audits" / "PressShop2126"
            / "OverheadCargo_v003" / "integration_receipt_v001.json"
        ),
        receipt_schema="cairnwell.press_shop.overhead_cargo_map_integration_receipt.v001",
        receipt_status=(
            "PASS_CANDIDATE_CARGO_MAP_INTEGRATED__"
            "S07_INTERMEDIATE_PALLET_COUNTS_DEFERRED__PIE_CAPTURE_PENDING"
        ),
        expected_receipt_sha256=(
            "0d58168d05869693aef7aaac8ddd4d5bac3e7e71785b4b4db6d6f32cd6569619"
        ),
        expected_map_sha256=(
            "5eae51f2a7d3e1c72deb4fd455d57a6339dee061840b7d062c5ddf680ab6100f"
        ),
        output_receipt=(
            PROJECT / "Saved" / "Audits" / "PressShop2126"
            / "ExactMapPIE_v003" / "exact_map_pie_receipt_v001.json"
        ),
        output_schema="cairnwell.press_shop.exact_map_pie_receipt.v001",
        runtime_route_contract="LEGACY_PRESS_ROUTE_V001_NO_INSPECTION_GATE",
        expected_topology_prefix="OF_RUNTIME_TOPOLOGY_V001_",
        expected_inspection_semantic_stage="PRESSING",
        expects_press_inspection_quality_gate=False,
        pass_status=(
            "PASS_EXACT_MAP_PIE_VISUAL_LIFECYCLE__"
            "PRESS_INSPECTION_QUALITY_GATE_ABSENT"
        ),
    ),
    "v004": CandidateProfile(
        key="v004",
        target_map=(
            "/Game/LineBoss/Candidates/PressShop/"
            "PressShop2126_OverheadPresentation_v004/Maps/"
            "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v004"
        ),
        target_file=(
            PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
            / "PressShop2126_OverheadPresentation_v004" / "Maps"
            / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v004.umap"
        ),
        source_receipt=(
            PROJECT / "Saved" / "Audits" / "PressShop2126"
            / "OverheadPresentation_v004" / "install_receipt_v001.json"
        ),
        receipt_schema=(
            "cairnwell.press_shop.overhead_presentation_polish_install_receipt.v001"
        ),
        receipt_status=(
            "PASS_CANDIDATE_PRESENTATION_POLISH_APPLIED__"
            "CARGO_PRESERVED__PIE_CAPTURE_PENDING"
        ),
        expected_receipt_sha256=None,
        expected_map_sha256=None,
        output_receipt=(
            PROJECT / "Saved" / "Audits" / "PressShop2126"
            / "ExactMapPIE_v004" / "exact_map_pie_receipt_v002.json"
        ),
        output_schema="cairnwell.press_shop.exact_map_pie_receipt.v002",
        runtime_route_contract="PRESS_INSPECTION_ROUTE_V002_QUALITY_GATE",
        expected_topology_prefix="OF_RUNTIME_TOPOLOGY_V002_",
        expected_inspection_semantic_stage="PRESS_PANEL_INSPECTION",
        expects_press_inspection_quality_gate=True,
        pass_status=(
            "PASS_EXACT_MAP_PIE_V002_PRESS_INSPECTION_HOLD_PASS_RELEASE__"
            "PALLETISING_OUTBOUND_VISUAL_LIFECYCLE"
        ),
    ),
    "v006": CandidateProfile(
        key="v006",
        target_map=(
            "/Game/LineBoss/Candidates/PressShop/"
            "PressShop2126_OverheadPresentation_v006/Maps/"
            "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v006"
        ),
        target_file=(
            PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
            / "PressShop2126_OverheadPresentation_v006" / "Maps"
            / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v006.umap"
        ),
        source_receipt=(
            PROJECT / "Saved" / "Audits" / "PressShop2126"
            / "OverheadPresentation_v006" / "install_receipt_v001.json"
        ),
        receipt_schema=(
            "cairnwell.press_shop."
            "overhead_presentation_correction_install_receipt.v001"
        ),
        receipt_status=(
            "PASS_CANDIDATE_PRESENTATION_CORRECTION_APPLIED__"
            "V005_VISUALS_PRESERVED__FRESH_CAPTURE_AND_PIE_PENDING"
        ),
        expected_receipt_sha256=None,
        expected_map_sha256=None,
        output_receipt=(
            PROJECT / "Saved" / "Audits" / "PressShop2126"
            / "ExactMapPIE_v006" / "exact_map_pie_receipt_v003.json"
        ),
        output_schema="cairnwell.press_shop.exact_map_pie_receipt.v003",
        runtime_route_contract="PRESS_INSPECTION_ROUTE_V002_QUALITY_GATE",
        expected_topology_prefix="OF_RUNTIME_TOPOLOGY_V002_",
        expected_inspection_semantic_stage="PRESS_PANEL_INSPECTION",
        expects_press_inspection_quality_gate=True,
        pass_status=(
            "PASS_EXACT_MAP_REGULAR_PIE_NATIVE_PLAYER_ACTIVATION__"
            "V002_PRESS_INSPECTION_HOLD_PASS_RELEASE__"
            "PALLETISING_OUTBOUND_VISUAL_LIFECYCLE"
        ),
    ),
}


V005_SOURCE_MAP = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v005/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v005"
)
V005_SOURCE_MAP_FILE = (
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
    / "PressShop2126_OverheadPresentation_v005" / "Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v005.umap"
)
V005_SOURCE_MAP_SHA256 = (
    "4d3ce8973cc7bede00f0204a1e653117935cfc9f120fac8b6a939510ad01fe4b"
)
V005_SOURCE_RECEIPT = (
    PROJECT / "Saved" / "Audits" / "PressShop2126"
    / "OverheadPresentation_v005" / "install_receipt_v001.json"
)
V005_SOURCE_RECEIPT_SHA256 = (
    "cf13095f09fbf1422b7ee4a41c8f45ca36ceb016af096abf73ccf2aae9eb4246"
)
V006_SEMANTIC_FINGERPRINT_NORMALIZATION = (
    "deterministic class_path+actor_label+semantic-row-hash multiset; only the "
    "ephemeral package/object path is removed and only the per-process pointer "
    "inside MotionStart/MotionEnd str(Transform) is replaced by all ten parsed "
    "numeric components; duplicate labels and multiplicity are retained; actor "
    "and motion transforms, asset, materials, collision, tags and all remaining "
    "visual metadata remain exact"
)
V006_LEGACY_PATH_HASH_STATUS = (
    "diagnostic_only_unstable_across_saved_map_reload_due_to_actor_object_paths_"
    "and_transform_repr_process_addresses; source package bytes, receipt/capture "
    "evidence, exact counts/tags and all numeric semantic fields are gated"
)
V006_LEGACY_PATH_GROUP_KEYS = {
    "cargo_visual", "combined_visual", "machinery_visual",
    "preserved_nonpresentation", "unchanged_v005_presentation",
}


PROTECTED_AUTHORITY_FILES: Mapping[Path, str] = {
    PROJECT / "Content" / "LineBoss" / "Factory" / "OneFactory" / "v001"
    / "Maps" / "LB_MoorcrossWorks_OneFactory_v001.umap": (
        "f4e97b33cdfb1f242b2c606a16b4caa05b74b298fdf1b1263d4a4c46d50e8d5c"
    ),
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
    / "PressShop2126_OverheadPlayable_v001" / "Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001.umap": (
        "43020cb3ea7d18a49319da68a04ae1b96d5af0d535c705e947f81d5c005ba7ce"
    ),
    PROJECT / "Content" / "LineBoss" / "Maps"
    / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": (
        "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8"
    ),
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
    / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": (
        "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0"
    ),
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
    / "PressShop2126_OverheadPresentation_v002" / "Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v002.umap": (
        "58fe57f3af0dfcf4021d6bbcd3a52d7d66de22187b561fb2db41becd83023275"
    ),
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop"
    / "PressShop2126_OverheadCargo_v003" / "Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003.umap": (
        "5eae51f2a7d3e1c72deb4fd455d57a6339dee061840b7d062c5ddf680ab6100f"
    ),
}


CARGO_CONTRACT: Tuple[Tuple[str, str, str, str, str, bool], ...] = (
    ("CARGO_WRAPPED_IN01_UNLOAD", "IN01_ARTICULATED_CARRIER", "MOVING_OVERLAY", "UNLOADING", "CARGO_IN01_UNLOAD", True),
    ("CARGO_WRAPPED_IN02_STORAGE_TRANSFER", "IN02_COIL_HANDLER_AGV", "MOVING_OVERLAY", "TRANSFER", "CARGO_IN02_TO_STORAGE", True),
    ("CARGO_WRAPPED_IN03_BUFFERED", "IN03_COIL_STORAGE", "WORKPIECE", "NONE", "CARGO_IN03_BUFFER", False),
    ("CARGO_DEPACK_ROLLERS", "IN04_DEPACK", "MOVING_OVERLAY", "ROLLERS", "CARGO_IN04_DEPACK_POSE", False),
    ("CARGO_DEPACK_WRAP_REMOVE", "IN04_DEPACK", "MOVING_OVERLAY", "WRAP_REMOVE", "CARGO_IN04_DEPACK_POSE", False),
    ("CARGO_DEPACK_VISION_INSPECT", "IN04_DEPACK", "MOVING_OVERLAY", "VISION_INSPECT", "CARGO_IN04_DEPACK_POSE", False),
    ("CARGO_BARE_IN05_OUTPUT_TO_RACK", "IN05_COIL_PREP", "MOVING_OVERLAY", "FEED", "CARGO_IN05_OUTPUT_TO_RACK", True),
    ("CARGO_BARE_S01_CART_TO_DECOILER", "S01_DESTACK_LOAD", "MOVING_OVERLAY", "LOAD", "COILTRANSFERTODECOILER", True),
    ("CARGO_S02_PANEL_BLANK", "S02_DEEP_DRAW", "WORKPIECE", "NONE", "CARGO_S02_WORKPIECE", False),
    ("CARGO_S03_WORKPIECE_REGISTERED", "S03_FORM", "WORKPIECE", "NONE", "CARGO_S03_FORM_WORKPIECE", False),
    ("CARGO_S04_WORKPIECE_REGISTERED", "S04_TRIM", "WORKPIECE", "NONE", "CARGO_S04_TRIM_WORKPIECE", False),
    ("CARGO_S05_WORKPIECE_REGISTERED", "S05_PIERCE", "WORKPIECE", "NONE", "CARGO_S05_PIERCE_WORKPIECE", False),
    ("CARGO_S06_WORKPIECE_REGISTERED", "S06_FLANGE", "WORKPIECE", "NONE", "CARGO_S06_FLANGE_WORKPIECE", False),
    ("CARGO_TRANSFER_PANEL_BLANK_AT_S02__TO__PANEL_FORMED", "S02_DEEP_DRAW", "CYAN_TRANSFER", "NONE", "CARGO_PANEL_BLANK_AT_S02__TO__PANEL_FORMED", True),
    ("CARGO_TRANSFER_PANEL_FORMED__TO__PANEL_TRIMMED", "S03_FORM", "CYAN_TRANSFER", "NONE", "CARGO_PANEL_FORMED__TO__PANEL_TRIMMED", True),
    ("CARGO_TRANSFER_PANEL_TRIMMED__TO__PANEL_PIERCED", "S04_TRIM", "CYAN_TRANSFER", "NONE", "CARGO_PANEL_TRIMMED__TO__PANEL_PIERCED", True),
    ("CARGO_TRANSFER_PANEL_PIERCED__TO__PANEL_FLANGED", "S05_PIERCE", "CYAN_TRANSFER", "NONE", "CARGO_PANEL_PIERCED__TO__PANEL_FLANGED", True),
    ("CARGO_TRANSFER_PANEL_FLANGED__TO__PANEL_COMPLETE_AT_S07_INSPECTION", "S06_FLANGE", "CYAN_TRANSFER", "NONE", "CARGO_PANEL_FLANGED__TO__PANEL_COMPLETE_AT_S07_INSPECTION", True),
    ("CARGO_S07_PANEL_PARKED", "S07_INSPECTION", "MOVING_OVERLAY", "PARKED", "CARGO_S07_PANEL_PARKED", False),
    ("CARGO_S07_PANEL_PICK", "S07_INSPECTION", "MOVING_OVERLAY", "PICK", "CARGO_S07_PANEL_PICK", True),
    ("CARGO_S07_PANEL_INSPECT", "S07_INSPECTION", "MOVING_OVERLAY", "INSPECT", "CARGO_S07_PANEL_INSPECT", False),
    ("CARGO_S07_PANEL_PLACE", "S07_INSPECTION", "MOVING_OVERLAY", "PLACE", "CARGO_S07_PANEL_PLACE", True),
    ("CARGO_S07_PALLET_BASE_PARKED", "S07_PALLETISER", "MOVING_OVERLAY", "PARKED", "CARGO_S07_PALLET_EMPTY_TO_DISPATCH_READY", True),
    ("CARGO_S07_PALLET_BASE_PICK", "S07_PALLETISER", "MOVING_OVERLAY", "PICK", "CARGO_S07_PALLET_EMPTY_TO_DISPATCH_READY", True),
    ("CARGO_S07_PALLET_BASE_PLACE", "S07_PALLETISER", "MOVING_OVERLAY", "PLACE", "CARGO_S07_PALLET_EMPTY_TO_DISPATCH_READY", True),
    ("CARGO_S07_DISPATCH_STACK_08", "SUPPORT_FLEET", "WORKPIECE", "NONE", "CARGO_S07_DISPATCH_READY", False),
)


CHECKPOINTS: Tuple[Checkpoint, ...] = (
    Checkpoint("INBOUND_LORRY_UNLOAD", EXPECTED_STATION_ROUTE_PREFIX[0], 0.20, "IN01_ARTICULATED_CARRIER", "CARGO_WRAPPED_IN01_UNLOAD", "RUNNING", "MOVING_OVERLAY", "UNLOADING", True, 0.20 / 0.48),
    Checkpoint("INBOUND_COIL_AGV_TRANSFER", EXPECTED_STATION_ROUTE_PREFIX[0], 0.75, "IN02_COIL_HANDLER_AGV", "CARGO_WRAPPED_IN02_STORAGE_TRANSFER", "MOVING", "MOVING_OVERLAY", "TRANSFER", True, (0.75 - 0.48) / 0.52),
    Checkpoint("WRAPPED_COIL_STORAGE", EXPECTED_STATION_ROUTE_PREFIX[1], 0.50, "IN03_COIL_STORAGE", "CARGO_WRAPPED_IN03_BUFFERED", "RUNNING", "WORKPIECE"),
    Checkpoint("DEPACK_WRAP_REMOVE", EXPECTED_STATION_ROUTE_PREFIX[2], 0.20, "IN04_DEPACK", "CARGO_DEPACK_WRAP_REMOVE", "RUNNING", "MOVING_OVERLAY", "WRAP_REMOVE"),
    Checkpoint("COIL_PREPARATION_TRANSFER", EXPECTED_STATION_ROUTE_PREFIX[2], 0.90, "IN05_COIL_PREP", "CARGO_BARE_IN05_OUTPUT_TO_RACK", "RUNNING", "MOVING_OVERLAY", "FEED", True, (0.90 - 0.38) / 0.62),
    Checkpoint("S01_COIL_CART_MID_TRANSFER", EXPECTED_STATION_ROUTE_PREFIX[3], 0.18, "S01_DESTACK_LOAD", "CARGO_BARE_S01_CART_TO_DECOILER", "MOVING", "MOVING_OVERLAY", "LOAD", True, 0.50),
    Checkpoint("S04_CONTACT", EXPECTED_STATION_ROUTE_PREFIX[4], (2.0 + 0.60) / 5.0, "S04_TRIM", "CARGO_S04_WORKPIECE_REGISTERED", "RUNNING", "WORKPIECE", source_role="FRAME_STATE", source_state="CONTACT"),
    Checkpoint("S06_TO_INSPECTION_TRANSFER", EXPECTED_STATION_ROUTE_PREFIX[4], 0.99, "S06_FLANGE", "CARGO_TRANSFER_PANEL_FLANGED__TO__PANEL_COMPLETE_AT_S07_INSPECTION", "MOVING", "CYAN_TRANSFER", require_motion=True, expected_motion_alpha=0.95),
    Checkpoint("S07_INSPECTION_SCAN", EXPECTED_STATION_ROUTE_PREFIX[5], 0.60, "S07_INSPECTION", "CARGO_S07_PANEL_INSPECT", "MOVING", "MOVING_OVERLAY", "INSPECT"),
    Checkpoint("S07_PALLETISER_PLACE", EXPECTED_STATION_ROUTE_PREFIX[6], 0.70, "S07_PALLETISER", "CARGO_S07_PALLET_BASE_PLACE", "MOVING", "MOVING_OVERLAY", "PLACE", True, 0.70),
    Checkpoint("OUTBOUND_PANEL_STILLAGE_TRANSFER", EXPECTED_STATION_ROUTE_PREFIX[6], 0.90, "SUPPORT_FLEET", "CARGO_S07_DISPATCH_STACK_08", "MOVING", "WORKPIECE"),
)


class GuardError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise GuardError("PRESSSHOP_2126_EXACT_MAP_PIE_V001_FAIL: " + message)


def sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(block)
    return hasher.hexdigest()


def file_fingerprint(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        fail("required file is missing: {}".format(path))
    stat = path.stat()
    return {
        "path": str(path),
        "sha256": sha256(path),
        "bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _require_sha(value: Optional[str], context: str) -> str:
    if value is None or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        fail(context + " must be an exact lower-case SHA-256")
    return value


def resolve_profile(environ: Mapping[str, str] = os.environ) -> CandidateProfile:
    key = environ.get(PROFILE_ENV, "v003").strip().lower()
    if key not in PROFILES:
        fail("{} must be one of: {}".format(PROFILE_ENV, ", ".join(PROFILES)))
    base = PROFILES[key]
    env_receipt = environ.get(RECEIPT_SHA_ENV, "").strip().lower() or None
    env_map = environ.get(MAP_SHA_ENV, "").strip().lower() or None
    if key == "v003":
        if env_receipt and env_receipt != base.expected_receipt_sha256:
            fail("v003 receipt override does not match its frozen hash")
        if env_map and env_map != base.expected_map_sha256:
            fail("v003 map override does not match its frozen hash")
        return base
    receipt_sha = _require_sha(
        env_receipt, "{} for {}".format(RECEIPT_SHA_ENV, key))
    map_sha = _require_sha(
        env_map, "{} for {}".format(MAP_SHA_ENV, key))
    return CandidateProfile(
        **{
            **base.__dict__,
            "expected_receipt_sha256": receipt_sha,
            "expected_map_sha256": map_sha,
        }
    )


def normalise_name(value: Any) -> str:
    text = str(value if value is not None else "").strip()
    if text in ("", "None", "NAME_None"):
        return "NONE"
    if ":" in text and text.startswith("<"):
        text = text.split(".")[-1].split(":", 1)[0]
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    return re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").upper() or "NONE"


def _read_prop(obj: Any, name: str) -> Any:
    try:
        return obj.get_editor_property(name)
    except Exception:
        if hasattr(obj, name):
            return getattr(obj, name)
        raise


def _tuple_result(value: Any) -> Tuple[Any, ...]:
    return value if isinstance(value, tuple) else (value,)


def _fail_reflected_native_false(context: str) -> None:
    fail(
        context
        + " returned native false through Unreal Python's bool+out-parameter "
        "contract (None); the generated wrapper suppresses OutReason on failure"
    )


def parse_bool_reason(result: Any, context: str) -> str:
    if result is None:
        _fail_reflected_native_false(context)
    values = _tuple_result(result)
    if len(values) == 1 and isinstance(values[0], bool):
        if not values[0]:
            fail(context + " returned false")
        return ""
    if len(values) >= 1 and isinstance(values[0], bool):
        if not values[0]:
            fail("{} failed: {}".format(context, values[-1]))
        return str(values[-1]) if len(values) > 1 else ""
    if len(values) == 1 and isinstance(values[0], str):
        return str(values[0])
    fail(context + " returned an unsupported reflected result: {!r}".format(result))


def parse_payload_reason(result: Any, payload_count: int, context: str) -> Tuple[Any, ...]:
    if result is None:
        _fail_reflected_native_false(context)
    values = _tuple_result(result)
    if len(values) == payload_count + 2 and isinstance(values[0], bool):
        if not values[0]:
            fail("{} failed: {}".format(context, values[-1]))
        return values[1:-1]
    if len(values) == payload_count + 1:
        return values[:-1]
    if payload_count == 1 and len(values) == 1 and not isinstance(values[0], bool):
        return values
    fail(context + " returned an unsupported reflected result: {!r}".format(result))


def canonical_json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False,
                       indent=2, sort_keys=True) + "\n").encode("utf-8")


def _require_receipt_sha256_field(receipt: Mapping[str, Any], key: str) -> str:
    value = receipt.get(key)
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        fail("v006 receipt {} must be an exact lower-case SHA-256".format(key))
    return value


def validate_v006_semantic_fingerprint_contract(
        receipt: Mapping[str, Any]) -> None:
    """Gate preservation on normalized semantics, never ephemeral actor paths."""
    if (receipt.get("clone_semantic_fingerprint_normalization")
            != V006_SEMANTIC_FINGERPRINT_NORMALIZATION):
        fail("v006 clone semantic fingerprint normalization contract changed")

    for prefix in (
            "visual_layer_actor", "machinery_actor", "cargo_actor"):
        before_key = prefix + "_semantic_fingerprints_before_sha256"
        after_key = prefix + "_semantic_fingerprints_after_sha256"
        before_hash = _require_receipt_sha256_field(receipt, before_key)
        after_hash = _require_receipt_sha256_field(receipt, after_key)
        if after_hash != before_hash:
            fail("v006 preserved semantic actor fingerprint changed: " + prefix)

    # The path-keyed hashes explain why a saved-map clone receives new object
    # paths.  Require well-formed provenance and the explicit diagnostic-only
    # declaration, but deliberately do not compare these values to each other
    # or use them as visual-preservation authority.
    for key in (
            "source_path_keyed_visual_fingerprints_sha256",
            "source_path_keyed_machinery_fingerprints_sha256",
            "source_path_keyed_cargo_fingerprints_sha256"):
        _require_receipt_sha256_field(receipt, key)
    legacy_hashes = receipt.get(
        "source_loaded_legacy_path_keyed_fingerprint_hashes")
    legacy_matches = receipt.get(
        "source_loaded_legacy_receipt_path_hash_matches")
    if (not isinstance(legacy_hashes, Mapping)
            or set(legacy_hashes) != V006_LEGACY_PATH_GROUP_KEYS):
        fail("v006 legacy path-keyed diagnostic hash inventory changed")
    if (not isinstance(legacy_matches, Mapping)
            or set(legacy_matches) != V006_LEGACY_PATH_GROUP_KEYS
            or any(not isinstance(value, bool)
                   for value in legacy_matches.values())):
        fail("v006 legacy receipt path-match diagnostic inventory changed")
    for key in sorted(V006_LEGACY_PATH_GROUP_KEYS):
        _require_receipt_sha256_field(legacy_hashes, key)
    if receipt.get("source_loaded_legacy_path_hash_status") != (
            V006_LEGACY_PATH_HASH_STATUS):
        fail("v006 legacy path hash diagnostic-only status changed")


def load_and_validate_source_receipt(profile: CandidateProfile) -> Dict[str, Any]:
    actual_sha = sha256(profile.source_receipt) if profile.source_receipt.is_file() else None
    expected_receipt_sha = _require_sha(
        profile.expected_receipt_sha256, "profile receipt SHA-256"
    )
    if actual_sha != expected_receipt_sha:
        fail("source integration receipt is missing or differs from the pinned hash")
    try:
        receipt = json.loads(profile.source_receipt.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail("source integration receipt is not UTF-8 JSON: {}".format(exc))
    if not isinstance(receipt, dict):
        fail("source integration receipt root must be an object")
    exact = {
        "schema": profile.receipt_schema,
        "status": profile.receipt_status,
        "target_map": profile.target_map,
        "target_map_sha256": profile.expected_map_sha256,
        "cargo_layer_count": EXPECTED_CARGO_LAYER_COUNT,
        "combined_visual_layer_count": EXPECTED_VISUAL_LAYER_COUNT,
        "runtime_validated": False,
        "packaged_build_validated": False,
    }
    if profile.key == "v003":
        exact.update({
            "existing_runtime_presentation_adapter_count_preserved": 1,
            "collision_enabled_on_cargo_layers": False,
        })
    elif profile.key == "v004":
        exact.update({
            "source_map": PROFILES["v003"].target_map,
            "source_map_sha256": PROFILES["v003"].expected_map_sha256,
            "source_receipt_sha256": PROFILES["v003"].expected_receipt_sha256,
            "cargo_actor_mutated_count": 0,
            "machinery_actor_mutated_count": 0,
            "source_actor_removed_count": 0,
            "native_cpp_modified": False,
        })
    elif profile.key == "v006":
        exact.update({
            "source_map": V005_SOURCE_MAP,
            "source_map_sha256": V005_SOURCE_MAP_SHA256,
            "source_receipt_sha256": V005_SOURCE_RECEIPT_SHA256,
            "cargo_actor_mutated_count": 0,
            "machinery_actor_mutated_count": 0,
            "source_actor_removed_count": 0,
            "native_cpp_modified": False,
        })
    else:  # Defensive even though resolve_profile already rejects unknown keys.
        fail("source receipt validator has no contract for profile " + profile.key)
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("source receipt {} mismatch: {!r} != {!r}".format(
                key, receipt.get(key), expected))
    if profile.target_file.is_file():
        target = file_fingerprint(profile.target_file)
        if target["sha256"] != profile.expected_map_sha256:
            fail("target map differs from its pinned hash")
        if int(receipt.get("target_map_bytes", -1)) != target["bytes"]:
            fail("target map byte count differs from the source receipt")
    else:
        fail("target map is missing: {}".format(profile.target_file))
    if profile.key == "v003":
        validate_cargo_receipt_contract(receipt)
    elif profile.key == "v004":
        nested_path = Path(str(receipt.get("source_receipt", ""))).resolve()
        expected_nested = PROFILES["v003"].source_receipt.resolve()
        if nested_path != expected_nested:
            fail("v004 receipt does not cite the frozen v003 cargo receipt")
        if sha256(nested_path) != PROFILES["v003"].expected_receipt_sha256:
            fail("v004 cargo provenance receipt differs from its frozen hash")
        nested = json.loads(nested_path.read_text(encoding="utf-8"))
        validate_cargo_receipt_contract(nested)
    elif profile.key == "v006":
        nested_path = Path(str(receipt.get("source_receipt", ""))).resolve()
        if nested_path != V005_SOURCE_RECEIPT.resolve():
            fail("v006 receipt does not cite the frozen v005 install receipt")
        if (not nested_path.is_file()
                or sha256(nested_path) != V005_SOURCE_RECEIPT_SHA256):
            fail("v006 v005 provenance receipt differs from its frozen hash")
        if (not V005_SOURCE_MAP_FILE.is_file()
                or sha256(V005_SOURCE_MAP_FILE) != V005_SOURCE_MAP_SHA256):
            fail("v006 v005 source map differs from its frozen hash")
        validate_v006_semantic_fingerprint_contract(receipt)
        frozen_cargo = json.loads(
            PROFILES["v003"].source_receipt.read_text(encoding="utf-8"))
        validate_cargo_receipt_contract(frozen_cargo)
    return receipt


def validate_cargo_receipt_contract(receipt: Mapping[str, Any]) -> None:
    rows = receipt.get("cargo_layers")
    if not isinstance(rows, list) or len(rows) != EXPECTED_CARGO_LAYER_COUNT:
        fail("source receipt must contain exactly 26 cargo layer rows")
    actual: Dict[str, Tuple[str, str, str, str, bool]] = {}
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("metadata_readback"), dict):
            fail("cargo layer row is missing metadata_readback")
        meta = row["metadata_readback"]
        layer_id = normalise_name(meta.get("LayerId"))
        if layer_id in actual:
            fail("duplicate cargo LayerId in receipt: " + layer_id)
        actual[layer_id] = (
            normalise_name(meta.get("MachineId")),
            normalise_name(meta.get("LayerRole")),
            normalise_name(meta.get("StateId")),
            normalise_name(meta.get("MotionChannel")),
            bool(meta.get("bHasMotionRange")),
        )
    expected = {
        normalise_name(layer): (
            normalise_name(machine), normalise_name(role),
            normalise_name(state), normalise_name(channel), moving,
        )
        for layer, machine, role, state, channel, moving in CARGO_CONTRACT
    }
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        wrong = sorted(key for key in set(actual) & set(expected)
                       if actual[key] != expected[key])
        fail("cargo metadata contract mismatch; missing={} extra={} wrong={}".format(
            missing, extra, wrong))


def verify_protected_files() -> Dict[str, Dict[str, Any]]:
    output: Dict[str, Dict[str, Any]] = {}
    for path, expected_sha in PROTECTED_AUTHORITY_FILES.items():
        fp = file_fingerprint(path)
        if fp["sha256"] != expected_sha:
            fail("protected authority differs from reviewed hash: {}".format(path))
        output[str(path)] = fp
    return output


def tracked_evidence_paths(profile: CandidateProfile) -> Tuple[Path, ...]:
    ordered = list(PROTECTED_AUTHORITY_FILES) + [
        profile.target_file,
        profile.source_receipt,
        PROFILES["v003"].source_receipt,
    ]
    if profile.key == "v006":
        ordered.extend((V005_SOURCE_MAP_FILE, V005_SOURCE_RECEIPT))
    unique: List[Path] = []
    seen = set()
    for path in ordered:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            unique.append(path)
    return tuple(unique)


def _dirty_packages() -> Dict[str, List[str]]:
    if unreal is None:
        return {"content": [], "maps": []}
    utility = unreal.EditorLoadingAndSavingUtils
    return {
        "content": sorted(str(value) for value in utility.get_dirty_content_packages()),
        "maps": sorted(str(value) for value in utility.get_dirty_map_packages()),
    }


def _world_package_name(world: Any) -> str:
    candidates: List[str] = []
    for getter in (
        lambda: world.get_outermost().get_name(),
        lambda: world.get_path_name(),
        lambda: world.get_name(),
    ):
        try:
            candidates.append(str(getter()))
        except Exception:
            pass
    return " | ".join(candidates)


def world_is_exact_target(world: Any, target_map: str) -> bool:
    text = _world_package_name(world)
    leaf = target_map.rsplit("/", 1)[-1]
    if leaf not in text:
        return False
    other_profiles = [
        profile.target_map.rsplit("/", 1)[-1]
        for profile in PROFILES.values()
        if profile.target_map != target_map
    ]
    return not any(other in text for other in other_profiles)


def _load_class(path: str) -> Any:
    actor_class = unreal.load_class(None, path)
    if actor_class is None:
        fail("compiled native class is unavailable: " + path)
    return actor_class


def _actors(world: Any, class_path: str) -> List[Any]:
    return list(unreal.GameplayStatics.get_all_actors_of_class(
        world, _load_class(class_path)))


def _actor_label(actor: Any) -> str:
    try:
        return str(actor.get_actor_label())
    except Exception:
        return str(actor.get_name())


def _layer_metadata(actor: Any) -> Dict[str, Any]:
    return {
        "layer_id": normalise_name(_read_prop(actor, "layer_id")),
        "assembly_id": normalise_name(_read_prop(actor, "assembly_id")),
        "machine_id": normalise_name(_read_prop(actor, "machine_id")),
        "role": normalise_name(_read_prop(actor, "layer_role")),
        "state": normalise_name(_read_prop(actor, "state_id")),
        "motion_channel": normalise_name(_read_prop(actor, "motion_channel")),
        "has_motion_range": bool(_read_prop(actor, "has_motion_range")),
    }


def _component_visible(component: Any) -> bool:
    for call in (
        lambda: bool(component.is_visible()),
        lambda: bool(component.get_visible_flag()),
        lambda: bool(_read_prop(component, "visible")),
    ):
        try:
            visible = call()
            break
        except Exception:
            visible = True
    try:
        hidden = bool(_read_prop(component, "hidden_in_game"))
    except Exception:
        hidden = False
    return visible and not hidden


def _actor_visible(actor: Any) -> bool:
    hidden = False
    for call in (
        lambda: bool(actor.get_actor_hidden_in_game()),
        lambda: bool(actor.is_hidden()),
    ):
        try:
            hidden = call()
            break
        except Exception:
            pass
    component = _read_prop(actor, "static_mesh_component")
    return not hidden and _component_visible(component)


def _collision_disabled(actor: Any) -> bool:
    try:
        if bool(actor.get_actor_enable_collision()):
            return False
    except Exception:
        pass
    component = _read_prop(actor, "static_mesh_component")
    try:
        state = normalise_name(component.get_collision_enabled())
        return state in ("NO_COLLISION", "NONE") or "NO_COLLISION" in state
    except Exception:
        return not bool(actor.get_actor_enable_collision())


def _vector(value: Any) -> Tuple[float, float, float]:
    return (float(value.x), float(value.y), float(value.z))


def _transform_location(transform: Any) -> Tuple[float, float, float]:
    try:
        return _vector(transform.translation)
    except Exception:
        return _vector(transform.get_editor_property("translation"))


def _lerp(start: Sequence[float], end: Sequence[float], alpha: float) -> Tuple[float, float, float]:
    return tuple(float(a) + (float(b) - float(a)) * alpha for a, b in zip(start, end))


def _distance(a: Sequence[float], b: Sequence[float]) -> float:
    return math.sqrt(sum((float(x) - float(y)) ** 2 for x, y in zip(a, b)))


def _status(coordinator: Any, unit_id: Any) -> Any:
    return parse_payload_reason(
        coordinator.get_vehicle_runtime_status(unit_id), 1,
        "GetVehicleRuntimeStatus",
    )[0]


def _status_snapshot(status: Any) -> Dict[str, Any]:
    return {
        "unit_id": normalise_name(_read_prop(status, "unit_id")),
        "station_id": normalise_name(_read_prop(status, "current_station_id")),
        "station_cursor": int(_read_prop(status, "station_cursor")),
        "completed_station_count": int(_read_prop(status, "completed_station_count")),
        "stage": normalise_name(_read_prop(status, "stage")),
        "quality_state": normalise_name(_read_prop(status, "quality_state")),
        "progress01": float(_read_prop(status, "normalized_cycle_progress")),
        "cycle_duration_seconds": float(_read_prop(status, "cycle_duration_seconds")),
        "started": bool(_read_prop(status, "started")),
        "at_quality_gate": bool(_read_prop(status, "at_quality_gate")),
        "awaiting_quality_result": bool(_read_prop(status, "awaiting_quality_result")),
        "completed": bool(_read_prop(status, "completed")),
        "dispatched": bool(_read_prop(status, "dispatched")),
    }


def validate_route_profile_contract(profile: CandidateProfile,
                                    route: Sequence[Any], topology: Any) -> Dict[str, Any]:
    if len(route) != EXPECTED_ROUTE_COUNT:
        fail("configured route does not contain exactly 57 stations")
    topology_id = normalise_name(topology)
    if not topology_id.startswith(profile.expected_topology_prefix):
        fail("configured topology does not match {}: {}".format(
            profile.runtime_route_contract, topology_id))
    inspection = route[5]
    snapshot = {
        "route_index": int(_read_prop(inspection, "route_index")),
        "station_id": normalise_name(_read_prop(inspection, "station_id")),
        "semantic_stage": normalise_name(_read_prop(inspection, "semantic_stage")),
        "quality_gate": bool(_read_prop(inspection, "quality_gate")),
    }
    if snapshot["route_index"] != 5:
        fail("Press inspection is not route index 5")
    if snapshot["station_id"] != normalise_name(EXPECTED_STATION_ROUTE_PREFIX[5]):
        fail("route index 5 is not the canonical Press inspection station")
    if snapshot["semantic_stage"] != profile.expected_inspection_semantic_stage:
        fail("Press inspection semantic stage does not match the selected profile")
    if snapshot["quality_gate"] != profile.expects_press_inspection_quality_gate:
        fail("Press inspection quality-gate flag does not match the selected profile")
    return {
        "contract": profile.runtime_route_contract,
        "topology_id": topology_id,
        "topology_prefix": profile.expected_topology_prefix,
        "inspection_step": snapshot,
    }


def validate_quality_lifecycle_contract(
        profile: CandidateProfile,
        in_cycle: Mapping[str, Any], hold: Mapping[str, Any],
        after_pass: Mapping[str, Any], released: Mapping[str, Any]) -> None:
    inspection = normalise_name(EXPECTED_STATION_ROUTE_PREFIX[5])
    dispatch = normalise_name(EXPECTED_STATION_ROUTE_PREFIX[6])
    if not profile.expects_press_inspection_quality_gate:
        fail("quality lifecycle may only run for a gate-enabled profile")
    if (in_cycle.get("station_id") != inspection
            or not in_cycle.get("at_quality_gate")
            or in_cycle.get("awaiting_quality_result")
            or float(in_cycle.get("progress01", -1.0)) >= 1.0):
        fail("Press inspection did not expose an active pre-completion quality gate")
    if (hold.get("station_id") != inspection
            or not hold.get("at_quality_gate")
            or not hold.get("awaiting_quality_result")
            or abs(float(hold.get("progress01", -1.0)) - 1.0) > 0.002
            or normalise_name(hold.get("quality_state")) != "PENDING"):
        fail("completed Press inspection did not hold pending a quality result")
    if (after_pass.get("station_id") != inspection
            or not after_pass.get("at_quality_gate")
            or after_pass.get("awaiting_quality_result")
            or normalise_name(after_pass.get("quality_state")) != "PASSED"):
        fail("passing quality evidence did not clear the inspection wait state")
    if (released.get("station_id") != dispatch
            or released.get("station_cursor") != 6
            or released.get("at_quality_gate")
            or released.get("awaiting_quality_result")
            or normalise_name(released.get("quality_state")) != "PASSED"):
        fail("passed Press inspection did not release the same unit to panel dispatch")


def _passed_quality_state() -> Any:
    if unreal is None:
        fail("quality enum lookup requires Unreal")
    for enum_name in (
            "LBOneFactoryVehicleQualityState",
            "ELBOneFactoryVehicleQualityState"):
        enum_type = getattr(unreal, enum_name, None)
        if enum_type is None:
            continue
        for value_name in ("PASSED", "Passed"):
            if hasattr(enum_type, value_name):
                return getattr(enum_type, value_name)
    fail("compiled Passed vehicle-quality enum is unavailable")


def _set_bool_property(actor: Any, name: str, value: bool) -> None:
    actor.set_editor_property(name, value)
    if bool(_read_prop(actor, name)) != value:
        fail("runtime coordinator property did not read back: " + name)


def freeze_runtime_drivers(coordinator: Any) -> Dict[str, bool]:
    """Freeze transient automation before the presentation warm-up interval."""
    _set_bool_property(
        coordinator, "advance_started_vehicles_on_actor_tick", False)
    _set_bool_property(coordinator, "auto_dispatch_open_contracts", False)
    return {
        "advance_started_vehicles_on_actor_tick": bool(_read_prop(
            coordinator, "advance_started_vehicles_on_actor_tick")),
        "auto_dispatch_open_contracts": bool(_read_prop(
            coordinator, "auto_dispatch_open_contracts")),
    }


def _seek_progress(coordinator: Any, unit_id: Any, station_id: str,
                   progress01: float) -> Dict[str, Any]:
    before = _status_snapshot(_status(coordinator, unit_id))
    if before["station_id"] != normalise_name(station_id):
        fail("expected station {} but unit is at {}".format(
            station_id, before["station_id"]))
    if progress01 + 1e-4 < before["progress01"]:
        fail("checkpoint progress would rewind native runtime state")
    duration = before["cycle_duration_seconds"]
    if not math.isfinite(duration) or duration <= 0.0:
        fail("native runtime reported an invalid cycle duration")
    delta = max(0.0, progress01 - before["progress01"]) * duration
    if delta > 0.0:
        parse_bool_reason(coordinator.tick_vehicle(unit_id, float(delta)), "TickVehicle")
    after = _status_snapshot(_status(coordinator, unit_id))
    if after["station_id"] != normalise_name(station_id):
        fail("TickVehicle unexpectedly left checkpoint station")
    if abs(after["progress01"] - progress01) > 0.002:
        fail("native runtime missed requested checkpoint progress: {} vs {}".format(
            after["progress01"], progress01))
    return after


def _advance_station(coordinator: Any, unit_id: Any, station_id: str) -> Dict[str, Any]:
    before = _status_snapshot(_status(coordinator, unit_id))
    if before["station_id"] != normalise_name(station_id):
        fail("cannot advance: unit is not at " + station_id)
    remaining = max(0.0, 1.0 - before["progress01"]) * before["cycle_duration_seconds"]
    parse_bool_reason(
        coordinator.tick_vehicle(unit_id, float(remaining + 1.0)),
        "TickVehicle station advance",
    )
    after = _status_snapshot(_status(coordinator, unit_id))
    if after["station_id"] == before["station_id"]:
        fail("native runtime did not advance from " + station_id)
    return after


def _refresh(presentation: Any) -> str:
    return parse_bool_reason(presentation.refresh_from_runtime(), "RefreshFromRuntime")


def _beacon_state(presentation: Any, machine_id: str) -> str:
    beacon = presentation.get_status_beacon(unreal.Name(machine_id))
    if beacon is None:
        fail("presentation has no status beacon for " + machine_id)
    return normalise_name(beacon.get_status())


def _exercise_press_inspection_quality_gate(
        profile: CandidateProfile, coordinator: Any, unit_id: Any,
        presentation: Any, layers_by_id: Mapping[str, Any],
        in_cycle: Mapping[str, Any]) -> Dict[str, Any]:
    if not profile.expects_press_inspection_quality_gate:
        fail("refusing to exercise a quality gate under the legacy v003 profile")
    inspection_station = normalise_name(EXPECTED_STATION_ROUTE_PREFIX[5])
    dispatch_station = normalise_name(EXPECTED_STATION_ROUTE_PREFIX[6])
    before = _status_snapshot(_status(coordinator, unit_id))
    if before != dict(in_cycle):
        fail("inspection status changed before the quality-hold exercise")
    if before["station_id"] != inspection_station:
        fail("quality-hold exercise did not begin at Press inspection")
    remaining = max(0.0, 1.0 - before["progress01"]) * before[
        "cycle_duration_seconds"]
    hold_reason = parse_bool_reason(
        coordinator.tick_vehicle(unit_id, float(remaining + 1.0)),
        "TickVehicle inspection completion hold",
    )
    hold = _status_snapshot(_status(coordinator, unit_id))
    hold_refresh_reason = _refresh(presentation)
    hold_beacon_component = presentation.get_status_beacon(
        unreal.Name("S07_INSPECTION"))
    if hold_beacon_component is None:
        fail("presentation has no status beacon for S07_INSPECTION")
    hold_beacon = normalise_name(hold_beacon_component.get_status())
    hold_amber_lamp_lit = bool(hold_beacon_component.is_amber_lamp_lit())
    if hold_beacon != "WAITING" or not hold_amber_lamp_lit:
        fail("Press inspection hold did not expose its visible amber waiting beacon")
    place_layer = layers_by_id.get("CARGO_S07_PANEL_PLACE")
    if place_layer is None or not _actor_visible(place_layer):
        fail("Press inspection hold does not retain the visible panel-place pose")
    place_meta = _layer_metadata(place_layer)
    if (place_meta["machine_id"] != "S07_INSPECTION"
            or place_meta["role"] != "MOVING_OVERLAY"
            or place_meta["state"] != "PLACE"):
        fail("Press inspection hold is bound to the wrong visual pose")

    pass_reason = parse_bool_reason(
        coordinator.submit_runtime_quality_result(
            unit_id, _passed_quality_state(),
            unreal.Name(QUALITY_PASS_EVIDENCE_ID)),
        "SubmitRuntimeQualityResult Press inspection pass",
    )
    after_pass = _status_snapshot(_status(coordinator, unit_id))
    release_reason = parse_bool_reason(
        coordinator.tick_vehicle(unit_id, 0.1),
        "TickVehicle Press inspection release",
    )
    released = _status_snapshot(_status(coordinator, unit_id))
    release_refresh_reason = _refresh(presentation)
    validate_quality_lifecycle_contract(
        profile, in_cycle, hold, after_pass, released)
    if released["unit_id"] != in_cycle["unit_id"]:
        fail("quality release changed the canonical UnitId")
    if released["station_id"] != dispatch_station:
        fail("quality release did not enter canonical panel dispatch")
    return {
        "inspection_in_cycle": dict(in_cycle),
        "completion_tick_reason": hold_reason,
        "completed_hold": hold,
        "hold_refresh_reason": hold_refresh_reason,
        "hold_beacon_state": hold_beacon,
        "hold_amber_lamp_lit": hold_amber_lamp_lit,
        "hold_cargo_layer": place_meta,
        "hold_cargo_visible": True,
        "quality_pass_evidence_id": QUALITY_PASS_EVIDENCE_ID,
        "quality_pass_submission_reason": pass_reason,
        "after_pass_submission": after_pass,
        "release_tick_reason": release_reason,
        "released_to_panel_dispatch": released,
        "release_refresh_reason": release_refresh_reason,
        "same_unit_id_preserved": True,
    }


def _verify_motion(actor: Any, expected_alpha: Optional[float]) -> Dict[str, Any]:
    if not bool(_read_prop(actor, "has_motion_range")):
        fail("representative mover has no authored motion range: " + _actor_label(actor))
    start = _transform_location(_read_prop(actor, "motion_start"))
    end = _transform_location(_read_prop(actor, "motion_end"))
    current = _vector(actor.get_actor_location())
    span = _distance(start, end)
    if span <= 1.0:
        fail("representative mover range is too small")
    if expected_alpha is not None:
        expected = _lerp(start, end, expected_alpha)
        if _distance(current, expected) > POSITION_TOLERANCE_CM:
            fail("mover location does not match native presentation alpha")
    elif _distance(current, start) <= 0.25:
        fail("representative mover remained at its authored start")
    return {
        "start_cm": list(start), "end_cm": list(end),
        "observed_cm": list(current), "span_cm": span,
        "expected_alpha": expected_alpha,
    }


def _sample_checkpoint(checkpoint: Checkpoint, coordinator: Any, unit_id: Any,
                       presentation: Any, layers_by_id: Mapping[str, Any],
                       all_layers: Sequence[Any]) -> Dict[str, Any]:
    status = _seek_progress(coordinator, unit_id, checkpoint.station_id,
                            checkpoint.progress01)
    refresh_reason = _refresh(presentation)
    layer = layers_by_id.get(normalise_name(checkpoint.cargo_layer_id))
    if layer is None:
        fail("checkpoint cargo layer is not bound: " + checkpoint.cargo_layer_id)
    meta = _layer_metadata(layer)
    if meta["machine_id"] != normalise_name(checkpoint.machine_id):
        fail("checkpoint cargo layer machine binding mismatch")
    if meta["role"] != normalise_name(checkpoint.expected_role):
        fail("checkpoint cargo layer role mismatch")
    if meta["state"] != normalise_name(checkpoint.expected_state):
        fail("checkpoint cargo layer state mismatch")
    if not _actor_visible(layer):
        fail("checkpoint cargo layer is not visibly enabled: " + checkpoint.cargo_layer_id)
    beacon = _beacon_state(presentation, checkpoint.machine_id)
    if beacon != normalise_name(checkpoint.expected_beacon):
        fail("{} beacon mismatch: {} != {}".format(
            checkpoint.machine_id, beacon, checkpoint.expected_beacon))
    motion: Optional[Dict[str, Any]] = None
    if checkpoint.require_motion:
        motion = _verify_motion(layer, checkpoint.expected_motion_alpha)
    source_match: Optional[Dict[str, Any]] = None
    if checkpoint.source_role:
        candidates = []
        for other in all_layers:
            other_meta = _layer_metadata(other)
            if (other_meta["machine_id"] == normalise_name(checkpoint.machine_id)
                    and other_meta["role"] == normalise_name(checkpoint.source_role)
                    and (checkpoint.source_state is None or
                         other_meta["state"] == normalise_name(checkpoint.source_state))
                    and _actor_visible(other)):
                candidates.append(other)
        if len(candidates) != 1:
            fail("checkpoint source-state layer did not resolve exactly once")
        source_match = _layer_metadata(candidates[0])
    return {
        "checkpoint_id": checkpoint.checkpoint_id,
        "status": status,
        "machine_id": checkpoint.machine_id,
        "beacon_state": beacon,
        "cargo_layer": meta,
        "cargo_visible": True,
        "motion": motion,
        "source_visual_state": source_match,
        "refresh_reason": refresh_reason,
    }


def runtime_activation_counts(world: Any) -> Dict[str, int]:
    """Count the exact native player/runtime authorities without mutating them."""
    counts = {
        "player_controller": len(_actors(world, PLAYER_CONTROLLER_CLASS)),
        "runtime_coordinator": len(_actors(world, COORDINATOR_CLASS)),
        "production": len(_actors(world, PRODUCTION_AUTHORITY_CLASS)),
    }
    for key, class_path in STARTER_LAYOUT_AUTHORITY_CLASSES.items():
        counts[key] = len(_actors(world, class_path))
    return counts


def activation_counts_ready(counts: Mapping[str, Any]) -> bool:
    """Return pending for 0, fail immediately for duplicates/invalid shapes."""
    expected = {
        "player_controller", "runtime_coordinator", "production",
        *STARTER_LAYOUT_AUTHORITY_CLASSES.keys(),
    }
    if set(counts) != expected:
        fail("native player activation count keys changed")
    ready = True
    for key in sorted(expected):
        value = counts[key]
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            fail("invalid native player activation count for " + key)
        if value > 1:
            fail("duplicate native player activation actor for {}: {}".format(
                key, value))
        ready = ready and value == 1
    return ready


def validate_native_player_activation_contract(
        snapshot: Mapping[str, Any]) -> None:
    """Pure fail-closed acceptance contract for the regular-PIE startup seam."""
    counts = snapshot.get("actor_counts")
    if not isinstance(counts, Mapping) or not activation_counts_ready(counts):
        fail("regular PIE did not create exactly one controller and five authorities")
    if snapshot.get("player_controller_class") != PLAYER_CONTROLLER_CLASS:
        fail("regular PIE did not use ALBOneFactoryPlayerController")
    if snapshot.get("primary_player_controller_matches") is not True:
        fail("regular PIE native controller is not the primary local controller")
    layouts = snapshot.get("layout_commissioned")
    if (not isinstance(layouts, Mapping)
            or set(layouts) != set(STARTER_LAYOUT_AUTHORITY_CLASSES)
            or any(value is not True for value in layouts.values())):
        fail("native player activation did not commission all four starter layouts")
    departments = snapshot.get("production_department_commissioned")
    expected_departments = {"press", "body", "paint", "assembly"}
    if (not isinstance(departments, Mapping)
            or set(departments) != expected_departments
            or any(value is not True for value in departments.values())):
        fail("native player activation did not commission all four production departments")
    contract_ids = snapshot.get("starter_contract_ids")
    if (not isinstance(contract_ids, list)
            or tuple(contract_ids) != tuple(sorted(EXPECTED_STARTER_CONTRACT_IDS))):
        fail("native player activation did not seed exactly the starter contract ladder")
    if snapshot.get("production_ledger_validated") is not True:
        fail("native player activation produced an invalid production ledger")


def capture_native_player_activation(world: Any) -> Dict[str, Any]:
    """Capture and validate the existing native startup result; never create it."""
    counts = runtime_activation_counts(world)
    if not activation_counts_ready(counts):
        fail("native player activation is incomplete")
    controllers = _actors(world, PLAYER_CONTROLLER_CLASS)
    primary = unreal.GameplayStatics.get_player_controller(world, 0)
    controller = controllers[0]
    controller_class = str(controller.get_class().get_path_name())
    primary_matches = bool(
        primary is not None
        and str(primary.get_path_name()) == str(controller.get_path_name())
    )

    layout_commissioned: Dict[str, bool] = {}
    for key, class_path in STARTER_LAYOUT_AUTHORITY_CLASSES.items():
        authority = _actors(world, class_path)[0]
        state = authority.capture_layout()
        layout_commissioned[key] = bool(_read_prop(state, "commissioned"))

    production = _actors(world, PRODUCTION_AUTHORITY_CLASS)[0]
    ledger = production.capture_ledger()
    ledger_reason = parse_bool_reason(
        unreal.LBOneFactoryProductionFlowLibrary.validate_ledger(ledger),
        "ValidateProductionLedgerAfterNativePlayerActivation",
    )
    commissioning = _read_prop(ledger, "commissioning")
    department_commissioned = {
        "press": bool(_read_prop(commissioning, "press_commissioned")),
        "body": bool(_read_prop(commissioning, "body_commissioned")),
        "paint": bool(_read_prop(commissioning, "paint_commissioned")),
        "assembly": bool(_read_prop(commissioning, "assembly_commissioned")),
    }
    contract_ids = sorted(
        normalise_name(_read_prop(contract, "contract_id"))
        for contract in list(_read_prop(ledger, "contracts"))
    )
    snapshot = {
        "pie_launch_mode": "REGULAR_PIE_NATIVE_PLAYER",
        "actor_counts": counts,
        "player_controller_class": controller_class,
        "primary_player_controller_matches": primary_matches,
        "layout_commissioned": layout_commissioned,
        "production_department_commissioned": department_commissioned,
        "starter_contract_ids": contract_ids,
        "production_ledger_validated": True,
        "production_ledger_validation_reason": ledger_reason,
    }
    validate_native_player_activation_contract(snapshot)
    return snapshot


class PieVerifier:
    def __init__(self, profile: CandidateProfile, source_receipt: Mapping[str, Any],
                 before: Mapping[str, Dict[str, Any]], dirty_before_load: Mapping[str, List[str]]) -> None:
        self.profile = profile
        self.source_receipt = dict(source_receipt)
        self.before = dict(before)
        self.dirty_before_load = dict(dirty_before_load)
        self.dirty_before_pie = _dirty_packages()
        self.started_at = time.monotonic()
        self.game_world_seen_at: Optional[float] = None
        self.pie_started_at: Optional[float] = None
        self.runtime_drivers_frozen = False
        self.native_player_activation_verified = False
        self.activation_snapshot: Optional[Dict[str, Any]] = None
        self.proof_started = False
        self.handle: Any = None
        self.finished = False
        self.checkpoints: List[Dict[str, Any]] = []
        self.quality_gate_evidence: Optional[Dict[str, Any]] = None
        self.receipt: Dict[str, Any] = {}
        self.level_editor = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        self.editor_worlds = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

    def finish(self, status: str, error: Optional[str] = None) -> None:
        if self.finished:
            return
        self.finished = True
        try:
            self.level_editor.editor_request_end_play()
        except Exception:
            pass
        after = {str(path): file_fingerprint(path)
                 for path in tracked_evidence_paths(self.profile)}
        unchanged = after == self.before
        dirty_after = _dirty_packages()
        dirty_unchanged = dirty_after == self.dirty_before_pie
        final_status = status
        if not unchanged:
            final_status = "FAIL_MAP_OR_PROTECTED_AUTHORITY_MUTATED"
        elif not dirty_unchanged:
            final_status = "FAIL_DIRTY_PACKAGE_SET_CHANGED"
        quality_present = bool(self.receipt.get(
            "press_inspection_quality_gate_present", False))
        quality_proved = bool(self.receipt.get(
            "quality_gate_behavior_proved", False))
        if (final_status.startswith("PASS_")
                and self.profile.expects_press_inspection_quality_gate
                and not quality_proved):
            final_status = "FAIL_V002_PRESS_INSPECTION_QUALITY_LIFECYCLE_UNPROVED"
        if (final_status.startswith("PASS_")
                and not self.native_player_activation_verified):
            final_status = "FAIL_NATIVE_PLAYER_ACTIVATION_UNPROVED"
        quality_gap: Optional[str] = None
        if not self.profile.expects_press_inspection_quality_gate:
            quality_gap = (
                "Frozen v003 legacy profile: OF_PRESS_PANEL_INSPECTION_001 "
                "is expected to use the V001 no-gate route. This historical "
                "profile must not be relabelled as V002 evidence."
            )
        output = {
            "schema": self.profile.output_schema,
            "status": final_status,
            "error": error,
            "profile": self.profile.key,
            "runtime_route_contract": self.profile.runtime_route_contract,
            "runtime_route_profile_validated": self.receipt.get(
                "runtime_route_profile_validated", False),
            "runtime_topology_id": self.receipt.get("runtime_topology_id"),
            "inspection_route_step": self.receipt.get("inspection_route_step"),
            "target_map": self.profile.target_map,
            "target_map_started_exactly": self.receipt.get("target_map_started_exactly", False),
            "game_world_identity": self.receipt.get("game_world_identity"),
            "game_mode_class": self.receipt.get("game_mode_class"),
            "pie_launch_mode": "REGULAR_PIE_NATIVE_PLAYER",
            "native_player_activation_contract_verified": (
                self.native_player_activation_verified),
            "native_player_activation_snapshot": self.receipt.get(
                "native_player_activation_snapshot"),
            "native_player_activation_snapshot_before_proof": self.receipt.get(
                "native_player_activation_snapshot_before_proof"),
            "player_controller_count": self.receipt.get(
                "player_controller_count", 0),
            "player_controller_class": self.receipt.get(
                "player_controller_class"),
            "runtime_authority_counts": self.receipt.get(
                "runtime_authority_counts", {}),
            "runtime_coordinator_count": self.receipt.get("runtime_coordinator_count", 0),
            "runtime_drivers_frozen_before_proof": self.receipt.get(
                "runtime_drivers_frozen_before_proof", False),
            "runtime_driver_readback": self.receipt.get("runtime_driver_readback"),
            "runtime_validation_reason": self.receipt.get("runtime_validation_reason"),
            "configured_route_count": self.receipt.get("configured_route_count"),
            "configured_route_prefix": self.receipt.get("configured_route_prefix"),
            "presentation_adapter_count": self.receipt.get("presentation_adapter_count", 0),
            "presentation_owns_production_state": False,
            "bound_visual_layer_count": self.receipt.get("bound_visual_layer_count"),
            "cargo_layer_count": self.receipt.get("cargo_layer_count"),
            "cargo_actor_contract_verified": self.receipt.get("cargo_actor_contract_verified", False),
            "cargo_machine_ids": self.receipt.get("cargo_machine_ids", []),
            "cargo_role_counts": self.receipt.get("cargo_role_counts", {}),
            "cargo_motion_range_count": self.receipt.get("cargo_motion_range_count"),
            "machine_beacon_bindings_verified": self.receipt.get(
                "machine_beacon_bindings_verified", False),
            "checkpoint_count": len(self.checkpoints),
            "checkpoints": self.checkpoints,
            "press_inspection_quality_gate_expected": (
                self.profile.expects_press_inspection_quality_gate),
            "press_inspection_quality_gate_present": quality_present,
            "quality_gate_behavior_proved": quality_proved,
            "quality_gate_evidence": self.quality_gate_evidence,
            "known_quality_gate_gap": quality_gap,
            "palletising_and_outbound_after_quality_release_proved": bool(
                self.receipt.get(
                    "palletising_and_outbound_after_quality_release_proved",
                    False)),
            "exact_map_pie_visual_lifecycle_validated": final_status.startswith("PASS_"),
            "exact_map_pie_quality_lifecycle_validated": (
                final_status.startswith("PASS_") and quality_proved),
            "packaged_build_validated": False,
            "performance_validated": False,
            "steam_capture_validated": False,
            "human_visual_quality_approved": False,
            "transient_pie_runtime_authority_exercised": bool(
                self.receipt.get("transient_pie_runtime_authority_exercised", False)),
            "project_content_mutated": False,
            "save_or_package_api_called": False,
            "source_receipt": str(self.profile.source_receipt),
            "source_receipt_sha256": self.profile.expected_receipt_sha256,
            "fingerprints_before": self.before,
            "fingerprints_after": after,
            "fingerprints_unchanged": unchanged,
            "dirty_packages_before_load": self.dirty_before_load,
            "dirty_packages_before_pie": self.dirty_before_pie,
            "dirty_packages_after_pie": dirty_after,
            "dirty_package_set_unchanged_during_pie": dirty_unchanged,
            "runtime_seconds": round(time.monotonic() - self.started_at, 3),
        }
        self.profile.output_receipt.parent.mkdir(parents=True, exist_ok=True)
        self.profile.output_receipt.write_bytes(canonical_json_bytes(output))
        if self.handle is not None:
            try:
                unreal.unregister_slate_post_tick_callback(self.handle)
            except Exception:
                pass
            self.handle = None
        unreal.EditorPythonScripting.set_keep_python_script_alive(False)
        unreal.SystemLibrary.quit_editor()

    def run_exact_proof(self, world: Any) -> None:
        if not world_is_exact_target(world, self.profile.target_map):
            fail("PIE started a different world: " + _world_package_name(world))
        self.receipt["target_map_started_exactly"] = True
        self.receipt["game_world_identity"] = _world_package_name(world)
        game_mode = unreal.GameplayStatics.get_game_mode(world)
        if game_mode is None:
            fail("PIE has no authoritative game mode")
        game_mode_class = str(game_mode.get_class().get_path_name())
        self.receipt["game_mode_class"] = game_mode_class
        if game_mode_class != GAME_MODE_CLASS:
            fail("wrong game mode in exact candidate PIE: " + game_mode_class)

        activation = capture_native_player_activation(world)
        self.receipt["native_player_activation_snapshot_before_proof"] = activation
        self.receipt["player_controller_count"] = activation[
            "actor_counts"]["player_controller"]
        self.receipt["player_controller_class"] = activation[
            "player_controller_class"]
        self.receipt["runtime_authority_counts"] = activation["actor_counts"]
        self.native_player_activation_verified = True

        coordinators = _actors(world, COORDINATOR_CLASS)
        presentations = _actors(world, PRESENTATION_CLASS)
        layers = _actors(world, VISUAL_LAYER_CLASS)
        self.receipt["runtime_coordinator_count"] = len(coordinators)
        self.receipt["presentation_adapter_count"] = len(presentations)
        if len(coordinators) != 1:
            fail("expected exactly one native runtime coordinator")
        if len(presentations) != EXPECTED_PRESENTATION_COUNT:
            fail("expected exactly one native overhead presentation adapter")
        if len(layers) != EXPECTED_VISUAL_LAYER_COUNT:
            fail("exact candidate has {} visual layers, expected {}".format(
                len(layers), EXPECTED_VISUAL_LAYER_COUNT))
        coordinator = coordinators[0]
        presentation = presentations[0]
        if bool(presentation.owns_production_state()):
            fail("presentation adapter unexpectedly claims production authority")
        if not bool(presentation.is_presentation_enabled()):
            fail("presentation adapter is disabled")
        if not self.runtime_drivers_frozen:
            fail("runtime drivers were not frozen on the first exact-map PIE frame")
        readback = freeze_runtime_drivers(coordinator)
        if any(readback.values()):
            fail("runtime drivers resumed before the exact proof")
        self.receipt["runtime_driver_readback"] = readback

        route, topology = parse_payload_reason(
            coordinator.get_configured_station_route(), 2,
            "GetConfiguredStationRoute",
        )
        station_ids = [normalise_name(_read_prop(step, "station_id")) for step in route]
        self.receipt["configured_route_count"] = len(station_ids)
        self.receipt["configured_route_prefix"] = station_ids[:7]
        if tuple(station_ids[:7]) != tuple(normalise_name(v) for v in EXPECTED_STATION_ROUTE_PREFIX):
            fail("configured press route prefix differs from the canonical route")
        route_contract = validate_route_profile_contract(
            self.profile, route, topology)
        self.receipt["runtime_route_profile_validated"] = True
        self.receipt["runtime_topology_id"] = route_contract["topology_id"]
        self.receipt["inspection_route_step"] = route_contract[
            "inspection_step"]
        # Validate the complete composite only after recording the independent
        # route preflight.  If Unreal Python reports native false as None, the
        # failed receipt can now distinguish route construction from the full
        # ledger/reservation audit without accepting either as success.
        self.receipt["runtime_validation_reason"] = parse_bool_reason(
            coordinator.validate_runtime_factory(), "ValidateRuntimeFactory")

        _refresh(presentation)
        bound_count = int(presentation.get_bound_visual_layer_count())
        self.receipt["bound_visual_layer_count"] = bound_count
        if bound_count != EXPECTED_VISUAL_LAYER_COUNT:
            fail("presentation did not bind all 146 visual layers")
        if int(presentation.get_status_beacon_count()) != EXPECTED_BEACON_COUNT:
            fail("presentation status beacon registry is incomplete")
        if int(presentation.get_task_light_count()) != EXPECTED_TASK_LIGHT_COUNT:
            fail("presentation task-light registry is incomplete")

        layers_by_id: Dict[str, Any] = {}
        for layer in layers:
            meta = _layer_metadata(layer)
            if meta["layer_id"] in layers_by_id:
                fail("duplicate visual LayerId in PIE: " + meta["layer_id"])
            layers_by_id[meta["layer_id"]] = layer
        cargo_ids = {normalise_name(row[0]) for row in CARGO_CONTRACT}
        cargo_layers = {key: layers_by_id.get(key) for key in cargo_ids}
        if any(value is None for value in cargo_layers.values()):
            fail("not all cargo layers were discovered in exact-map PIE")
        for expected in CARGO_CONTRACT:
            layer_id, machine, role, state, channel, has_motion = expected
            actor = cargo_layers[normalise_name(layer_id)]
            meta = _layer_metadata(actor)
            actual = (meta["machine_id"], meta["role"], meta["state"],
                      meta["motion_channel"], meta["has_motion_range"])
            wanted = (normalise_name(machine), normalise_name(role),
                      normalise_name(state), normalise_name(channel), has_motion)
            if actual != wanted:
                fail("PIE cargo metadata mismatch for " + layer_id)
            if not _collision_disabled(actor):
                fail("presentation-only cargo has collision enabled: " + layer_id)
        self.receipt["cargo_layer_count"] = len(cargo_layers)
        self.receipt["cargo_actor_contract_verified"] = True
        machine_ids = sorted({normalise_name(row[1]) for row in CARGO_CONTRACT})
        if len(machine_ids) != EXPECTED_BEACON_COUNT:
            fail("cargo contract does not cover all 14 overhead machine roles")
        for machine_id in machine_ids:
            if presentation.get_status_beacon(unreal.Name(machine_id)) is None:
                fail("presentation beacon/control binding is missing: " + machine_id)
        role_counts: Dict[str, int] = {}
        for row in CARGO_CONTRACT:
            role = normalise_name(row[2])
            role_counts[role] = role_counts.get(role, 0) + 1
        self.receipt["cargo_machine_ids"] = machine_ids
        self.receipt["cargo_role_counts"] = role_counts
        self.receipt["cargo_motion_range_count"] = sum(
            1 for row in CARGO_CONTRACT if row[5])
        self.receipt["machine_beacon_bindings_verified"] = True

        unit_id = parse_payload_reason(
            coordinator.dispatch_next_open_contract(), 1,
            "DispatchNextOpenContract",
        )[0]
        if normalise_name(unit_id) == "NONE":
            fail("no canonical evidence unit was available for dispatch")
        self.receipt["transient_pie_runtime_authority_exercised"] = True

        current_station: Optional[str] = None
        for checkpoint in CHECKPOINTS:
            if current_station is None:
                current_station = _status_snapshot(_status(coordinator, unit_id))["station_id"]
            while current_station != normalise_name(checkpoint.station_id):
                before_station = current_station
                if (self.profile.expects_press_inspection_quality_gate
                        and before_station == normalise_name(
                            EXPECTED_STATION_ROUTE_PREFIX[5])):
                    inspection_sample = next(
                        (row for row in self.checkpoints
                         if row["checkpoint_id"] == "S07_INSPECTION_SCAN"),
                        None)
                    if inspection_sample is None:
                        fail("quality hold reached before the inspection visual checkpoint")
                    if self.quality_gate_evidence is not None:
                        fail("Press inspection quality gate was exercised more than once")
                    self.quality_gate_evidence = (
                        _exercise_press_inspection_quality_gate(
                            self.profile, coordinator, unit_id, presentation,
                            layers_by_id, inspection_sample["status"]))
                    after = self.quality_gate_evidence[
                        "released_to_panel_dispatch"]
                else:
                    after = _advance_station(
                        coordinator, unit_id, before_station)
                current_station = after["station_id"]
                if current_station not in station_ids[:7]:
                    fail("evidence unit left the press route before checkpoints completed")
            sample = _sample_checkpoint(
                checkpoint, coordinator, unit_id, presentation,
                layers_by_id, layers,
            )
            self.checkpoints.append(sample)

        inspection = next(row for row in self.checkpoints
                          if row["checkpoint_id"] == "S07_INSPECTION_SCAN")
        if self.profile.expects_press_inspection_quality_gate:
            if (not inspection["status"]["at_quality_gate"]
                    or inspection["status"]["awaiting_quality_result"]):
                fail("V002 inspection did not report its active pre-completion quality gate")
            if self.quality_gate_evidence is None:
                fail("V002 inspection hold/pass/release evidence was not produced")
            completed_ids = {row["checkpoint_id"] for row in self.checkpoints}
            downstream_ids = {
                "S07_PALLETISER_PLACE",
                "OUTBOUND_PANEL_STILLAGE_TRANSFER",
            }
            if not downstream_ids.issubset(completed_ids):
                fail("palletising/outbound checkpoints did not follow quality release")
            self.receipt["press_inspection_quality_gate_present"] = True
            self.receipt["quality_gate_behavior_proved"] = True
            self.receipt[
                "palletising_and_outbound_after_quality_release_proved"] = True
        else:
            if (inspection["status"]["at_quality_gate"]
                    or inspection["status"]["awaiting_quality_result"]):
                fail("v003 legacy inspection unexpectedly reported a quality gate")
            self.receipt["press_inspection_quality_gate_present"] = False
            self.receipt["quality_gate_behavior_proved"] = False
            self.receipt[
                "palletising_and_outbound_after_quality_release_proved"] = False
        self.finish(self.profile.pass_status)

    def tick(self, _delta_seconds: float) -> None:
        if self.finished:
            return
        try:
            now = time.monotonic()
            world = self.editor_worlds.get_game_world()
            if world is None:
                if now - self.started_at > GAME_WORLD_TIMEOUT_SECONDS:
                    self.finish("FAIL_PIE_WORLD_TIMEOUT")
                return
            if self.game_world_seen_at is None:
                self.game_world_seen_at = now
            if self.pie_started_at is None:
                if not world_is_exact_target(world, self.profile.target_map):
                    fail("PIE started a different world: " + _world_package_name(world))
                counts = runtime_activation_counts(world)
                self.receipt["runtime_authority_counts"] = counts
                self.receipt["player_controller_count"] = counts[
                    "player_controller"]
                self.receipt["runtime_coordinator_count"] = counts[
                    "runtime_coordinator"]
                if not activation_counts_ready(counts):
                    if now - self.game_world_seen_at > PLAYER_ACTIVATION_TIMEOUT_SECONDS:
                        self.finish(
                            "FAIL_NATIVE_PLAYER_ACTIVATION_TIMEOUT",
                            "regular PIE did not reach the exact 1 controller + "
                            "4 layouts + 1 production + 1 coordinator contract; "
                            "last counts={!r}".format(counts),
                        )
                    return
                activation = capture_native_player_activation(world)
                self.activation_snapshot = activation
                self.receipt["native_player_activation_snapshot"] = activation
                self.receipt["player_controller_class"] = activation[
                    "player_controller_class"]
                self.native_player_activation_verified = True
                coordinators = _actors(world, COORDINATOR_CLASS)
                readback = freeze_runtime_drivers(coordinators[0])
                if any(readback.values()):
                    fail("could not freeze runtime drivers at PIE entry")
                self.runtime_drivers_frozen = True
                self.receipt["runtime_drivers_frozen_before_proof"] = True
                self.receipt["runtime_driver_readback"] = readback
                self.pie_started_at = now
                return
            if not self.proof_started and now - self.pie_started_at >= 1.0:
                self.proof_started = True
                self.run_exact_proof(world)
            elif now - self.started_at > RUN_TIMEOUT_SECONDS:
                self.finish("FAIL_EXACT_MAP_PIE_TIMEOUT")
        except Exception as exc:
            self.finish("FAIL_EXACT_MAP_PIE_EXCEPTION", repr(exc))


def main() -> None:
    if unreal is None:
        fail("this verifier must run inside Unreal Editor Python")
    profile = resolve_profile()
    if profile.output_receipt.exists():
        fail("refusing to overwrite exact-map PIE evidence: {}".format(
            profile.output_receipt))
    source_receipt = load_and_validate_source_receipt(profile)
    protected_before = verify_protected_files()
    for tracked in tracked_evidence_paths(profile):
        protected_before[str(tracked)] = file_fingerprint(tracked)
    dirty_before_load = _dirty_packages()
    if not unreal.EditorLoadingAndSavingUtils.load_map(profile.target_map):
        fail("could not load exact candidate map: " + profile.target_map)
    editor_world = unreal.get_editor_subsystem(
        unreal.UnrealEditorSubsystem).get_editor_world()
    if editor_world is None or not world_is_exact_target(editor_world, profile.target_map):
        fail("editor did not load the exact requested candidate map")
    verifier = PieVerifier(profile, source_receipt, protected_before, dirty_before_load)
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    verifier.handle = unreal.register_slate_post_tick_callback(verifier.tick)
    # EditorRequestBeginPlay requests EPlaySessionWorldType::PlayInEditor.
    # Unlike EditorPlaySimulate, this creates the configured native player
    # controller and therefore exercises the real production startup seam.
    verifier.level_editor.editor_request_begin_play()


if __name__ == "__main__":
    main()
