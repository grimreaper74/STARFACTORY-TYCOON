"""Install the candidate-only Press Shop 2126 overhead deck presentation.

This is a guarded, one-shot presentation lane.  It clones the hash-locked
``OverheadPlayable_v001`` integration map to a new candidate package and edits
only that clone.  The source map, the protected builder-authority map and all
other evidence maps are snapshotted before and after the run.

The clone retains the 120 registered overhead sprite-layer actors, the native
presentation adapter, the OneFactory bootstrap/build authority and map-authored
navigation/player datums.  It removes only presentation actors already marked
``LB.Environment.VisualOnly`` + ``LB.NotProcessWIP``, the inherited OneFactory
HISM shell, the superseded management camera, and two exact legacy presentation
classes.  It then creates a roofless dark deck, pale-green station pads,
cream/yellow material-flow markings, native TextRender labels, and three exact
true-overhead orthographic cameras.

The script does not run itself when imported, does not modify C++ or Config,
does not import source art, and never overwrites an existing target.  A fresh
visual capture and runtime/package validation remain separate gates.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")

SOURCE_MAP = (
    "/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPlayable_v001/"
    "Maps/LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001"
)
TARGET_ROOT = (
    "/Game/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v002"
)
TARGET_MAP = (
    TARGET_ROOT
    + "/Maps/LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v002"
)
MATERIAL_ROOT = TARGET_ROOT + "/Materials"

SOURCE_FILE = (
    PROJECT
    / "Content"
    / "LineBoss"
    / "Candidates"
    / "PressShop"
    / "PressShop2126_OverheadPlayable_v001"
    / "Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001.umap"
)
TARGET_ROOT_DISK = (
    PROJECT
    / "Content"
    / "LineBoss"
    / "Candidates"
    / "PressShop"
    / "PressShop2126_OverheadPresentation_v002"
)
TARGET_FILE = (
    TARGET_ROOT_DISK
    / "Maps"
    / "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v002.umap"
)
SOURCE_FILE_SHA256 = (
    "43020cb3ea7d18a49319da68a04ae1b96d5af0d535c705e947f81d5c005ba7ce"
)

SOURCE_RECEIPT = (
    PROJECT
    / "Saved"
    / "Audits"
    / "PressShop2126"
    / "OverheadPlayable_v001"
    / "build_receipt_v002.json"
)
SOURCE_RECEIPT_SHA256 = (
    "91c2e7ef4dd6e5bc2ce289e2c149ff4abeb1258f78af43ec6d6f5e68f18e2a6f"
)
SOURCE_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.overhead_playable_map_build_receipt.v002"
)
SOURCE_RECEIPT_STATUS = "PASS_CANDIDATE_MAP_INTEGRATION__NOT_RUNTIME_READY"

RECEIPT = (
    PROJECT
    / "Saved"
    / "Audits"
    / "PressShop2126"
    / "OverheadPresentation_v002"
    / "install_receipt_v001.json"
)
RECEIPT_SCHEMA = (
    "cairnwell.press_shop.overhead_deck_presentation_install_receipt.v001"
)
RECOVERY_RECEIPT = (
    PROJECT
    / "Saved"
    / "Audits"
    / "PressShop2126"
    / "OverheadPresentation_v002"
    / "failed_run_recovery_receipt_v001.json"
)
RECOVERY_RECEIPT_SCHEMA = (
    "cairnwell.press_shop.overhead_deck_presentation_failed_run_recovery.v001"
)
RECOVERY_RECEIPT_SHA256_AFTER_FIRST_RECOVERY = (
    "3736b43e99e4dd59c0a0e6e1f2526d1bfa0c3684f30aa88180c71afcb30dc630"
)
RECOVERY_RECEIPT_V002 = (
    PROJECT
    / "Saved"
    / "Audits"
    / "PressShop2126"
    / "OverheadPresentation_v002"
    / "failed_run_recovery_receipt_v002.json"
)
RECOVERY_RECEIPT_SCHEMA_V002 = (
    "cairnwell.press_shop.overhead_deck_presentation_failed_run_recovery.v002"
)
RECOVERY_RECEIPT_SHA256_AFTER_SECOND_RECOVERY = (
    "9e9712b997cbe1719085a4a11e64348d5428d401736e54f6af2337cec3a4ff0e"
)
RECOVERY_RECEIPT_V003 = (
    PROJECT
    / "Saved"
    / "Audits"
    / "PressShop2126"
    / "OverheadPresentation_v002"
    / "failed_run_recovery_receipt_v003.json"
)
RECOVERY_RECEIPT_SCHEMA_V003 = (
    "cairnwell.press_shop.overhead_deck_presentation_failed_run_recovery.v003"
)
FAILED_RUN_LOG = (
    PROJECT
    / "Saved"
    / "Logs"
    / "PressShop2126_OverheadPresentation_v002_install_v001_absolute.log"
)
FAILED_RUN_LOG_SHA256 = (
    "0f5ad8d93d0a983a1395a3c95e16acc65d1fdb00606fb937c1433f9037b47032"
)
FAILED_RUN_ERROR = "presentation cube retained collision: DECK_BASE"
SECOND_FAILED_RUN_LOG = (
    PROJECT
    / "Saved"
    / "Logs"
    / "PressShop2126_OverheadPresentation_v002_install_v001_guarded_recovery_retry.log"
)
SECOND_FAILED_RUN_LOG_SHA256 = (
    "9593e0f982400fdca5e1eecbbac366fac1c783e708c486211c1dde0936013444"
)
SECOND_FAILED_RUN_ERROR = (
    "presentation component profile is not NoCollision: DECK_BASE"
)
THIRD_FAILED_RUN_LOG = (
    PROJECT
    / "Saved"
    / "Logs"
    / "PressShop2126_OverheadPresentation_v002_install_v001_guarded_recovery_profile_last.log"
)
THIRD_FAILED_RUN_LOG_SHA256 = (
    "5297813221b743beb8d863efa5f25838ad6560dd9e2a64b88f3b28517c42ac38"
)
THIRD_FAILED_RUN_ERROR = (
    "presentation component does not ignore ECC_WORLD_STATIC: DECK_BASE"
)

PROTECTED_MAPS = {
    PROJECT
    / "Content"
    / "LineBoss"
    / "Maps"
    / "LB_PressShop_BuilderAuthorityCandidate_v438.umap":
        "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT
    / "Content"
    / "LineBoss"
    / "Factory"
    / "OneFactory"
    / "v001"
    / "Maps"
    / "LB_MoorcrossWorks_OneFactory_v001.umap":
        "f4e97b33cdfb1f242b2c606a16b4caa05b74b298fdf1b1263d4a4c46d50e8d5c",
    SOURCE_FILE: SOURCE_FILE_SHA256,
    PROJECT
    / "Content"
    / "LineBoss"
    / "Candidates"
    / "PressShop"
    / "PressShop2126_v002"
    / "Maps"
    / "LB_PressShop_2126_Steam_v002.umap":
        "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
    PROJECT
    / "Content"
    / "LineBoss"
    / "Candidates"
    / "PressShop"
    / "PressShopFactorio2p5D_IndividualSprites_v007"
    / "Maps"
    / "LB_PressShop_Factorio2p5D_IndividualSprites_v007.umap":
        "0e1bc9ddbf753a790955375eba8d0b274eb7d48cb336a84a82df431f85aa9624",
    PROJECT
    / "Content"
    / "LineBoss"
    / "Candidates"
    / "PressShop"
    / "PressShop2126_FullHall_v001"
    / "Maps"
    / "LB_PressShop_2126_FullHall_v001.umap":
        "37fc7af541675f4f38afd816d7d4552628d1deaf22b0abe01d6830907a62349f",
}

EXPECTED_GAME_MODE = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
VISUAL_LAYER_CLASS_PATH = (
    "/Script/LineBossCarFactory.LBPressShopOverheadVisualLayerActor"
)
PRESENTATION_CLASS_PATH = (
    "/Script/LineBossCarFactory.LBPressShopOverheadPresentationActor"
)
VISUAL_LAYER_TAG = "LB.PressShop.Overhead.VisualLayer.v001"
PRESENTATION_TAG = "LB.PressShop.OverheadPresentation.v001"
SOURCE_CAMERA_TAG = "LB.PressShop.Overhead.Camera.v001"

PASS_TAG = "LB.PressShop.OverheadDeckPresentation.v002"
VISUAL_ONLY_TAG = "LB.Environment.VisualOnly"
NOT_WIP_TAG = "LB.NotProcessWIP"
ROOFLESS_TAG = "LB.PressShop.RooflessPresentation.v002"
CAMERA_TAG = "LB.PressShop.OverheadDeck.Camera.v002"

BOOTSTRAP_TAG = "LB.OneFactory.Bootstrap.v001"
BUILD_AUTHORITY_TAG = "LB.OneFactory.MapAuthored.PressBuildAuthority.v001"
PLAYER_START_TAG = "LB.OneFactory.PlayerStart.Management.v001"
HISM_SHELL_TAG = "LB.OneFactory.Environment.HISM"
LEGACY_MANAGEMENT_CAMERA_TAG = "LB.OneFactory.ManagementView.Overview.v001"

LEGACY_PRESENTATION_CLASS_PATHS = frozenset({
    "/Script/LineBossCarFactory.LBOneFactoryScanBeamActor",
    "/Script/LineBossCarFactory.LBPressTrainSignageActor",
})
PROTECTED_NATIVE_CLASS_TOKENS = (
    "LBOneFactoryBootstrap",
    "LBPressShopBuildAuthority",
)

EXPECTED_SOURCE_PRE_EXISTING_ACTORS = 13702
EXPECTED_SOURCE_VISUAL_LAYERS = 120
EXPECTED_SOURCE_PRESENTATION_ADAPTERS = 1
EXPECTED_SOURCE_CAMERAS = 2
EXPECTED_SOURCE_ACTORS = (
    EXPECTED_SOURCE_PRE_EXISTING_ACTORS
    + EXPECTED_SOURCE_VISUAL_LAYERS
    + EXPECTED_SOURCE_PRESENTATION_ADAPTERS
    + EXPECTED_SOURCE_CAMERAS
)
EXPECTED_SOURCE_LEGACY_REMOVALS = 13689
EXPECTED_RETAINED_INFRASTRUCTURE_ACTORS = 15

CUBE_ASSET = "/Engine/BasicShapes/Cube.Cube"
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

MATERIAL_SPECS: Tuple[Mapping[str, Any], ...] = (
    {
        "id": "deck",
        "name": "M_CA_MW_PS2126_DeckCharcoal_Unlit_v001",
        "srgb_hex": "#171D21",
    },
    {
        "id": "zone",
        "name": "M_CA_MW_PS2126_ZonePaleGreen_Unlit_v001",
        "srgb_hex": "#91AA9C",
    },
    {
        "id": "cream",
        "name": "M_CA_MW_PS2126_FlowCream_Unlit_v001",
        "srgb_hex": "#E8DEC2",
    },
    {
        "id": "yellow",
        "name": "M_CA_MW_PS2126_SafetyYellow_Unlit_v001",
        "srgb_hex": "#E1B94F",
    },
)

# Complete persisted inventory from the first fail-closed run.  The map was
# saved by ``new_level_from_template`` before actor mutation; the four material
# packages were saved before the DECK_BASE collision readback stopped the run.
# No presentation actor mutation or install receipt was saved.  Recovery is
# legal only when disk and asset-registry inventories match these five packages.
FAILED_RUN_ARTIFACTS: Tuple[Mapping[str, Any], ...] = (
    {
        "asset": TARGET_MAP,
        "disk": TARGET_FILE,
        "sha256": "1876faa9e0e5f298b5202733ccaf3769f8c909a60d56e18bbea4e2fa65c30f6e",
        "bytes": 33968363,
    },
    {
        "asset": MATERIAL_ROOT + "/M_CA_MW_PS2126_DeckCharcoal_Unlit_v001",
        "disk": TARGET_ROOT_DISK / "Materials" / "M_CA_MW_PS2126_DeckCharcoal_Unlit_v001.uasset",
        "sha256": "e35bf6a49277d53708c7f9d599c18cc5e6fbcb30fe6f314eb841280d4110540c",
        "bytes": 5354,
    },
    {
        "asset": MATERIAL_ROOT + "/M_CA_MW_PS2126_FlowCream_Unlit_v001",
        "disk": TARGET_ROOT_DISK / "Materials" / "M_CA_MW_PS2126_FlowCream_Unlit_v001.uasset",
        "sha256": "416182e7cd72b2998c13c5d95b4da85543397eefe04d2e5d3bde5b51a9a021f9",
        "bytes": 5336,
    },
    {
        "asset": MATERIAL_ROOT + "/M_CA_MW_PS2126_SafetyYellow_Unlit_v001",
        "disk": TARGET_ROOT_DISK / "Materials" / "M_CA_MW_PS2126_SafetyYellow_Unlit_v001.uasset",
        "sha256": "26e459e706f7b1f698f92f5248408533a1966f62af7cdd003f853844333389a7",
        "bytes": 5354,
    },
    {
        "asset": MATERIAL_ROOT + "/M_CA_MW_PS2126_ZonePaleGreen_Unlit_v001",
        "disk": TARGET_ROOT_DISK / "Materials" / "M_CA_MW_PS2126_ZonePaleGreen_Unlit_v001.uasset",
        "sha256": "fde7fe0bf42bba4d384191d90bf3102d87507a561314ae0fc7c6826a32b90e2b",
        "bytes": 5360,
    },
)

# After the exact v001 cleanup, a second fail-closed run recreated the same five
# candidate packages and stopped before saving map actor mutations because the
# strict profile readback observed ``Custom``.  These new package hashes and the
# second failure log form a separate recovery lane; the v001 recovery receipt is
# hash-locked and preserved as prerequisite evidence.
SECOND_FAILED_RUN_ARTIFACTS: Tuple[Mapping[str, Any], ...] = (
    {
        "asset": TARGET_MAP,
        "disk": TARGET_FILE,
        "sha256": "c4982debb56e031d3640de16cd521587e8342bece20b86dc74ffcc5c0fac4e4e",
        "bytes": 33968363,
    },
    {
        "asset": MATERIAL_ROOT + "/M_CA_MW_PS2126_DeckCharcoal_Unlit_v001",
        "disk": TARGET_ROOT_DISK / "Materials" / "M_CA_MW_PS2126_DeckCharcoal_Unlit_v001.uasset",
        "sha256": "dc509c1ea6aaaed92ba5fb9f34c8dbea4cc057dde1287003ea212a8186bb75fc",
        "bytes": 5354,
    },
    {
        "asset": MATERIAL_ROOT + "/M_CA_MW_PS2126_FlowCream_Unlit_v001",
        "disk": TARGET_ROOT_DISK / "Materials" / "M_CA_MW_PS2126_FlowCream_Unlit_v001.uasset",
        "sha256": "26e6951c5a6aa4dc86befae8a89059eff006613dfa077a4441c7b9c58b1d3dba",
        "bytes": 5336,
    },
    {
        "asset": MATERIAL_ROOT + "/M_CA_MW_PS2126_SafetyYellow_Unlit_v001",
        "disk": TARGET_ROOT_DISK / "Materials" / "M_CA_MW_PS2126_SafetyYellow_Unlit_v001.uasset",
        "sha256": "e1dbf34db9140749963b4c7dbc07e7db3a7756263c9457ccc4ee479ac02f68a5",
        "bytes": 5354,
    },
    {
        "asset": MATERIAL_ROOT + "/M_CA_MW_PS2126_ZonePaleGreen_Unlit_v001",
        "disk": TARGET_ROOT_DISK / "Materials" / "M_CA_MW_PS2126_ZonePaleGreen_Unlit_v001.uasset",
        "sha256": "d5027cfaa60ffb1c80e1cac2c2ed214c338c5c510b58ec2e31e3659b0d7201df",
        "bytes": 5360,
    },
)

# Profile-last preserved the native profile name but the project-defined
# NoCollision profile restored a blocking response container.  That run again
# stopped before map mutation save and persisted only this fresh clone plus four
# materials.  Its cleanup is independently gated by these hashes, its failure
# log, and both prior immutable recovery receipts.
THIRD_FAILED_RUN_ARTIFACTS: Tuple[Mapping[str, Any], ...] = (
    {
        "asset": TARGET_MAP,
        "disk": TARGET_FILE,
        "sha256": "c51c95a2ffcd590a82b5bb961b9753c9ddb50a2302b6982d1796d4e57de93a32",
        "bytes": 33968363,
    },
    {
        "asset": MATERIAL_ROOT + "/M_CA_MW_PS2126_DeckCharcoal_Unlit_v001",
        "disk": TARGET_ROOT_DISK / "Materials" / "M_CA_MW_PS2126_DeckCharcoal_Unlit_v001.uasset",
        "sha256": "c03dc133736ec338f7ff632055cd727aa68862d3a3d54f17c78dae0ea698644d",
        "bytes": 5354,
    },
    {
        "asset": MATERIAL_ROOT + "/M_CA_MW_PS2126_FlowCream_Unlit_v001",
        "disk": TARGET_ROOT_DISK / "Materials" / "M_CA_MW_PS2126_FlowCream_Unlit_v001.uasset",
        "sha256": "c561fa2c6f3c878cee22526e18b4b01a6b9dbe122a00de5ca4197e4a67d95e82",
        "bytes": 5336,
    },
    {
        "asset": MATERIAL_ROOT + "/M_CA_MW_PS2126_SafetyYellow_Unlit_v001",
        "disk": TARGET_ROOT_DISK / "Materials" / "M_CA_MW_PS2126_SafetyYellow_Unlit_v001.uasset",
        "sha256": "ee3ecff0a7befb6c4ce2c4472dfede583917b439b860d353feab4aca43e1f622",
        "bytes": 5354,
    },
    {
        "asset": MATERIAL_ROOT + "/M_CA_MW_PS2126_ZonePaleGreen_Unlit_v001",
        "disk": TARGET_ROOT_DISK / "Materials" / "M_CA_MW_PS2126_ZonePaleGreen_Unlit_v001.uasset",
        "sha256": "9874b5dbfe38952afd89de26e4684864f713d18802b7c51ca6f32cca61015c81",
        "bytes": 5360,
    },
)

DECK_CENTER_XY = (-7730.645880159617, 8840.218280826943)
DECK_SIZE_XY = (6700.0, 16100.0)
DECK_MIN_XY = (
    DECK_CENTER_XY[0] - DECK_SIZE_XY[0] / 2.0,
    DECK_CENTER_XY[1] - DECK_SIZE_XY[1] / 2.0,
)
DECK_MAX_XY = (
    DECK_CENTER_XY[0] + DECK_SIZE_XY[0] / 2.0,
    DECK_CENTER_XY[1] + DECK_SIZE_XY[1] / 2.0,
)
PROCESS_PAD_X = -8990.75
PROCESS_PAD_WIDTH_X = 2300.0
STATION_LABEL_X = -10095.0
FLOW_LANE_X = -6500.0
FLOW_LANE_WIDTH_X = 950.0
FLOW_LANE_CENTER_Y = DECK_CENTER_XY[1]
FLOW_LANE_LENGTH_Y = 15500.0
PRESENTATION_TOP_Z = -0.1

STATION_PADS: Tuple[Mapping[str, Any], ...] = (
    {"id": "IN01", "text": "IN01\nRECEIVE", "center_y": 1600.0, "length_y": 1300.0},
    {"id": "IN02", "text": "IN02\nAGV", "center_y": 3260.0, "length_y": 1100.0},
    {"id": "IN03", "text": "IN03\nSTORE", "center_y": 4260.0, "length_y": 650.0},
    {"id": "IN04_05", "text": "IN04-05\nCOIL PREP", "center_y": 5200.0, "length_y": 1050.0},
    {"id": "S01", "text": "S01\nDESTACK", "center_y": 6350.0, "length_y": 1100.0},
    {"id": "S02", "text": "S02\nDRAW", "center_y": 7500.0, "length_y": 1000.0},
    {"id": "S03", "text": "S03\nFORM", "center_y": 8950.0, "length_y": 1050.0},
    {"id": "S04", "text": "S04\nTRIM", "center_y": 10400.0, "length_y": 1050.0},
    {"id": "S05", "text": "S05\nPIERCE", "center_y": 11850.0, "length_y": 1050.0},
    {"id": "S06", "text": "S06\nFLANGE", "center_y": 13300.0, "length_y": 1050.0},
    {"id": "S07_INSPECT", "text": "S07-A\nINSPECT", "center_y": 14700.0, "length_y": 900.0},
    {"id": "S07_PALLET", "text": "S07-B\nPALLET", "center_y": 15900.0, "length_y": 1100.0},
)

FLOW_ARROW_Y = (2200.0, 4200.0, 6200.0, 8200.0, 10200.0, 12200.0, 14200.0, 16000.0)
FLOW_CONNECTOR_Y = (2200.0, 5200.0, 7500.0, 10400.0, 14700.0, 15900.0)

CAMERA_Z_CM = 21712.544
CAMERA_ASPECT = 16.0 / 9.0
CAMERA_ROTATION = (-90.0, 0.0, 0.0)
CAMERA_MIN_MARGIN_CM = 150.0
CAMERA_SPECS: Tuple[Mapping[str, Any], ...] = (
    {
        "id": "overview",
        "label": "CAM | Press Shop 2126 | roofless deck overview v002",
        "center_xy_cm": DECK_CENTER_XY,
        "ortho_width_cm": 16500.0,
        "bounds_min_xy_cm": DECK_MIN_XY,
        "bounds_max_xy_cm": DECK_MAX_XY,
        "role_tag": "LB.PressShop.OverheadDeck.Camera.Overview.v002",
    },
    {
        "id": "press_spine",
        "label": "CAM | Press Shop 2126 | roofless production spine v002",
        "center_xy_cm": (-8090.0, 10450.0),
        "ortho_width_cm": 8900.0,
        "bounds_min_xy_cm": (-10280.0, 6200.0),
        "bounds_max_xy_cm": (-5900.0, 14700.0),
        "role_tag": "LB.PressShop.OverheadDeck.Camera.PressSpine.v002",
    },
    {
        "id": "steam_hero",
        "label": "CAM | Press Shop 2126 | S03-S06 native-scale Steam hero v002",
        "center_xy_cm": (-8990.75, 11200.0),
        "ortho_width_cm": 6900.0,
        "bounds_min_xy_cm": (-9800.0, 8050.0),
        "bounds_max_xy_cm": (-8180.0, 14000.0),
        "role_tag": "LB.PressShop.OverheadDeck.Camera.SteamHero.v002",
        "additional_tags": (
            "LB.SteamReviewCamera",
            "LB.PressShop.SteamHero.v002",
        ),
    },
)

ROOF_TOKENS = ("roof", "ceiling", "canopy")
NUMERIC_TOLERANCE = 0.001


class PresentationGuardError(RuntimeError):
    """Fail-closed error for this one-shot candidate lane."""


def fail(message: str) -> None:
    raise PresentationGuardError(
        "PRESSSHOP_2126_OVERHEAD_DECK_PRESENTATION_V001_FAIL: " + message
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


def _require_mapping(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        fail(context + " must be a JSON object")
    return value


def _require_exact_bool(value: Any, expected: bool, context: str) -> None:
    if value is not expected:
        fail("{} must be {}".format(context, expected))


def load_and_validate_source_receipt() -> Mapping[str, Any]:
    if not SOURCE_RECEIPT.is_file():
        fail("source integration receipt is missing")
    if digest(SOURCE_RECEIPT) != SOURCE_RECEIPT_SHA256:
        fail("source integration receipt hash changed")
    try:
        value = json.loads(SOURCE_RECEIPT.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        fail("source integration receipt is unreadable: " + str(exc))
    receipt = _require_mapping(value, "source integration receipt")
    exact = {
        "schema": SOURCE_RECEIPT_SCHEMA,
        "status": SOURCE_RECEIPT_STATUS,
        "target_map": SOURCE_MAP,
        "target_map_sha256": SOURCE_FILE_SHA256,
        "native_visual_layer_class": VISUAL_LAYER_CLASS_PATH,
        "native_presentation_class": PRESENTATION_CLASS_PATH,
        "spawned_visual_layer_count": EXPECTED_SOURCE_VISUAL_LAYERS,
        "pre_existing_actor_count": EXPECTED_SOURCE_PRE_EXISTING_ACTORS,
    }
    for key, expected in exact.items():
        if receipt.get(key) != expected:
            fail("source receipt {} changed".format(key))
    _require_exact_bool(receipt.get("map_integrated"), True, "source map_integrated")
    _require_exact_bool(
        receipt.get("pre_existing_actor_fingerprints_unchanged"),
        True,
        "source pre-existing fingerprints unchanged",
    )
    _require_exact_bool(
        receipt.get("duplicate_gameplay_controllers_spawned"),
        False,
        "source duplicate controller claim",
    )
    for key in (
        "runtime_validated",
        "runtime_ready",
        "packaged_build_validated",
        "steam_capture_validated",
    ):
        _require_exact_bool(receipt.get(key), False, "source " + key)
    if receipt.get("game_mode_before") != EXPECTED_GAME_MODE:
        fail("source GameMode before integration changed")
    if receipt.get("game_mode_after") != EXPECTED_GAME_MODE:
        fail("source GameMode after integration changed")
    if receipt.get("protected_hashes_before") != receipt.get("protected_hashes_after"):
        fail("source receipt does not prove protected hashes stable")
    if receipt.get("dirty_packages_after_save") != {"content": [], "maps": []}:
        fail("source receipt does not finish with a clean package set")
    cameras = receipt.get("cameras")
    if not isinstance(cameras, list) or len(cameras) != EXPECTED_SOURCE_CAMERAS:
        fail("source camera count changed")
    for camera in cameras:
        row = _require_mapping(camera, "source camera")
        if row.get("projection") != "ORTHOGRAPHIC":
            fail("source camera is no longer orthographic")
        transform = _require_mapping(row.get("transform"), "source camera transform")
        rotation = transform.get("rotation_deg_pitch_yaw_roll")
        if rotation != list(CAMERA_ROTATION):
            fail("source camera is no longer exactly true-overhead")
    return receipt


def protected_snapshot() -> Dict[str, str]:
    result: Dict[str, str] = {}
    for path, expected in PROTECTED_MAPS.items():
        if not path.is_file():
            fail("protected map missing: " + path.as_posix())
        actual = digest(path)
        if actual != expected:
            fail("protected map hash changed: " + path.as_posix())
        result[path.as_posix()] = actual
    return result


def srgb_hex_to_linear(hex_code: str) -> Tuple[float, float, float]:
    if (
        not isinstance(hex_code, str)
        or len(hex_code) != 7
        or not hex_code.startswith("#")
    ):
        raise ValueError("expected #RRGGBB")

    def convert(value: int) -> float:
        channel = value / 255.0
        if channel <= 0.04045:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    return tuple(
        convert(int(hex_code[index:index + 2], 16))
        for index in (1, 3, 5)
    )


def _box(
    item_id: str,
    label: str,
    role: str,
    material_id: str,
    location: Sequence[float],
    dimensions: Sequence[float],
    yaw: float = 0.0,
) -> Dict[str, Any]:
    return {
        "id": item_id,
        "label": label,
        "role": role,
        "material_id": material_id,
        "location_cm": tuple(float(value) for value in location),
        "dimensions_cm": tuple(float(value) for value in dimensions),
        "yaw_deg": float(yaw),
    }


def build_box_specs() -> Tuple[Mapping[str, Any], ...]:
    specs: List[Mapping[str, Any]] = []
    deck_x, deck_y = DECK_CENTER_XY
    deck_w, deck_l = DECK_SIZE_XY
    min_x, min_y = DECK_MIN_XY
    max_x, max_y = DECK_MAX_XY

    specs.append(_box(
        "DECK_BASE",
        "2126 OVERHEAD DECK | dark industrial factory deck",
        "Deck",
        "deck",
        (deck_x, deck_y, -11.0),
        (deck_w, deck_l, 20.0),
    ))
    border_thickness = 24.0
    specs.extend((
        _box(
            "DECK_BORDER_WEST", "2126 OVERHEAD DECK | cream west border",
            "DeckBorder", "cream", (min_x + border_thickness / 2.0, deck_y, -0.35),
            (border_thickness, deck_l, 0.5),
        ),
        _box(
            "DECK_BORDER_EAST", "2126 OVERHEAD DECK | cream east border",
            "DeckBorder", "cream", (max_x - border_thickness / 2.0, deck_y, -0.35),
            (border_thickness, deck_l, 0.5),
        ),
        _box(
            "DECK_BORDER_SOUTH", "2126 OVERHEAD DECK | cream inbound border",
            "DeckBorder", "cream", (deck_x, min_y + border_thickness / 2.0, -0.35),
            (deck_w, border_thickness, 0.5),
        ),
        _box(
            "DECK_BORDER_NORTH", "2126 OVERHEAD DECK | cream outbound border",
            "DeckBorder", "cream", (deck_x, max_y - border_thickness / 2.0, -0.35),
            (deck_w, border_thickness, 0.5),
        ),
    ))

    for row in STATION_PADS:
        item_id = str(row["id"])
        center_y = float(row["center_y"])
        length_y = float(row["length_y"])
        specs.append(_box(
            "PAD_" + item_id,
            "2126 OVERHEAD PAD | {} | pale-green production zone".format(item_id),
            "StationPad",
            "zone",
            (PROCESS_PAD_X, center_y, -0.6),
            (PROCESS_PAD_WIDTH_X, length_y, 0.8),
        ))
        specs.append(_box(
            "PAD_KEY_" + item_id,
            "2126 OVERHEAD PAD | {} | yellow station key".format(item_id),
            "StationKey",
            "yellow",
            (
                PROCESS_PAD_X - PROCESS_PAD_WIDTH_X / 2.0 + 32.0,
                center_y,
                -0.3,
            ),
            (42.0, max(80.0, length_y - 100.0), 0.4),
        ))

    specs.append(_box(
        "FLOW_LANE",
        "2126 OVERHEAD FLOW | cream autonomous material lane",
        "FlowLane",
        "cream",
        (FLOW_LANE_X, FLOW_LANE_CENTER_Y, -0.45),
        (FLOW_LANE_WIDTH_X, FLOW_LANE_LENGTH_Y, 0.6),
    ))
    flow_min_x = FLOW_LANE_X - FLOW_LANE_WIDTH_X / 2.0
    flow_max_x = FLOW_LANE_X + FLOW_LANE_WIDTH_X / 2.0
    flow_min_y = FLOW_LANE_CENTER_Y - FLOW_LANE_LENGTH_Y / 2.0
    flow_max_y = FLOW_LANE_CENTER_Y + FLOW_LANE_LENGTH_Y / 2.0
    specs.extend((
        _box(
            "FLOW_EDGE_WEST", "2126 OVERHEAD FLOW | yellow west lane edge",
            "FlowEdge", "yellow", (flow_min_x, FLOW_LANE_CENTER_Y, -0.3),
            (28.0, FLOW_LANE_LENGTH_Y, 0.4),
        ),
        _box(
            "FLOW_EDGE_EAST", "2126 OVERHEAD FLOW | yellow east lane edge",
            "FlowEdge", "yellow", (flow_max_x, FLOW_LANE_CENTER_Y, -0.3),
            (28.0, FLOW_LANE_LENGTH_Y, 0.4),
        ),
        _box(
            "FLOW_EDGE_INBOUND", "2126 OVERHEAD FLOW | yellow inbound cap",
            "FlowEdge", "yellow", (FLOW_LANE_X, flow_min_y, -0.3),
            (FLOW_LANE_WIDTH_X, 28.0, 0.4),
        ),
        _box(
            "FLOW_EDGE_OUTBOUND", "2126 OVERHEAD FLOW | yellow outbound cap",
            "FlowEdge", "yellow", (FLOW_LANE_X, flow_max_y, -0.3),
            (FLOW_LANE_WIDTH_X, 28.0, 0.4),
        ),
    ))

    pad_edge_x = PROCESS_PAD_X + PROCESS_PAD_WIDTH_X / 2.0
    connector_edge_x = flow_min_x
    connector_width = connector_edge_x - pad_edge_x
    connector_x = pad_edge_x + connector_width / 2.0
    for index, center_y in enumerate(FLOW_CONNECTOR_Y, start=1):
        specs.append(_box(
            "FLOW_CONNECTOR_{:02d}".format(index),
            "2126 OVERHEAD FLOW | cream station connector {:02d}".format(index),
            "FlowConnector",
            "cream",
            (connector_x, center_y, -0.25),
            (connector_width, 58.0, 0.3),
        ))

    for index, center_y in enumerate(FLOW_ARROW_Y, start=1):
        prefix = "FLOW_ARROW_{:02d}".format(index)
        specs.extend((
            _box(
                prefix + "_SHAFT",
                "2126 OVERHEAD FLOW | yellow arrow {:02d} shaft".format(index),
                "FlowArrow", "yellow", (FLOW_LANE_X, center_y - 40.0, -0.25),
                (42.0, 240.0, 0.3),
            ),
            _box(
                prefix + "_HEAD_WEST",
                "2126 OVERHEAD FLOW | yellow arrow {:02d} west head".format(index),
                "FlowArrow", "yellow",
                (FLOW_LANE_X - 58.0, center_y + 82.0, -0.25),
                (38.0, 150.0, 0.3), 45.0,
            ),
            _box(
                prefix + "_HEAD_EAST",
                "2126 OVERHEAD FLOW | yellow arrow {:02d} east head".format(index),
                "FlowArrow", "yellow",
                (FLOW_LANE_X + 58.0, center_y + 82.0, -0.25),
                (38.0, 150.0, 0.3), -45.0,
            ),
        ))
    return tuple(specs)


def build_text_specs() -> Tuple[Mapping[str, Any], ...]:
    specs: List[Mapping[str, Any]] = []
    for row in STATION_PADS:
        item_id = str(row["id"])
        specs.append({
            "id": "LABEL_" + item_id,
            "label": "2126 OVERHEAD LABEL | " + item_id,
            "role": "StationLabel",
            "text": str(row["text"]),
            "location_cm": (STATION_LABEL_X, float(row["center_y"]), 0.05),
            "rotation_deg_pitch_yaw_roll": (-90.0, -90.0, 0.0),
            "world_size_cm": 82.0,
            "colour_rgba": (23, 29, 33, 255),
        })
    specs.extend((
        {
            "id": "LABEL_TITLE",
            "label": "2126 OVERHEAD LABEL | Press Shop title",
            "role": "DeckTitle",
            "text": "PRESS SHOP 2126",
            "location_cm": (-4700.0, DECK_CENTER_XY[1], 0.05),
            "rotation_deg_pitch_yaw_roll": (-90.0, -90.0, 0.0),
            "world_size_cm": 160.0,
            "colour_rgba": (232, 222, 194, 255),
        },
        {
            "id": "LABEL_INBOUND",
            "label": "2126 OVERHEAD LABEL | inbound coil flow",
            "role": "FlowLabel",
            "text": "INBOUND COIL",
            "location_cm": (-5350.0, 1500.0, 0.05),
            "rotation_deg_pitch_yaw_roll": (-90.0, -90.0, 0.0),
            "world_size_cm": 92.0,
            "colour_rgba": (225, 185, 79, 255),
        },
        {
            "id": "LABEL_OUTBOUND",
            "label": "2126 OVERHEAD LABEL | outbound panel flow",
            "role": "FlowLabel",
            "text": "OUTBOUND PANEL",
            "location_cm": (-5350.0, 16000.0, 0.05),
            "rotation_deg_pitch_yaw_roll": (-90.0, -90.0, 0.0),
            "world_size_cm": 92.0,
            "colour_rgba": (225, 185, 79, 255),
        },
    ))
    return tuple(specs)


def _rotated_box_half_extents(spec: Mapping[str, Any]) -> Tuple[float, float]:
    dimensions = spec["dimensions_cm"]
    half_x = float(dimensions[0]) / 2.0
    half_y = float(dimensions[1]) / 2.0
    radians = math.radians(float(spec["yaw_deg"]))
    cosine = abs(math.cos(radians))
    sine = abs(math.sin(radians))
    return (
        half_x * cosine + half_y * sine,
        half_x * sine + half_y * cosine,
    )


def camera_margins(spec: Mapping[str, Any]) -> Dict[str, float]:
    minimum = spec["bounds_min_xy_cm"]
    maximum = spec["bounds_max_xy_cm"]
    center = spec["center_xy_cm"]
    width = float(spec["ortho_width_cm"])
    visible_x = width / CAMERA_ASPECT
    return {
        "screen_horizontal_world_y_cm": min(
            float(minimum[1]) - (float(center[1]) - width / 2.0),
            (float(center[1]) + width / 2.0) - float(maximum[1]),
        ),
        "screen_vertical_world_x_cm": min(
            float(minimum[0]) - (float(center[0]) - visible_x / 2.0),
            (float(center[0]) + visible_x / 2.0) - float(maximum[0]),
        ),
        "visible_width_world_y_cm": width,
        "visible_height_world_x_cm": visible_x,
    }


def validate_design_contract() -> Dict[str, Any]:
    boxes = build_box_specs()
    texts = build_text_specs()
    material_ids = {str(row["id"]) for row in MATERIAL_SPECS}
    if material_ids != {"deck", "zone", "cream", "yellow"}:
        fail("presentation material role set changed")
    material_names = [str(row["name"]) for row in MATERIAL_SPECS]
    if len(material_names) != len(set(material_names)):
        fail("duplicate material asset name")
    for row in MATERIAL_SPECS:
        srgb_hex_to_linear(str(row["srgb_hex"]))

    ids = [str(row["id"]) for row in boxes] + [str(row["id"]) for row in texts]
    labels = [str(row["label"]) for row in boxes] + [str(row["label"]) for row in texts]
    if len(ids) != len(set(ids)) or len(labels) != len(set(labels)):
        fail("presentation actor IDs and labels must be unique")
    if any(token in label.lower() for label in labels for token in ROOF_TOKENS):
        fail("presentation actor label implies roof geometry")

    for spec in boxes:
        if spec["material_id"] not in material_ids:
            fail("box references an unknown material: " + str(spec["id"]))
        dimensions = spec["dimensions_cm"]
        if len(dimensions) != 3 or any(float(value) <= 0.0 for value in dimensions):
            fail("box dimensions must be positive: " + str(spec["id"]))
        location = spec["location_cm"]
        top_z = float(location[2]) + float(dimensions[2]) / 2.0
        if top_z > PRESENTATION_TOP_Z + NUMERIC_TOLERANCE:
            fail("box would occlude a zero-Z sprite plane: " + str(spec["id"]))
        if spec["id"] == "DECK_BASE":
            continue
        half_x, half_y = _rotated_box_half_extents(spec)
        if (
            float(location[0]) - half_x < DECK_MIN_XY[0] - NUMERIC_TOLERANCE
            or float(location[0]) + half_x > DECK_MAX_XY[0] + NUMERIC_TOLERANCE
            or float(location[1]) - half_y < DECK_MIN_XY[1] - NUMERIC_TOLERANCE
            or float(location[1]) + half_y > DECK_MAX_XY[1] + NUMERIC_TOLERANCE
        ):
            fail("presentation box escapes the dark deck: " + str(spec["id"]))

    ordered_pads = sorted(
        STATION_PADS,
        key=lambda row: float(row["center_y"]),
    )
    previous_end = None
    for row in ordered_pads:
        start = float(row["center_y"]) - float(row["length_y"]) / 2.0
        end = float(row["center_y"]) + float(row["length_y"]) / 2.0
        if previous_end is not None and start - previous_end < 40.0:
            fail("station pads overlap or lose their dark gutter")
        if start < DECK_MIN_XY[1] or end > DECK_MAX_XY[1]:
            fail("station pad leaves the deck")
        previous_end = end

    for camera in CAMERA_SPECS:
        if tuple(camera.get("rotation", CAMERA_ROTATION)) != CAMERA_ROTATION:
            fail("camera rotation changed")
        margins = camera_margins(camera)
        if (
            margins["screen_horizontal_world_y_cm"] < CAMERA_MIN_MARGIN_CM
            or margins["screen_vertical_world_x_cm"] < CAMERA_MIN_MARGIN_CM
        ):
            fail("camera does not frame its declared bounds")

    return {
        "box_specs": boxes,
        "text_specs": texts,
        "box_role_counts": dict(Counter(str(row["role"]) for row in boxes)),
        "text_role_counts": dict(Counter(str(row["role"]) for row in texts)),
        "camera_margins": {
            str(row["id"]): camera_margins(row) for row in CAMERA_SPECS
        },
    }


def _record_tags(record: Mapping[str, Any]) -> frozenset[str]:
    value = record.get("tags", ())
    if not isinstance(value, (list, tuple, set, frozenset)):
        return frozenset()
    return frozenset(str(tag) for tag in value)


def legacy_removal_reason(record: Mapping[str, Any]) -> str | None:
    """Return the exact deletion selector for a source-map actor record."""
    tags = _record_tags(record)
    if VISUAL_LAYER_TAG in tags or PRESENTATION_TAG in tags:
        return None
    class_path = str(record.get("class_path", ""))
    if any(token in class_path for token in PROTECTED_NATIVE_CLASS_TOKENS):
        return None
    if VISUAL_ONLY_TAG in tags and NOT_WIP_TAG in tags:
        return "legacy_visual_only_not_wip"
    if HISM_SHELL_TAG in tags:
        return "onefactory_hism_shell"
    if LEGACY_MANAGEMENT_CAMERA_TAG in tags:
        return "legacy_management_camera"
    if class_path in LEGACY_PRESENTATION_CLASS_PATHS:
        return "legacy_unbound_presentation_class"
    return None


def is_roof_record(record: Mapping[str, Any]) -> bool:
    # The explicit ``RooflessPresentation`` provenance tag is a negative
    # assertion, not geometry.  Remove that word before checking structural
    # roof/ceiling/canopy tokens.
    label = str(record.get("label", "")).lower().replace("roofless", "")
    tags = " ".join(_record_tags(record)).lower().replace("roofless", "")
    return any(token in label or token in tags for token in ROOF_TOKENS)


def asset_disk_path(asset_path: str) -> Path:
    normalised = asset_path.split(".", 1)[0]
    if not normalised.startswith("/Game/"):
        raise ValueError("not a /Game asset path: " + asset_path)
    return PROJECT / "Content" / (normalised[len("/Game/"):] + ".uasset")


def _class_path(actor: Any) -> str:
    actor_class = actor.get_class()
    try:
        return str(actor_class.get_path_name())
    except Exception:
        return str(actor_class)


def actor_record(actor: Any) -> Dict[str, Any]:
    return {
        "label": str(actor.get_actor_label()),
        "path": str(actor.get_path_name()),
        "class_path": _class_path(actor),
        "tags": sorted(str(tag) for tag in actor.tags),
    }


def _world_package_name(world: Any) -> str:
    return str(world.get_outermost().get_name()) if world else ""


def _world_game_mode_path(world: Any) -> str | None:
    if not world:
        return None
    settings = world.get_world_settings()
    game_mode = settings.get_editor_property("default_game_mode")
    return str(game_mode.get_path_name()) if game_mode else None


def _editor_world() -> Any:
    subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if subsystem is None:
        fail("UnrealEditorSubsystem is unavailable")
    world = subsystem.get_editor_world()
    if world is None:
        fail("editor world is unavailable")
    return world


def _actor_subsystem() -> Any:
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if subsystem is None:
        fail("EditorActorSubsystem is unavailable")
    return subsystem


def _level_subsystem() -> Any:
    subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if subsystem is None:
        fail("LevelEditorSubsystem is unavailable")
    return subsystem


def dirty_package_paths() -> Dict[str, List[str]]:
    content = sorted(
        str(package.get_path_name())
        for package in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()
    )
    maps = sorted(
        str(package.get_path_name())
        for package in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()
    )
    return {"content": content, "maps": maps}


def _normalise_registry_asset_path(value: Any) -> str:
    path = str(value)
    leaf = path.rsplit("/", 1)[-1]
    if "." in leaf:
        path = path.rsplit(".", 1)[0]
    return path


def expected_failed_run_disk_fingerprints(
    artifacts: Sequence[Mapping[str, Any]] = FAILED_RUN_ARTIFACTS,
) -> Dict[str, Dict[str, Any]]:
    return {
        Path(row["disk"]).resolve().as_posix(): {
            "sha256": str(row["sha256"]),
            "bytes": int(row["bytes"]),
        }
        for row in artifacts
    }


def validate_failed_run_artifact_fingerprints(
    disk_fingerprints: Mapping[str, Mapping[str, Any]],
    registry_assets: Iterable[str],
    artifacts: Sequence[Mapping[str, Any]] = FAILED_RUN_ARTIFACTS,
) -> None:
    """Prove that recovery is bounded to the exact first-run residue."""
    expected_disk = expected_failed_run_disk_fingerprints(artifacts)
    actual_disk = {
        str(path): {
            "sha256": str(values.get("sha256", "")),
            "bytes": int(values.get("bytes", -1)),
        }
        for path, values in disk_fingerprints.items()
    }
    if actual_disk != expected_disk:
        fail("failed-run disk inventory is not the exact five-package fingerprint")
    expected_registry = {
        str(row["asset"]) for row in artifacts
    }
    actual_registry = {
        _normalise_registry_asset_path(value) for value in registry_assets
    }
    if actual_registry != expected_registry:
        fail("failed-run asset-registry inventory is not the exact five packages")


def _inspect_target_artifacts() -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    disk: Dict[str, Dict[str, Any]] = {}
    if TARGET_ROOT_DISK.exists():
        for path in sorted(TARGET_ROOT_DISK.rglob("*")):
            if path.is_file():
                disk[path.resolve().as_posix()] = {
                    "sha256": digest(path),
                    "bytes": path.stat().st_size,
                }
    registry = sorted(
        _normalise_registry_asset_path(path)
        for path in unreal.EditorAssetLibrary.list_assets(
            TARGET_ROOT, recursive=True, include_folder=False
        )
    )
    return disk, registry


def recover_exact_failed_run_assets(
    protected_before: Mapping[str, str],
) -> Dict[str, Any]:
    """Delete only an exact, independently receipted five-package residue."""
    disk, registry = _inspect_target_artifacts()
    if not disk and not registry:
        if (
            RECOVERY_RECEIPT.exists()
            or RECOVERY_RECEIPT_V002.exists()
            or RECOVERY_RECEIPT_V003.exists()
        ):
            fail("recovery receipt exists without failed-run residue; refusing rerun")
        return {"performed": False}

    if RECEIPT.exists():
        fail("install receipt exists; failed-run recovery is not permitted")

    prior_recovery: Dict[str, Any] | None = None
    if RECOVERY_RECEIPT_V002.exists():
        if not RECOVERY_RECEIPT.exists():
            fail("second recovery receipt exists without the first recovery receipt")
        if digest(RECOVERY_RECEIPT) != RECOVERY_RECEIPT_SHA256_AFTER_FIRST_RECOVERY:
            fail("first failed-run recovery receipt changed")
        if digest(RECOVERY_RECEIPT_V002) != RECOVERY_RECEIPT_SHA256_AFTER_SECOND_RECOVERY:
            fail("second failed-run recovery receipt changed")
        if RECOVERY_RECEIPT_V003.exists():
            fail("third failed-run recovery receipt already exists")
        artifacts = THIRD_FAILED_RUN_ARTIFACTS
        failed_log = THIRD_FAILED_RUN_LOG
        failed_log_sha256 = THIRD_FAILED_RUN_LOG_SHA256
        failed_error = THIRD_FAILED_RUN_ERROR
        recovery_receipt = RECOVERY_RECEIPT_V003
        recovery_schema = RECOVERY_RECEIPT_SCHEMA_V003
        prior_recovery = {
            "receipt": RECOVERY_RECEIPT_V002.as_posix(),
            "sha256": RECOVERY_RECEIPT_SHA256_AFTER_SECOND_RECOVERY,
        }
    elif RECOVERY_RECEIPT.exists():
        if digest(RECOVERY_RECEIPT) != RECOVERY_RECEIPT_SHA256_AFTER_FIRST_RECOVERY:
            fail("first failed-run recovery receipt changed")
        if RECOVERY_RECEIPT_V003.exists():
            fail("third recovery receipt exists before the second recovery receipt")
        artifacts = SECOND_FAILED_RUN_ARTIFACTS
        failed_log = SECOND_FAILED_RUN_LOG
        failed_log_sha256 = SECOND_FAILED_RUN_LOG_SHA256
        failed_error = SECOND_FAILED_RUN_ERROR
        recovery_receipt = RECOVERY_RECEIPT_V002
        recovery_schema = RECOVERY_RECEIPT_SCHEMA_V002
        prior_recovery = {
            "receipt": RECOVERY_RECEIPT.as_posix(),
            "sha256": RECOVERY_RECEIPT_SHA256_AFTER_FIRST_RECOVERY,
        }
    else:
        if RECOVERY_RECEIPT_V002.exists() or RECOVERY_RECEIPT_V003.exists():
            fail("later recovery receipt exists without the first recovery receipt")
        artifacts = FAILED_RUN_ARTIFACTS
        failed_log = FAILED_RUN_LOG
        failed_log_sha256 = FAILED_RUN_LOG_SHA256
        failed_error = FAILED_RUN_ERROR
        recovery_receipt = RECOVERY_RECEIPT
        recovery_schema = RECOVERY_RECEIPT_SCHEMA

    if not failed_log.is_file() or digest(failed_log) != failed_log_sha256:
        fail("failed-run log is missing or changed")
    try:
        failed_log_text = failed_log.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        fail("failed-run log is unreadable: " + str(exc))
    if failed_error not in failed_log_text:
        fail("failed-run log does not contain the exact DECK_BASE collision error")
    if "PRESSSHOP_2126_OVERHEAD_DECK_PRESENTATION_V001_PASS" in failed_log_text:
        fail("failed-run log contains a success marker; cleanup is not permitted")

    validate_failed_run_artifact_fingerprints(disk, registry, artifacts)
    exact_root = (
        PROJECT
        / "Content"
        / "LineBoss"
        / "Candidates"
        / "PressShop"
        / "PressShop2126_OverheadPresentation_v002"
    ).resolve()
    if TARGET_ROOT_DISK.resolve() != exact_root:
        fail("failed-run recovery root changed")
    if TARGET_ROOT != (
        "/Game/LineBoss/Candidates/PressShop/"
        "PressShop2126_OverheadPresentation_v002"
    ):
        fail("failed-run registry root changed")

    # This is the only destructive asset operation in the script.  Its exact
    # target contents, log provenance and every protected hash are proven above.
    if not unreal.EditorAssetLibrary.delete_directory(TARGET_ROOT):
        fail("Unreal could not delete the verified failed-run target root")
    unreal.collect_garbage()
    disk_after, registry_after = _inspect_target_artifacts()
    if disk_after or registry_after:
        fail("verified failed-run target root was not fully removed")
    protected_after = protected_snapshot()
    if dict(protected_after) != dict(protected_before):
        fail("protected map changed during verified failed-run recovery")
    if digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
        fail("source integration map changed during verified failed-run recovery")

    record = {
        "performed": True,
        "schema": recovery_schema,
        "status": "PASS_EXACT_FAILED_RUN_ARTIFACTS_REMOVED__TARGET_READY_FOR_REBUILD",
        "failed_run_error": failed_error,
        "failed_run_log": failed_log.as_posix(),
        "failed_run_log_sha256": failed_log_sha256,
        "deletion_api": "EditorAssetLibrary.delete_directory",
        "deleted_registry_root": TARGET_ROOT,
        "deleted_artifacts": [
            {
                "asset": str(row["asset"]),
                "disk": Path(row["disk"]).as_posix(),
                "sha256": str(row["sha256"]),
                "bytes": int(row["bytes"]),
            }
            for row in artifacts
        ],
        "protected_hashes_before": dict(protected_before),
        "protected_hashes_after": protected_after,
        "source_map_sha256_after": digest(SOURCE_FILE),
    }
    if prior_recovery is not None:
        record["previous_recovery"] = prior_recovery
    _write_new_json(recovery_receipt, record)
    return record


def _vector(values: Sequence[float]) -> Any:
    return unreal.Vector(
        x=float(values[0]), y=float(values[1]), z=float(values[2])
    )


def _rotator(values: Sequence[float]) -> Any:
    return unreal.Rotator(
        pitch=float(values[0]), yaw=float(values[1]), roll=float(values[2])
    )


def _spawn_actor(
    actor_subsystem: Any,
    actor_class: Any,
    location: Sequence[float],
    rotation: Sequence[float],
    label: str,
) -> Any:
    actor = actor_subsystem.spawn_actor_from_class(
        actor_class, _vector(location), _rotator(rotation), transient=False
    )
    if actor is None:
        fail("could not spawn " + label)
    actor.set_actor_label(label, mark_dirty=True)
    actor.tags = [
        unreal.Name(PASS_TAG),
        unreal.Name(VISUAL_ONLY_TAG),
        unreal.Name(NOT_WIP_TAG),
        unreal.Name(ROOFLESS_TAG),
    ]
    return actor


def create_unlit_material(spec: Mapping[str, Any]) -> Tuple[Any, Dict[str, Any]]:
    asset_name = str(spec["name"])
    asset_path = MATERIAL_ROOT + "/" + asset_name
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        fail("candidate material already exists: " + asset_path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name,
        MATERIAL_ROOT,
        unreal.Material,
        unreal.MaterialFactoryNew(),
    )
    if not isinstance(material, unreal.Material):
        fail("could not create candidate material " + asset_name)
    material.set_editor_property(
        "shading_model", unreal.MaterialShadingModel.MSM_UNLIT
    )
    colour = srgb_hex_to_linear(str(spec["srgb_hex"]))
    expression = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -220, 0
    )
    if expression is None:
        fail("could not create colour expression for " + asset_name)
    expression.set_editor_property(
        "constant", unreal.LinearColor(colour[0], colour[1], colour[2], 1.0)
    )
    if not unreal.MaterialEditingLibrary.connect_material_property(
        expression, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    ):
        fail("could not connect unlit colour for " + asset_name)
    unreal.MaterialEditingLibrary.recompile_material(material)
    if not unreal.EditorAssetLibrary.save_loaded_asset(
        material, only_if_is_dirty=False
    ):
        fail("could not save candidate material " + asset_name)
    disk = asset_disk_path(asset_path)
    if not disk.is_file():
        fail("candidate material package missing on disk: " + asset_name)
    return material, {
        "id": str(spec["id"]),
        "asset": asset_path,
        "srgb_hex": str(spec["srgb_hex"]),
        "linear_rgb": list(colour),
        "sha256": digest(disk),
        "bytes": disk.stat().st_size,
        "shading_model": "UNLIT",
    }


def disable_and_verify_collision(
    actor: Any, component: Any, item_id: str
) -> Dict[str, Any]:
    """Apply and read back an explicit actor/component ignore-all contract."""
    actor.set_actor_enable_collision(False)
    component.set_collision_profile_name(
        unreal.Name("NoCollision"), update_overlaps=False
    )
    # Response/enabled setters deliberately follow the named profile because
    # this project's native NoCollision profile retains blocking response
    # metadata.  Unreal consequently reports Custom; that is accepted only if
    # the strict enabled and every-channel readbacks below prove inertness.
    component.set_collision_response_to_all_channels(
        unreal.CollisionResponseType.ECR_IGNORE
    )
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("generate_overlap_events", False)
    component.set_editor_property("can_ever_affect_navigation", False)

    actor_collision = bool(actor.get_actor_enable_collision())
    collision_enabled = str(component.get_collision_enabled())
    collision_profile = str(component.get_collision_profile_name())
    normalised_profile = "".join(
        character.lower() for character in collision_profile if character.isalnum()
    )
    if actor_collision:
        fail("presentation actor retained collision: " + item_id)
    if "NO_COLLISION" not in collision_enabled.upper():
        fail("presentation component retained collision: " + item_id)
    if normalised_profile not in {"nocollision", "custom"}:
        fail("presentation component profile is neither NoCollision nor Custom: " + item_id)

    ignored_channels: List[str] = []
    for channel_name in COLLISION_CHANNEL_NAMES:
        channel = getattr(unreal.CollisionChannel, channel_name)
        response = str(component.get_collision_response_to_channel(channel))
        if "ECR_IGNORE" not in response.upper():
            fail(
                "presentation component does not ignore {}: {}".format(
                    channel_name, item_id
                )
            )
        ignored_channels.append(channel_name)
    return {
        "actor_collision_enabled": actor_collision,
        "component_collision_enabled": collision_enabled,
        "collision_profile": collision_profile,
        "profile_acceptance": (
            "NativeNoCollision"
            if normalised_profile == "nocollision"
            else "CustomWithNoCollisionAndIgnoreAll"
        ),
        "ignored_channels": ignored_channels,
    }


def spawn_box_actor(
    actor_subsystem: Any,
    cube: Any,
    materials: Mapping[str, Any],
    spec: Mapping[str, Any],
) -> Dict[str, Any]:
    actor = _spawn_actor(
        actor_subsystem,
        unreal.StaticMeshActor,
        spec["location_cm"],
        (0.0, float(spec["yaw_deg"]), 0.0),
        str(spec["label"]),
    )
    actor.tags = list(actor.tags) + [
        unreal.Name("LB.PressShop.OverheadDeck.Role." + str(spec["role"]))
    ]
    component = actor.get_editor_property("static_mesh_component")
    if component is None or not component.set_static_mesh(cube):
        fail("could not assign native cube to " + str(spec["id"]))
    dimensions = spec["dimensions_cm"]
    actor.set_actor_scale3d(
        unreal.Vector(
            x=float(dimensions[0]) / 100.0,
            y=float(dimensions[1]) / 100.0,
            z=float(dimensions[2]) / 100.0,
        )
    )
    material = materials[str(spec["material_id"])]
    component.set_material(0, material)
    component.set_editor_property("cast_shadow", False)
    collision = disable_and_verify_collision(actor, component, str(spec["id"]))
    assigned = component.get_material(0)
    if assigned is None or str(assigned.get_path_name()) != str(material.get_path_name()):
        fail("presentation cube material readback failed: " + str(spec["id"]))
    return {
        "id": str(spec["id"]),
        "label": str(spec["label"]),
        "actor_path": str(actor.get_path_name()),
        "role": str(spec["role"]),
        "material": str(material.get_path_name()),
        "location_cm": list(spec["location_cm"]),
        "dimensions_cm": list(spec["dimensions_cm"]),
        "yaw_deg": float(spec["yaw_deg"]),
        "collision": "NoCollision",
        "collision_readback": collision,
        "cast_shadow": False,
    }


def spawn_text_actor(
    actor_subsystem: Any, spec: Mapping[str, Any]
) -> Dict[str, Any]:
    actor = _spawn_actor(
        actor_subsystem,
        unreal.TextRenderActor,
        spec["location_cm"],
        spec["rotation_deg_pitch_yaw_roll"],
        str(spec["label"]),
    )
    actor.tags = list(actor.tags) + [
        unreal.Name("LB.PressShop.OverheadDeck.Role." + str(spec["role"]))
    ]
    component = actor.get_editor_property("text_render")
    if component is None:
        fail("text actor has no TextRender component: " + str(spec["id"]))
    component.set_text(str(spec["text"]))
    component.set_world_size(float(spec["world_size_cm"]))
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(
        unreal.VerticalTextAligment.EVRTA_TEXT_CENTER
    )
    colour = spec["colour_rgba"]
    component.set_text_render_color(
        unreal.Color(
            int(colour[0]), int(colour[1]), int(colour[2]), int(colour[3])
        )
    )
    component.set_editor_property("cast_shadow", False)
    collision = disable_and_verify_collision(actor, component, str(spec["id"]))
    return {
        "id": str(spec["id"]),
        "label": str(spec["label"]),
        "actor_path": str(actor.get_path_name()),
        "role": str(spec["role"]),
        "text": str(spec["text"]),
        "location_cm": list(spec["location_cm"]),
        "rotation_deg_pitch_yaw_roll": list(
            spec["rotation_deg_pitch_yaw_roll"]
        ),
        "world_size_cm": float(spec["world_size_cm"]),
        "colour_rgba": list(spec["colour_rgba"]),
        "collision": "NoCollision",
        "collision_readback": collision,
        "cast_shadow": False,
    }


def spawn_camera_actor(
    actor_subsystem: Any, spec: Mapping[str, Any]
) -> Dict[str, Any]:
    center = spec["center_xy_cm"]
    actor = _spawn_actor(
        actor_subsystem,
        unreal.CameraActor,
        (float(center[0]), float(center[1]), CAMERA_Z_CM),
        CAMERA_ROTATION,
        str(spec["label"]),
    )
    actor.tags = list(actor.tags) + [
        unreal.Name(CAMERA_TAG), unreal.Name(str(spec["role_tag"]))
    ]
    actor.tags = list(actor.tags) + [
        unreal.Name(str(tag)) for tag in spec.get("additional_tags", ())
    ]
    component = actor.get_editor_property("camera_component")
    if component is None:
        fail("camera has no native CameraComponent: " + str(spec["id"]))
    component.set_editor_property(
        "projection_mode", unreal.CameraProjectionMode.ORTHOGRAPHIC
    )
    component.set_editor_property("ortho_width", float(spec["ortho_width_cm"]))
    component.set_editor_property("aspect_ratio", CAMERA_ASPECT)
    component.set_editor_property("constrain_aspect_ratio", True)
    forward = actor.get_actor_forward_vector()
    if (
        abs(float(forward.x)) > 0.00001
        or abs(float(forward.y)) > 0.00001
        or float(forward.z) > -0.99999
    ):
        fail("camera is not exactly true-overhead: " + str(spec["id"]))
    margins = camera_margins(spec)
    return {
        "id": str(spec["id"]),
        "label": str(spec["label"]),
        "actor_path": str(actor.get_path_name()),
        "projection": "ORTHOGRAPHIC",
        "ortho_width_cm": float(spec["ortho_width_cm"]),
        "aspect_ratio": CAMERA_ASPECT,
        "location_cm": [float(center[0]), float(center[1]), CAMERA_Z_CM],
        "rotation_deg_pitch_yaw_roll": list(CAMERA_ROTATION),
        "camera_axis_contract": {
            "view": "-Z",
            "screen_right": "+Y",
            "screen_up": "+X",
        },
        "declared_bounds_min_xy_cm": list(spec["bounds_min_xy_cm"]),
        "declared_bounds_max_xy_cm": list(spec["bounds_max_xy_cm"]),
        "margins": margins,
    }


def _count_tag(records: Iterable[Mapping[str, Any]], tag: str) -> int:
    return sum(1 for record in records if tag in _record_tags(record))


def validate_source_world_inventory(
    records: Sequence[Mapping[str, Any]], source_receipt: Mapping[str, Any]
) -> Dict[str, Any]:
    if len(records) != EXPECTED_SOURCE_ACTORS:
        fail(
            "source clone actor count changed: expected {}, found {}".format(
                EXPECTED_SOURCE_ACTORS, len(records)
            )
        )
    if _count_tag(records, VISUAL_LAYER_TAG) != EXPECTED_SOURCE_VISUAL_LAYERS:
        fail("source clone visual-layer tag count changed")
    if _count_tag(records, PRESENTATION_TAG) != EXPECTED_SOURCE_PRESENTATION_ADAPTERS:
        fail("source clone presentation-adapter count changed")
    if _count_tag(records, SOURCE_CAMERA_TAG) != EXPECTED_SOURCE_CAMERAS:
        fail("source clone camera count changed")
    if _count_tag(records, BOOTSTRAP_TAG) != 1:
        fail("source clone must retain exactly one OneFactory bootstrap")
    if _count_tag(records, BUILD_AUTHORITY_TAG) != 1:
        fail("source clone must retain exactly one Press build authority")
    if _count_tag(records, PLAYER_START_TAG) != 1:
        fail("source clone must retain exactly one management PlayerStart")
    layer_classes = {
        str(record["class_path"])
        for record in records
        if VISUAL_LAYER_TAG in _record_tags(record)
    }
    if layer_classes != {str(source_receipt["native_visual_layer_class"])}:
        fail("source clone visual-layer class changed")
    presentation_classes = {
        str(record["class_path"])
        for record in records
        if PRESENTATION_TAG in _record_tags(record)
    }
    if presentation_classes != {str(source_receipt["native_presentation_class"])}:
        fail("source clone presentation class changed")
    removals = [record for record in records if legacy_removal_reason(record)]
    if len(removals) != EXPECTED_SOURCE_LEGACY_REMOVALS:
        fail(
            "legacy presentation removal count changed: expected {}, found {}".format(
                EXPECTED_SOURCE_LEGACY_REMOVALS, len(removals)
            )
        )
    for record in removals:
        class_path = str(record.get("class_path", ""))
        if any(token in class_path for token in PROTECTED_NATIVE_CLASS_TOKENS):
            fail("removal selector reached protected native infrastructure")
    return {
        "removals": removals,
        "removal_reason_counts": dict(Counter(
            str(legacy_removal_reason(record)) for record in removals
        )),
        "removal_class_counts": dict(Counter(
            str(record["class_path"]) for record in removals
        )),
    }


def _write_new_json(path: Path, value: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("xb") as handle:
            handle.write(canonical_json_bytes(value))
    except FileExistsError:
        fail("receipt already exists; refusing overwrite")


def main() -> None:
    design = validate_design_contract()
    source_receipt = load_and_validate_source_receipt()
    protected_before = protected_snapshot()

    if RECEIPT.exists():
        fail("target receipt already exists; refusing rerun")
    if digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
        fail("source integration map hash changed")
    if dirty_package_paths() != {"content": [], "maps": []}:
        fail("editor has dirty packages before candidate creation")

    world_before = _editor_world()
    world_before_name = _world_package_name(world_before)
    if world_before_name in {SOURCE_MAP, TARGET_MAP}:
        fail("run from an unrelated clean editor world, not source or target")

    recovery = recover_exact_failed_run_assets(protected_before)
    remaining_disk_files = (
        [path for path in TARGET_ROOT_DISK.rglob("*") if path.is_file()]
        if TARGET_ROOT_DISK.exists()
        else []
    )
    if TARGET_FILE.exists() or remaining_disk_files:
        fail("target candidate still exists on disk; refusing overwrite")
    if unreal.EditorAssetLibrary.does_asset_exist(TARGET_MAP):
        fail("target candidate map still exists in the asset registry")
    remaining_registry_assets = unreal.EditorAssetLibrary.list_assets(
        TARGET_ROOT, recursive=True, include_folder=False
    )
    if remaining_registry_assets:
        fail("target candidate assets still exist in the asset registry")
    if protected_snapshot() != protected_before:
        fail("protected maps changed before target creation")
    if digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
        fail("source integration map changed before target creation")

    cube = unreal.load_asset(CUBE_ASSET)
    if not isinstance(cube, unreal.StaticMesh):
        fail("native Unreal cube is unavailable")
    level_subsystem = _level_subsystem()
    actor_subsystem = _actor_subsystem()

    # On a fresh lane this is the first mutating operation.  The only allowed
    # earlier mutation is exact failed-run recovery, whose five-package disk and
    # registry fingerprints are separately guarded and receipted above.
    if not level_subsystem.new_level_from_template(TARGET_MAP, SOURCE_MAP):
        fail("could not create the presentation candidate from the source map")
    world = _editor_world()
    if _world_package_name(world) != TARGET_MAP:
        fail("target candidate is not the active editor world")
    game_mode_before = _world_game_mode_path(world)
    if game_mode_before != EXPECTED_GAME_MODE:
        fail("candidate clone changed the local OneFactory GameMode")

    actors = list(actor_subsystem.get_all_level_actors())
    records = [actor_record(actor) for actor in actors]
    inventory = validate_source_world_inventory(records, source_receipt)
    actors_by_path = {str(actor.get_path_name()): actor for actor in actors}
    removal_records = sorted(inventory["removals"], key=lambda row: str(row["path"]))
    removal_labels = sorted(str(record["label"]) for record in removal_records)
    removal_paths = sorted(str(record["path"]) for record in removal_records)
    target_actor_prefix = TARGET_MAP + "."
    for record in removal_records:
        actor_path = str(record["path"])
        if not actor_path.startswith(target_actor_prefix):
            fail("destructive selector escaped the target candidate world")
        actor = actors_by_path.get(actor_path)
        if actor is None:
            fail("removal actor disappeared before deletion: " + actor_path)
        if not actor_subsystem.destroy_actor(actor):
            fail("could not remove legacy presentation actor: " + actor_path)

    after_removal = [actor_record(actor) for actor in actor_subsystem.get_all_level_actors()]
    survivors = [record for record in after_removal if legacy_removal_reason(record)]
    if survivors:
        fail("legacy presentation actors survived exact deletion")
    expected_after_removal = EXPECTED_SOURCE_ACTORS - EXPECTED_SOURCE_LEGACY_REMOVALS
    if len(after_removal) != expected_after_removal:
        fail("unexpected actor count after legacy presentation deletion")
    if _count_tag(after_removal, VISUAL_LAYER_TAG) != EXPECTED_SOURCE_VISUAL_LAYERS:
        fail("overhead sprite layers changed during deck cleanup")
    if _count_tag(after_removal, PRESENTATION_TAG) != 1:
        fail("native presentation adapter changed during deck cleanup")
    if _count_tag(after_removal, BOOTSTRAP_TAG) != 1:
        fail("OneFactory bootstrap changed during deck cleanup")
    if _count_tag(after_removal, BUILD_AUTHORITY_TAG) != 1:
        fail("Press build authority changed during deck cleanup")
    if _count_tag(after_removal, PLAYER_START_TAG) != 1:
        fail("management PlayerStart changed during deck cleanup")

    materials: Dict[str, Any] = {}
    material_records: List[Dict[str, Any]] = []
    for material_spec in MATERIAL_SPECS:
        material, record = create_unlit_material(material_spec)
        materials[str(material_spec["id"])] = material
        material_records.append(record)

    created_boxes = [
        spawn_box_actor(actor_subsystem, cube, materials, spec)
        for spec in design["box_specs"]
    ]
    created_texts = [
        spawn_text_actor(actor_subsystem, spec)
        for spec in design["text_specs"]
    ]
    created_cameras = [
        spawn_camera_actor(actor_subsystem, spec) for spec in CAMERA_SPECS
    ]

    final_records = [actor_record(actor) for actor in actor_subsystem.get_all_level_actors()]
    created_actor_count = len(created_boxes) + len(created_texts) + len(created_cameras)
    if len(final_records) != expected_after_removal + created_actor_count:
        fail("final actor count does not match the deterministic presentation plan")
    if _count_tag(final_records, PASS_TAG) != created_actor_count:
        fail("candidate presentation tag count is incomplete")
    if _count_tag(final_records, CAMERA_TAG) != len(CAMERA_SPECS):
        fail("candidate camera tag count is incomplete")
    if _count_tag(final_records, SOURCE_CAMERA_TAG) != 0:
        fail("superseded source cameras survived the presentation pass")
    roof_records = [record for record in final_records if is_roof_record(record)]
    if roof_records:
        fail("roof/ceiling/canopy actor survived in the roofless candidate")
    if _world_game_mode_path(world) != game_mode_before:
        fail("presentation pass changed the local GameMode")

    dirty_before_save = dirty_package_paths()
    expected_dirty_maps = [TARGET_MAP]
    if dirty_before_save["maps"] != expected_dirty_maps:
        fail("only the target map may be dirty before save")
    if dirty_before_save["content"]:
        fail("candidate materials must be explicitly saved before map save")
    if not level_subsystem.save_current_level():
        fail("could not save the presentation candidate map")
    dirty_after_save = dirty_package_paths()
    if dirty_after_save != {"content": [], "maps": []}:
        fail("candidate packages remain dirty after explicit save")
    if not TARGET_FILE.is_file():
        fail("target candidate map package is missing after save")

    protected_after = protected_snapshot()
    if protected_after != protected_before:
        fail("a protected map changed during the candidate presentation pass")
    if digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
        fail("source integration map changed during the candidate pass")

    labels_payload = canonical_json_bytes(removal_labels)
    paths_payload = canonical_json_bytes(removal_paths)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "status": (
            "PASS_CANDIDATE_PRESENTATION_MAP_ASSEMBLED__"
            "VISUAL_CAPTURE_AND_RUNTIME_PENDING"
        ),
        "candidate_only": True,
        "source_map": SOURCE_MAP,
        "source_map_sha256": SOURCE_FILE_SHA256,
        "source_receipt": SOURCE_RECEIPT.as_posix(),
        "source_receipt_sha256": SOURCE_RECEIPT_SHA256,
        "target_map": TARGET_MAP,
        "target_map_sha256": digest(TARGET_FILE),
        "target_map_bytes": TARGET_FILE.stat().st_size,
        "target_creation_api": "LevelEditorSubsystem.new_level_from_template",
        "failed_run_recovery": recovery,
        "current_world_before_target_creation": world_before_name,
        "game_mode_before": game_mode_before,
        "game_mode_after": _world_game_mode_path(world),
        "protected_authority_map_mutated": False,
        "protected_hashes_before": protected_before,
        "protected_hashes_after": protected_after,
        "source_actor_count": EXPECTED_SOURCE_ACTORS,
        "legacy_presentation_removed_count": len(removal_records),
        "legacy_presentation_removal_reason_counts": inventory["removal_reason_counts"],
        "legacy_presentation_removal_class_counts": inventory["removal_class_counts"],
        "legacy_presentation_removed_labels_sha256": hashlib.sha256(labels_payload).hexdigest(),
        "legacy_presentation_removed_paths_sha256": hashlib.sha256(paths_payload).hexdigest(),
        "legacy_presentation_removed_label_sample_first": removal_labels[:12],
        "legacy_presentation_removed_label_sample_last": removal_labels[-12:],
        "retained_native_contract": {
            "visual_layer_class": VISUAL_LAYER_CLASS_PATH,
            "visual_layer_count": EXPECTED_SOURCE_VISUAL_LAYERS,
            "presentation_adapter_class": PRESENTATION_CLASS_PATH,
            "presentation_adapter_count": 1,
            "onefactory_bootstrap_count": 1,
            "press_build_authority_count": 1,
            "management_player_start_count": 1,
            "retained_infrastructure_actor_count": EXPECTED_RETAINED_INFRASTRUCTURE_ACTORS,
            "owns_production_state": False,
        },
        "created_materials": material_records,
        "created_box_actor_count": len(created_boxes),
        "created_text_actor_count": len(created_texts),
        "created_camera_actor_count": len(created_cameras),
        "created_actor_count": created_actor_count,
        "created_box_role_counts": design["box_role_counts"],
        "created_text_role_counts": design["text_role_counts"],
        "created_boxes": created_boxes,
        "created_texts": created_texts,
        "cameras": created_cameras,
        "station_pad_ids": [str(row["id"]) for row in STATION_PADS],
        "material_flow_direction": "+Y",
        "camera_axis_contract": {
            "view": "-Z",
            "screen_right": "+Y",
            "screen_up": "+X",
        },
        "roof_created": False,
        "roof_actor_count_after": 0,
        "new_large_machine_geometry": 0,
        "collision_enabled_on_created_presentation": False,
        "dirty_packages_before_save": dirty_before_save,
        "dirty_packages_after_save": dirty_after_save,
        "runtime_validated": False,
        "runtime_ready": False,
        "packaged_build_validated": False,
        "visual_capture_validated": False,
        "steam_capture_validated": False,
        "honest_status": (
            "Candidate map and native presentation assets are assembled and disk-verified; "
            "fresh rendered visual QA, native automation, gameplay journey, cook and packaged "
            "validation remain required."
        ),
    }
    _write_new_json(RECEIPT, receipt)
    unreal.log(
        "PRESSSHOP_2126_OVERHEAD_DECK_PRESENTATION_V001_PASS map={} receipt={}".format(
            TARGET_MAP, RECEIPT.as_posix()
        )
    )
    unreal.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
