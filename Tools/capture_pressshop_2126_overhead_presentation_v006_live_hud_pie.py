"""Regular-PIE live-HUD Steam-candidate capture for Press Shop 2126 v006.

This lane is deliberately narrower than the exact lifecycle verifier.  It
loads one hash-pinned v006 candidate, starts normal Play In Editor, proves the
real OneFactory player/HUD/bootstrap and complete 57-position route, sends one
order through ``ALBOneFactoryPlayerController.PlaceOrder``, and waits for that
unit to reach a naturally ticking S04 press stroke.  Only then does it
temporarily hand the player's view to the *saved* true-overhead SteamHero
CameraActor and request one native game-viewport screenshot including UMG.

The script never uses SceneCapture2D, a high-resolution editor viewport,
runtime coordinator stepping/freezing, property/visibility edits, asset
imports, saves, builds or cooks.  The only gameplay mutation is the same
player order action exposed by ``+ NEW ORDER``.  It restores the possessed
pawn as view target before PIE ends.  Evidence is append-only: every run owns
a new timestamped directory under Saved and no file is overwritten.

Both the final map SHA-256 and guarded install-receipt SHA-256 are mandatory
environment inputs because they do not exist until the isolated v006 install
has completed.  Importing this module outside Unreal is supported so the
fail-closed contracts can be unit tested without launching the editor.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
import traceback
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

try:  # Offline tests intentionally import this file without Unreal installed.
    import unreal  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised by offline tests
    unreal = None  # type: ignore


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPT_FILE = Path(__file__).resolve()

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
INSTALL_SCHEMA = (
    "cairnwell.press_shop."
    "overhead_presentation_correction_install_receipt.v001"
)
INSTALL_STATUS = (
    "PASS_CANDIDATE_PRESENTATION_CORRECTION_APPLIED__"
    "V005_VISUALS_PRESERVED__FRESH_CAPTURE_AND_PIE_PENDING"
)

MAP_SHA_ENV = "LB_PRESSSHOP_V006_STEAM_UI_EXPECTED_MAP_SHA256"
RECEIPT_SHA_ENV = "LB_PRESSSHOP_V006_STEAM_UI_EXPECTED_INSTALL_RECEIPT_SHA256"
STAMP_ENV = "LB_PRESSSHOP_V006_STEAM_UI_RUN_STAMP"

RUNS_ROOT = (
    PROJECT / "Saved/Audits/PressShop2126/OverheadPresentation_v006/"
    "LiveHUDSteamCapture/Runs"
)
SCREENSHOT_NAME = "PressShop2126_LiveHUD_SteamHero_1920x1080_v006.png"
RECEIPT_NAME = "live_hud_steam_capture_receipt_v001.json"
SCREENSHOT_SIZE = (1920, 1080)
MIN_SCREENSHOT_BYTES = 64 * 1024

OUTPUT_SCHEMA = "cairnwell.press_shop.live_hud_steam_capture_receipt.v001"
PASS_STATUS = (
    "PASS_REGULAR_PIE_NATIVE_PLAYER_LIVE_HUD__"
    "NATURAL_S04_PRESS_STROKE__STEAMHERO_1920X1080_V006"
)
FAIL_STATUS = "FAIL_REGULAR_PIE_LIVE_HUD_STEAM_CAPTURE_V006"

GAME_MODE_CLASS = "/Script/LineBossCarFactory.LBOneFactoryGameMode"
PLAYER_CONTROLLER_CLASS = (
    "/Script/LineBossCarFactory.LBOneFactoryPlayerController"
)
PAWN_CLASS = "/Script/LineBossCarFactory.LBManagementPawn"
HUD_CLASS = "/Script/LineBossCarFactory.LBOneFactoryProductionHUD"
BOOTSTRAP_CLASS = "/Script/LineBossCarFactory.LBOneFactoryBootstrap"
COORDINATOR_CLASS = (
    "/Script/LineBossCarFactory.LBOneFactoryRuntimeCoordinator"
)
PRODUCTION_CLASS = (
    "/Script/LineBossCarFactory.LBOneFactoryProductionFlowAuthority"
)
PRESENTATION_CLASS = (
    "/Script/LineBossCarFactory.LBPressShopOverheadPresentationActor"
)
VISUAL_LAYER_CLASS = (
    "/Script/LineBossCarFactory.LBPressShopOverheadVisualLayerActor"
)
TOP_BAR_CLASS = "/Script/LineBossCarFactory.LBOneFactoryTopBarWidget"
FLOW_STRIP_CLASS = "/Script/LineBossCarFactory.LBOneFactoryFlowStripWidget"
CAMERA_CLASS = "/Script/Engine.CameraActor"

# All three states are paint-visible in Slate.  The two native management
# widgets intentionally use SelfHitTestInvisible on their full-screen roots so
# the bar/strip paint while empty screen space remains click-through.  Hidden
# and Collapsed are the only non-painting states accepted by neither capture
# gate nor final UI snapshot.
PAINT_VISIBLE_WIDGET_STATES = frozenset(
    ("VISIBLE", "HIT_TEST_INVISIBLE", "SELF_HIT_TEST_INVISIBLE")
)

LAYOUT_CLASSES: Mapping[str, str] = {
    "press": "/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority",
    "body_weld": (
        "/Script/LineBossCarFactory.LBOneFactoryBodyWeldStarterLayoutAuthority"
    ),
    "paint": "/Script/LineBossCarFactory.LBOneFactoryPaintStarterLayoutAuthority",
    "assembly": (
        "/Script/LineBossCarFactory.LBOneFactoryAssemblyStarterLayoutAuthority"
    ),
}

EXPECTED_ROUTE_COUNT = 57
EXPECTED_TOPOLOGY_PREFIX = "OF_RUNTIME_TOPOLOGY_V002_"
EXPECTED_PRESS_PREFIX = (
    "OF_PRESS_INBOUND_RECEIVING_001",
    "OF_PRESS_WRAPPED_COIL_STORE_001",
    "OF_PRESS_BLANK_PREP_001",
    "OF_PRESS_PREPARED_BLANK_BUFFER_001",
    "OF_PRESS_TRAIN_001",
    "OF_PRESS_PANEL_INSPECTION_001",
    "OF_PRESS_PANEL_DISPATCH_001",
)
EXPECTED_CONTRACT_IDS = ("CON_STARTER_1", "CON_STARTER_2", "CON_STARTER_3")
PRESS_STATION_ID = "OF_PRESS_TRAIN_001"
PRESS_ROUTE_INDEX = 4
TARGET_PRESS_MACHINE = "S04_TRIM"
TARGET_PRESS_PROGRESS_MIN = 0.485
TARGET_PRESS_PROGRESS_MAX = 0.495
# ComputePressVisualState divides the Press train into five equal machine
# windows.  S04 is index 2 and its visible motion frames span local progress
# [0.28, 0.90), hence global Press progress [0.456, 0.580).  The narrower
# range above is the reviewed hand-off point; this wider range is used only to
# prove that natural motion remained visibly active while the asynchronous UI
# screenshot was written.
S04_ACTIVE_PROGRESS_MIN = (2.0 + 0.28) / 5.0
S04_ACTIVE_PROGRESS_MAX = (2.0 + 0.90) / 5.0
ALLOWED_ACTIVE_FRAMES = ("DESCENDING", "CONTACT", "RISING")

EXPECTED_VISUAL_LAYERS = 146
EXPECTED_BEACONS = 14
EXPECTED_TASK_LIGHTS = 4

STEAM_HERO_LABEL = "CAM | Press Shop 2126 | S03-S06 framed Steam hero v006"
STEAM_HERO_ROLE_TAG = "LB.PressShop.OverheadDeck.Camera.SteamHero.v006"
STEAM_HERO_CAMERA_TAG = "LB.PressShop.OverheadDeck.Camera.v006"
STEAM_HERO_LOCATION = (-8855.75, 11092.0, 21712.544)
STEAM_HERO_ROTATION = (-90.0, 0.0, 0.0)  # pitch, yaw, roll
STEAM_HERO_ORTHO_WIDTH = 5700.0
STEAM_HERO_ASPECT = 16.0 / 9.0

GAME_WORLD_TIMEOUT_SECONDS = 90.0
ACTIVATION_TIMEOUT_SECONDS = 60.0
ORDER_TIMEOUT_SECONDS = 8.0
NATURAL_PRESS_TIMEOUT_SECONDS = 150.0
CAPTURE_TIMEOUT_SECONDS = 30.0
TOTAL_TIMEOUT_SECONDS = 210.0


class CaptureGuardError(RuntimeError):
    """Fail-closed contract error for the v006 live-HUD capture lane."""


def fail(message: str) -> None:
    raise CaptureGuardError(message)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def project_relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT.resolve()).as_posix()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json_new(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")


def required_hash(value: Optional[str], variable: str) -> str:
    if value is None or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        fail(variable + " must be an explicit lowercase 64-digit SHA-256")
    if value == "0" * 64 or len(set(value)) == 1:
        fail(variable + " is a placeholder, not a reviewed SHA-256")
    return value


def required_guard_hashes(environment: Mapping[str, str]) -> Tuple[str, str]:
    return (
        required_hash(environment.get(MAP_SHA_ENV), MAP_SHA_ENV),
        required_hash(environment.get(RECEIPT_SHA_ENV), RECEIPT_SHA_ENV),
    )


def safe_stamp(value: Optional[str] = None) -> str:
    stamp = (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        if value is None
        else value
    )
    if re.fullmatch(r"\d{8}T\d{12}Z", stamp) is None:
        fail("unsafe live-HUD capture run stamp: {!r}".format(stamp))
    return stamp


def create_run_paths(environment: Mapping[str, str]) -> Tuple[str, Path, Path, Path]:
    stamp = safe_stamp(environment.get(STAMP_ENV))
    run_dir = RUNS_ROOT / stamp
    if run_dir.exists():
        fail("refusing to merge or overwrite live-HUD evidence: " + str(run_dir))
    run_dir.mkdir(parents=True, exist_ok=False)
    return stamp, run_dir, run_dir / SCREENSHOT_NAME, run_dir / RECEIPT_NAME


def _close(left: Sequence[float], right: Sequence[float], tolerance=0.02) -> bool:
    return len(left) == len(right) and all(
        math.isfinite(float(a)) and abs(float(a) - float(b)) <= tolerance
        for a, b in zip(left, right)
    )


def validate_install_receipt(
    receipt: Mapping[str, Any], expected_map_sha: str
) -> Dict[str, Any]:
    if receipt.get("schema") != INSTALL_SCHEMA:
        fail("v006 install receipt schema changed")
    if receipt.get("status") != INSTALL_STATUS:
        fail("v006 install receipt status changed")
    if receipt.get("candidate_only") is not True:
        fail("v006 receipt no longer declares candidate-only scope")
    if receipt.get("target_map") != TARGET_MAP:
        fail("v006 install receipt targets a different map")
    if receipt.get("target_map_sha256") != expected_map_sha:
        fail("v006 receipt/map hash chain is not exact")
    if (
        receipt.get("combined_visual_layer_count") != EXPECTED_VISUAL_LAYERS
        or receipt.get("machinery_visual_layer_count") != 120
        or receipt.get("cargo_layer_count") != 26
    ):
        fail("v006 machine/cargo visual inventory changed")
    if (
        receipt.get("machinery_actor_mutated_count") != 0
        or receipt.get("cargo_actor_mutated_count") != 0
        or receipt.get("machine_or_cargo_transform_mutations") != 0
        or receipt.get("new_machinery_geometry") != 0
        or receipt.get("new_cargo_geometry") != 0
        or receipt.get("native_cpp_modified") is not False
    ):
        fail("v006 receipt authorises forbidden machine/cargo/native changes")
    if receipt.get("game_mode_after") != GAME_MODE_CLASS:
        fail("v006 candidate does not retain the OneFactory GameMode")
    if receipt.get("protected_hashes_before") != receipt.get("protected_hashes_after"):
        fail("v006 install receipt reports protected-map drift")
    if receipt.get("runtime_validated") is not False or receipt.get("pie_validated") is not False:
        fail("v006 install receipt improperly claims later runtime evidence")
    mutations = receipt.get("presentation_mutations")
    if not isinstance(mutations, list) or len(mutations) != 83:
        fail("v006 receipt has no presentation mutation inventory")
    heroes = [row for row in mutations if row.get("id") == "steam_hero"]
    if len(heroes) != 1:
        fail("v006 receipt does not identify exactly one SteamHero camera")
    hero = heroes[0]
    if (
        hero.get("kind") != "camera"
        or hero.get("label") != STEAM_HERO_LABEL
        or hero.get("role_tag") != STEAM_HERO_ROLE_TAG
        or not _close(hero.get("location_cm", ()), STEAM_HERO_LOCATION)
        or not _close((hero.get("ortho_width_cm"),), (STEAM_HERO_ORTHO_WIDTH,))
    ):
        fail("v006 receipt SteamHero camera contract changed")
    return {"steam_hero": dict(hero), "mutation_count": len(mutations)}


def load_guarded_install_receipt(
    expected_map_sha: str, expected_receipt_sha: str
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    if not TARGET_FILE.is_file() or not INSTALL_RECEIPT.is_file():
        fail("v006 map/install receipt is absent; guarded install must finish first")
    if sha256(TARGET_FILE) != expected_map_sha:
        fail("v006 target map hash differs from the required environment guard")
    if sha256(INSTALL_RECEIPT) != expected_receipt_sha:
        fail("v006 install receipt hash differs from the required environment guard")
    receipt = load_json(INSTALL_RECEIPT)
    return receipt, validate_install_receipt(receipt, expected_map_sha)


def normalise_name(value: Any) -> str:
    text = str(value).strip()
    if "." in text:
        text = text.rsplit(".", 1)[-1]
    if ":" in text:
        text = text.split(":", 1)[0]
    return text.strip("<> '\"").upper()


def parse_bool_reason(result: Any, operation: str) -> str:
    """Interpret UE 5.8 bool+OutReason reflection without accepting None."""
    if result is None:
        fail(operation + " returned native false (UE Python suppressed OutReason)")
    if isinstance(result, tuple):
        if not result or result[0] is not True:
            fail(operation + " returned an explicit false tuple")
        return str(result[-1]) if len(result) > 1 else "TRUE"
    if result is False:
        fail(operation + " returned false")
    return str(result)


def parse_payload_reason(result: Any, payload_count: int, operation: str) -> Tuple[Any, ...]:
    """Read bool+payload+reason calls in both UE 5.8 and legacy tuple shapes."""
    if result is None:
        fail(operation + " returned native false (UE Python suppressed outputs)")
    if not isinstance(result, tuple):
        if payload_count == 1:
            return (result,)
        fail(operation + " returned an unexpected non-tuple payload")
    values = list(result)
    if values and isinstance(values[0], bool):
        if values.pop(0) is not True:
            fail(operation + " returned explicit native false")
    if len(values) == payload_count + 1 and isinstance(values[-1], str):
        values.pop()
    if len(values) != payload_count:
        fail(operation + " returned {} outputs; expected {}".format(
            len(values), payload_count
        ))
    return tuple(values)


def _read_prop(value: Any, name: str) -> Any:
    try:
        return getattr(value, name)
    except Exception:
        return value.get_editor_property(name)


def class_path(value: Any) -> str:
    return str(value.get_class().get_path_name())


def actor_tags(actor: Any) -> Tuple[str, ...]:
    return tuple(sorted(str(tag) for tag in _read_prop(actor, "tags")))


def actor_label(actor: Any) -> str:
    try:
        return str(actor.get_actor_label())
    except Exception:
        return str(actor.get_name())


def _vector(value: Any) -> Tuple[float, float, float]:
    return float(value.x), float(value.y), float(value.z)


def _rotation(value: Any) -> Tuple[float, float, float]:
    return float(value.pitch), float(value.yaw), float(value.roll)


def png_dimensions(path: Path) -> Optional[Tuple[int, int]]:
    data = path.read_bytes()[:24]
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return None
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def file_ready(path: Path) -> bool:
    return (
        path.is_file()
        and path.stat().st_size >= MIN_SCREENSHOT_BYTES
        and png_dimensions(path) == SCREENSHOT_SIZE
    )


def validate_activation_snapshot(snapshot: Mapping[str, Any]) -> None:
    exact = {
        "game_mode": 1,
        "player_controller": 1,
        "pawn": 1,
        "hud": 1,
        "bootstrap": 1,
        "runtime_coordinator": 1,
        "production": 1,
        "press": 1,
        "body_weld": 1,
        "paint": 1,
        "assembly": 1,
        "presentation": 1,
        "top_bar": 1,
        "flow_strip": 1,
    }
    if snapshot.get("counts") != exact:
        fail("regular PIE exact-one runtime/UI inventory changed")
    expected_classes = {
        "game_mode": GAME_MODE_CLASS,
        "player_controller": PLAYER_CONTROLLER_CLASS,
        "pawn": PAWN_CLASS,
        "hud": HUD_CLASS,
        "bootstrap": BOOTSTRAP_CLASS,
    }
    if snapshot.get("classes") != expected_classes:
        fail("regular PIE GameMode/controller/pawn/HUD/bootstrap class contract changed")
    for flag in (
        "controller_is_primary",
        "controller_possesses_pawn",
        "controller_views_pawn_before_capture",
        "controller_owns_hud",
        "game_mode_shell_valid",
        "game_mode_runtime_backbone_valid",
        "game_mode_binds_bootstrap",
        "game_mode_binds_coordinator",
        "game_mode_binds_production",
        "bootstrap_ready",
        "all_layouts_commissioned",
        "all_departments_commissioned",
        "ledger_valid",
        "runtime_factory_valid",
        "top_bar_visible",
        "flow_strip_visible",
        "widgets_owned_by_player",
        "natural_actor_tick_enabled",
        "automatic_contract_dispatch_disabled",
    ):
        if snapshot.get(flag) is not True:
            fail("regular PIE activation flag failed: " + flag)
    if snapshot.get("route_count") != EXPECTED_ROUTE_COUNT:
        fail("regular PIE route is not exactly 57 physical positions")
    if tuple(snapshot.get("press_route_prefix", ())) != EXPECTED_PRESS_PREFIX:
        fail("regular PIE Press route prefix changed")
    if not str(snapshot.get("topology_id", "")).startswith(EXPECTED_TOPOLOGY_PREFIX):
        fail("regular PIE route is not the V002 topology")
    if tuple(snapshot.get("starter_contract_ids", ())) != EXPECTED_CONTRACT_IDS:
        fail("regular PIE starter-contract ladder changed")
    if snapshot.get("unit_count_before_player_order") != 0:
        fail("capture did not begin from a clean player-order ledger")


def validate_camera_snapshot(snapshot: Mapping[str, Any]) -> None:
    if snapshot.get("class") != CAMERA_CLASS:
        fail("SteamHero role does not belong to an exact CameraActor")
    if snapshot.get("label") != STEAM_HERO_LABEL:
        fail("SteamHero saved CameraActor label changed")
    tags = tuple(snapshot.get("tags", ()))
    if STEAM_HERO_ROLE_TAG not in tags or STEAM_HERO_CAMERA_TAG not in tags:
        fail("SteamHero saved CameraActor role tags changed")
    if sum(tag.startswith("LB.PressShop.OverheadDeck.Camera.SteamHero.") for tag in tags) != 1:
        fail("SteamHero CameraActor has an ambiguous versioned role")
    if "ORTHOGRAPHIC" not in str(snapshot.get("projection", "")).upper():
        fail("SteamHero CameraActor is not orthographic")
    if not _close(snapshot.get("location_cm", ()), STEAM_HERO_LOCATION):
        fail("SteamHero CameraActor location changed")
    if not _close(snapshot.get("rotation_pitch_yaw_roll", ()), STEAM_HERO_ROTATION):
        fail("SteamHero CameraActor is not true overhead")
    if not _close((snapshot.get("ortho_width_cm"),), (STEAM_HERO_ORTHO_WIDTH,)):
        fail("SteamHero CameraActor ortho width changed")
    if not _close((snapshot.get("aspect_ratio"),), (STEAM_HERO_ASPECT,)):
        fail("SteamHero CameraActor aspect ratio changed")
    if snapshot.get("constrain_aspect_ratio") is not True:
        fail("SteamHero CameraActor no longer constrains 16:9")


def validate_natural_press_snapshot(
    snapshot: Mapping[str, Any], *, require_capture_window: bool = True
) -> None:
    if snapshot.get("station_id") != PRESS_STATION_ID:
        fail("evidence unit is not naturally resident at the Press train")
    if snapshot.get("station_cursor") != PRESS_ROUTE_INDEX:
        fail("evidence unit Press cursor changed")
    progress = snapshot.get("progress01")
    if not isinstance(progress, (int, float)) or not math.isfinite(float(progress)):
        fail("evidence unit has no finite natural Press progress")
    minimum = (
        TARGET_PRESS_PROGRESS_MIN
        if require_capture_window
        else S04_ACTIVE_PROGRESS_MIN
    )
    maximum = (
        TARGET_PRESS_PROGRESS_MAX
        if require_capture_window
        else S04_ACTIVE_PROGRESS_MAX
    )
    progress_in_scope = (
        minimum <= float(progress) <= maximum
        if require_capture_window
        else minimum <= float(progress) < maximum
    )
    if not progress_in_scope:
        scope = "reviewed capture window" if require_capture_window else "visible S04 stroke"
        fail("evidence unit is outside the natural " + scope)
    if (
        snapshot.get("started") is not True
        or snapshot.get("completed") is not False
        or snapshot.get("dispatched") is not False
        or snapshot.get("awaiting_quality_result") is not False
    ):
        fail("evidence unit is not in a normal active Press cycle")
    if snapshot.get("machine_id") != TARGET_PRESS_MACHINE:
        fail("natural Press progress did not select S04 Trim")
    if snapshot.get("visible_frame") not in ALLOWED_ACTIVE_FRAMES:
        fail("S04 has no visible descending/contact/rising frame")
    if snapshot.get("visible_frame_count") != 1:
        fail("S04 active frame is missing or ambiguous")
    if snapshot.get("beacon_state") != "RUNNING":
        fail("S04 live beacon is not visibly Running")
    if snapshot.get("bound_visual_layer_count") != EXPECTED_VISUAL_LAYERS:
        fail("live presentation is not bound to all 146 visual layers")
    if snapshot.get("status_beacon_count") != EXPECTED_BEACONS:
        fail("live presentation beacon registry is incomplete")
    if snapshot.get("task_light_count") != EXPECTED_TASK_LIGHTS:
        fail("live presentation task-light registry is incomplete")


PROTECTED_AUTHORITY_FILES: Mapping[Path, str] = {
    PROJECT / "Content/LineBoss/Factory/OneFactory/v001/Maps/"
    "LB_MoorcrossWorks_OneFactory_v001.umap": (
        "f4e97b33cdfb1f242b2c606a16b4caa05b74b298fdf1b1263d4a4c46d50e8d5c"
    ),
    PROJECT / "Content/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPlayable_v001/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadPlayable_v001.umap": (
        "43020cb3ea7d18a49319da68a04ae1b96d5af0d535c705e947f81d5c005ba7ce"
    ),
    PROJECT / "Content/LineBoss/Maps/"
    "LB_PressShop_BuilderAuthorityCandidate_v438.umap": (
        "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8"
    ),
    PROJECT / "Content/LineBoss/Candidates/PressShop/PressShop2126_v002/Maps/"
    "LB_PressShop_2126_Steam_v002.umap": (
        "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0"
    ),
    PROJECT / "Content/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadPresentation_v002/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v002.umap": (
        "58fe57f3af0dfcf4021d6bbcd3a52d7d66de22187b561fb2db41becd83023275"
    ),
    PROJECT / "Content/LineBoss/Candidates/PressShop/"
    "PressShop2126_OverheadCargo_v003/Maps/"
    "LB_MoorcrossWorks_PressShop2126_OverheadCargo_v003.umap": (
        "5eae51f2a7d3e1c72deb4fd455d57a6339dee061840b7d062c5ddf680ab6100f"
    ),
}


def protected_snapshot(extra: Iterable[Path] = ()) -> Dict[str, Dict[str, Any]]:
    paths = set(PROTECTED_AUTHORITY_FILES)
    paths.update(extra)
    for root in (PROJECT / "Config", PROJECT / "Saved/SaveGames"):
        if root.is_dir():
            paths.update(path for path in root.rglob("*") if path.is_file())
    result: Dict[str, Dict[str, Any]] = {}
    for path in sorted(paths, key=lambda value: str(value).lower()):
        key = project_relative(path)
        result[key] = {
            "exists": path.is_file(),
            "bytes": path.stat().st_size if path.is_file() else None,
            "sha256": sha256(path) if path.is_file() else None,
        }
    return result


def verify_protected_authorities() -> None:
    for path, expected in PROTECTED_AUTHORITY_FILES.items():
        if not path.is_file() or sha256(path) != expected:
            fail("protected authority map drift: " + str(path))


def _require_unreal() -> Any:
    if unreal is None:
        fail("live-HUD capture must run inside Unreal Editor Python")
    return unreal


def _actors(world: Any, actor_class: Any) -> list[Any]:
    ue = _require_unreal()
    return list(ue.GameplayStatics.get_all_actors_of_class(world, actor_class))


def _objects_in_world(world: Any, object_class: Any) -> list[Any]:
    ue = _require_unreal()
    return [obj for obj in ue.ObjectIterator(object_class) if obj.get_world() == world]


def _one(rows: Sequence[Any], description: str) -> Any:
    if len(rows) != 1:
        fail("expected exactly one {}, found {}".format(description, len(rows)))
    return rows[0]


def _world_package_name(world: Any) -> str:
    try:
        return str(world.get_outermost().get_name())
    except Exception:
        return str(world.get_path_name()).split(":", 1)[0].split(".", 1)[0]


def world_is_exact_target(world: Any) -> bool:
    package = _world_package_name(world)
    if package == TARGET_MAP:
        return True
    parent, leaf = TARGET_MAP.rsplit("/", 1)
    return re.fullmatch(
        re.escape(parent) + r"/UEDPIE_\d+_" + re.escape(leaf), package
    ) is not None


def camera_contract_snapshot(snapshot: Mapping[str, Any]) -> Dict[str, Any]:
    """Return saved CameraActor fields that must survive PIE unchanged.

    PIE duplicates an actor into a UEDPIE package, so its object path is
    intentionally not a saved-property comparison field.  Everything else is
    part of the frozen v006 camera contract.
    """
    return {key: value for key, value in snapshot.items() if key != "path"}


def saved_camera_contract_changed(
    editor_after: Mapping[str, Any],
    editor_before: Optional[Mapping[str, Any]],
    pie_camera: Optional[Mapping[str, Any]],
) -> bool:
    """Detect saved-camera drift without inventing drift on an early failure.

    ``pie_camera`` remains unset until the capture actually performs its
    temporary view-target switch.  The saved editor actor must still match its
    pre-PIE snapshot in every run; the PIE duplicate is an additional contract
    only after that duplicate was observed.
    """
    if editor_before is None or editor_after != editor_before:
        return True
    return pie_camera is not None and camera_contract_snapshot(
        editor_after
    ) != camera_contract_snapshot(pie_camera)


def _component_visible(component: Any) -> bool:
    try:
        visible = bool(component.is_visible())
    except Exception:
        visible = bool(_read_prop(component, "visible"))
    try:
        hidden = bool(_read_prop(component, "hidden_in_game"))
    except Exception:
        hidden = False
    return visible and not hidden


def _actor_visible(actor: Any) -> bool:
    # UE 5.8 does not expose AActor::IsHidden/GetActorHiddenInGame to Python.
    # ``hidden`` is the supported reflected bHidden property.  The overhead
    # presentation actor applies every runtime state to its static-mesh
    # component as both visibility and hidden_in_game, so component state is
    # the authoritative, fail-observable seam if actor reflection is absent.
    try:
        hidden = bool(_read_prop(actor, "hidden"))
    except Exception:
        hidden = False
    return not hidden and _component_visible(_read_prop(actor, "static_mesh_component"))


def ensure_possessed_pawn_view_target(controller: Any, pawn: Any) -> bool:
    """Restore the player camera when needed, then prove possession and view."""
    if controller.get_controlled_pawn() != pawn:
        return False
    if controller.get_view_target() != pawn:
        controller.set_view_target_with_blend(pawn, 0.0)
    return (
        controller.get_controlled_pawn() == pawn
        and controller.get_view_target() == pawn
    )


def camera_snapshot(camera: Any) -> Dict[str, Any]:
    component = _read_prop(camera, "camera_component")
    return {
        "path": str(camera.get_path_name()),
        "class": class_path(camera),
        "label": actor_label(camera),
        "tags": list(actor_tags(camera)),
        "location_cm": list(_vector(camera.get_actor_location())),
        "rotation_pitch_yaw_roll": list(_rotation(camera.get_actor_rotation())),
        "projection": str(_read_prop(component, "projection_mode")),
        "ortho_width_cm": float(_read_prop(component, "ortho_width")),
        "aspect_ratio": float(_read_prop(component, "aspect_ratio")),
        "constrain_aspect_ratio": bool(_read_prop(component, "constrain_aspect_ratio")),
    }


def find_saved_steam_hero(world: Any) -> Tuple[Any, Dict[str, Any]]:
    ue = _require_unreal()
    cameras = [
        actor
        for actor in _actors(world, ue.CameraActor)
        if STEAM_HERO_ROLE_TAG in actor_tags(actor)
    ]
    camera = _one(cameras, "saved v006 SteamHero CameraActor role")
    snapshot = camera_snapshot(camera)
    validate_camera_snapshot(snapshot)
    return camera, snapshot


def widget_snapshot(widget: Any, controller: Any) -> Dict[str, Any]:
    visibility = normalise_name(widget.get_visibility())
    return {
        "path": str(widget.get_path_name()),
        "class": class_path(widget),
        "in_viewport": bool(widget.is_in_viewport()),
        "visibility": visibility,
        "owning_player_matches": widget.get_owning_player() == controller,
    }


def widget_is_paint_visible(snapshot: Mapping[str, Any]) -> bool:
    """True only when a viewport widget is in a Slate paint-visible state."""
    return bool(snapshot.get("in_viewport")) and normalise_name(
        snapshot.get("visibility", "")
    ) in PAINT_VISIBLE_WIDGET_STATES


def capture_activation(world: Any) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    ue = _require_unreal()
    game_mode = _one(_actors(world, ue.LBOneFactoryGameMode), "OneFactory GameMode")
    controller = _one(
        _actors(world, ue.LBOneFactoryPlayerController), "OneFactory player controller"
    )
    pawn = _one(_actors(world, ue.LBManagementPawn), "management pawn")
    hud = _one(_actors(world, ue.LBOneFactoryProductionHUD), "production HUD")
    bootstrap = _one(_actors(world, ue.LBOneFactoryBootstrap), "OneFactory bootstrap")
    coordinator = _one(
        _actors(world, ue.LBOneFactoryRuntimeCoordinator), "runtime coordinator"
    )
    production = _one(
        _actors(world, ue.LBOneFactoryProductionFlowAuthority),
        "production flow authority",
    )
    presentation = _one(
        _actors(world, ue.LBPressShopOverheadPresentationActor),
        "overhead presentation adapter",
    )
    layout_rows = {
        "press": _actors(world, ue.LBOneFactoryPressStarterLayoutAuthority),
        "body_weld": _actors(world, ue.LBOneFactoryBodyWeldStarterLayoutAuthority),
        "paint": _actors(world, ue.LBOneFactoryPaintStarterLayoutAuthority),
        "assembly": _actors(world, ue.LBOneFactoryAssemblyStarterLayoutAuthority),
    }
    top_bar = _one(
        _objects_in_world(world, ue.LBOneFactoryTopBarWidget), "TopBar UMG widget"
    )
    flow_strip = _one(
        _objects_in_world(world, ue.LBOneFactoryFlowStripWidget), "FlowStrip UMG widget"
    )
    primary = ue.GameplayStatics.get_player_controller(world, 0)
    route, topology = parse_payload_reason(
        coordinator.get_configured_station_route(), 2, "GetConfiguredStationRoute"
    )
    route = list(route)
    route_ids = [normalise_name(_read_prop(step, "station_id")) for step in route]
    indices = [int(_read_prop(step, "route_index")) for step in route]
    if indices != list(range(EXPECTED_ROUTE_COUNT)):
        fail("57-position route indices are not contiguous")
    parse_bool_reason(coordinator.validate_runtime_factory(), "ValidateRuntimeFactory")
    ledger = production.capture_ledger()
    parse_bool_reason(
        ue.LBOneFactoryProductionFlowLibrary.validate_ledger(ledger),
        "ValidateProductionLedger",
    )
    commissioning = _read_prop(ledger, "commissioning")
    department_flags = {
        "press": bool(_read_prop(commissioning, "press_commissioned")),
        "body": bool(_read_prop(commissioning, "body_commissioned")),
        "paint": bool(_read_prop(commissioning, "paint_commissioned")),
        "assembly": bool(_read_prop(commissioning, "assembly_commissioned")),
    }
    layout_flags = {
        key: bool(_read_prop(_one(rows, key + " layout authority").capture_layout(), "commissioned"))
        for key, rows in layout_rows.items()
    }
    top = widget_snapshot(top_bar, controller)
    flow = widget_snapshot(flow_strip, controller)
    counts = {
        "game_mode": 1,
        "player_controller": 1,
        "pawn": 1,
        "hud": 1,
        "bootstrap": 1,
        "runtime_coordinator": 1,
        "production": 1,
        **{key: len(rows) for key, rows in layout_rows.items()},
        "presentation": 1,
        "top_bar": 1,
        "flow_strip": 1,
    }
    snapshot = {
        "counts": counts,
        "classes": {
            "game_mode": class_path(game_mode),
            "player_controller": class_path(controller),
            "pawn": class_path(pawn),
            "hud": class_path(hud),
            "bootstrap": class_path(bootstrap),
        },
        "controller_is_primary": controller == primary,
        "controller_possesses_pawn": controller.get_controlled_pawn() == pawn,
        "controller_views_pawn_before_capture": controller.get_view_target() == pawn,
        "controller_owns_hud": controller.get_hud() == hud,
        "game_mode_shell_valid": bool(game_mode.has_valid_one_factory_shell()),
        "game_mode_runtime_backbone_valid": bool(game_mode.has_valid_runtime_backbone()),
        "game_mode_binds_bootstrap": game_mode.get_one_factory_bootstrap() == bootstrap,
        "game_mode_binds_coordinator": (
            game_mode.get_one_factory_runtime_coordinator() == coordinator
        ),
        "game_mode_binds_production": (
            game_mode.get_one_factory_production_flow() == production
        ),
        "bootstrap_ready": (
            bool(bootstrap.has_valid_shell())
            and bool(bootstrap.was_validation_attempted())
            and normalise_name(bootstrap.get_bootstrap_state()) == "READY"
        ),
        "all_layouts_commissioned": all(layout_flags.values()),
        "layout_commissioned": layout_flags,
        "all_departments_commissioned": all(department_flags.values()),
        "department_commissioned": department_flags,
        "ledger_valid": True,
        "runtime_factory_valid": True,
        "route_count": len(route),
        "press_route_prefix": route_ids[:7],
        "topology_id": normalise_name(topology),
        "starter_contract_ids": sorted(
            normalise_name(_read_prop(row, "contract_id"))
            for row in list(_read_prop(ledger, "contracts"))
        ),
        "unit_count_before_player_order": len(list(_read_prop(ledger, "units"))),
        "top_bar_visible": widget_is_paint_visible(top),
        "flow_strip_visible": widget_is_paint_visible(flow),
        "widgets_owned_by_player": (
            top["owning_player_matches"] and flow["owning_player_matches"]
        ),
        "top_bar": top,
        "flow_strip": flow,
        "natural_actor_tick_enabled": bool(
            _read_prop(coordinator, "advance_started_vehicles_on_actor_tick")
        ),
        "automatic_contract_dispatch_disabled": not bool(
            _read_prop(coordinator, "auto_dispatch_open_contracts")
        ),
        "presentation_enabled": bool(presentation.is_presentation_enabled()),
    }
    validate_activation_snapshot(snapshot)
    if snapshot["presentation_enabled"] is not True:
        fail("overhead presentation adapter is disabled")
    objects = {
        "game_mode": game_mode,
        "controller": controller,
        "pawn": pawn,
        "hud": hud,
        "bootstrap": bootstrap,
        "coordinator": coordinator,
        "production": production,
        "presentation": presentation,
        "top_bar": top_bar,
        "flow_strip": flow_strip,
    }
    return snapshot, objects


def status_snapshot(coordinator: Any, unit_id: Any) -> Dict[str, Any]:
    status = parse_payload_reason(
        coordinator.get_vehicle_runtime_status(unit_id), 1,
        "GetVehicleRuntimeStatus",
    )[0]
    return {
        "unit_id": normalise_name(_read_prop(status, "unit_id")),
        "station_id": normalise_name(_read_prop(status, "current_station_id")),
        "station_cursor": int(_read_prop(status, "station_cursor")),
        "stage": normalise_name(_read_prop(status, "stage")),
        "progress01": float(_read_prop(status, "normalized_cycle_progress")),
        "cycle_duration_seconds": float(_read_prop(status, "cycle_duration_seconds")),
        "started": bool(_read_prop(status, "started")),
        "at_quality_gate": bool(_read_prop(status, "at_quality_gate")),
        "awaiting_quality_result": bool(_read_prop(status, "awaiting_quality_result")),
        "completed": bool(_read_prop(status, "completed")),
        "dispatched": bool(_read_prop(status, "dispatched")),
    }


def live_press_snapshot(
    world: Any,
    coordinator: Any,
    presentation: Any,
    unit_id: Any,
    *,
    require_capture_window: bool = True,
) -> Dict[str, Any]:
    ue = _require_unreal()
    result = status_snapshot(coordinator, unit_id)
    visible_frames = []
    for layer in _actors(world, ue.LBPressShopOverheadVisualLayerActor):
        if (
            normalise_name(_read_prop(layer, "machine_id")) == TARGET_PRESS_MACHINE
            and normalise_name(_read_prop(layer, "layer_role")) == "FRAME_STATE"
            and normalise_name(_read_prop(layer, "state_id")) in ALLOWED_ACTIVE_FRAMES
            and _actor_visible(layer)
        ):
            visible_frames.append(normalise_name(_read_prop(layer, "state_id")))
    beacon = presentation.get_status_beacon(ue.Name(TARGET_PRESS_MACHINE))
    if beacon is None:
        fail("live presentation has no S04 status beacon")
    result.update({
        "machine_id": TARGET_PRESS_MACHINE,
        "visible_frame": visible_frames[0] if len(visible_frames) == 1 else None,
        "visible_frame_count": len(visible_frames),
        "beacon_state": normalise_name(beacon.get_status()),
        "bound_visual_layer_count": int(presentation.get_bound_visual_layer_count()),
        "status_beacon_count": int(presentation.get_status_beacon_count()),
        "task_light_count": int(presentation.get_task_light_count()),
    })
    validate_natural_press_snapshot(
        result, require_capture_window=require_capture_window
    )
    return result


def current_unit_ids(production: Any) -> Tuple[str, ...]:
    ledger = production.capture_ledger()
    return tuple(sorted(
        normalise_name(_read_prop(row, "unit_id"))
        for row in list(_read_prop(ledger, "units"))
    ))


def ui_snapshot(objects: Mapping[str, Any]) -> Dict[str, Any]:
    controller = objects["controller"]
    top = widget_snapshot(objects["top_bar"], controller)
    flow = widget_snapshot(objects["flow_strip"], controller)
    if (
        not widget_is_paint_visible(top)
        or not widget_is_paint_visible(flow)
        or not top["owning_player_matches"]
        or not flow["owning_player_matches"]
    ):
        fail("TopBar/FlowStrip was not visibly player-owned at capture time")
    return {"top_bar": top, "flow_strip": flow}


def dirty_packages() -> Dict[str, list[str]]:
    ue = _require_unreal()
    return {
        "content": sorted(str(value) for value in ue.EditorLoadingAndSavingUtils.get_dirty_content_packages()),
        "maps": sorted(str(value) for value in ue.EditorLoadingAndSavingUtils.get_dirty_map_packages()),
    }


class LiveHudCaptureRunner:
    def __init__(
        self,
        stamp: str,
        run_dir: Path,
        screenshot: Path,
        receipt_path: Path,
        map_sha: str,
        receipt_sha: str,
        install_contract: Mapping[str, Any],
        protected_before: Mapping[str, Any],
        dirty_before_pie: Mapping[str, Any],
    ) -> None:
        ue = _require_unreal()
        self.stamp = stamp
        self.run_dir = run_dir
        self.screenshot = screenshot
        self.receipt_path = receipt_path
        self.map_sha = map_sha
        self.receipt_sha = receipt_sha
        self.install_contract = dict(install_contract)
        self.protected_before = dict(protected_before)
        self.dirty_before_pie = dict(dirty_before_pie)
        self.levels = ue.get_editor_subsystem(ue.LevelEditorSubsystem)
        self.editor_worlds = ue.get_editor_subsystem(ue.UnrealEditorSubsystem)
        if self.levels is None or self.editor_worlds is None:
            fail("required Unreal editor subsystems are unavailable")
        self.started = time.monotonic()
        self.phase_started = self.started
        self.phase = "WAIT_WORLD"
        self.game_world_seen: Optional[float] = None
        self.activation_started: Optional[float] = None
        self.order_started: Optional[float] = None
        self.press_wait_started: Optional[float] = None
        self.capture_started: Optional[float] = None
        self.resize_last_attempt = 0.0
        self.resize_exact_since: Optional[float] = None
        self.handle: Any = None
        self.objects: Dict[str, Any] = {}
        self.unit_id: Optional[Any] = None
        self.before_unit_ids: Tuple[str, ...] = ()
        self.camera: Optional[Any] = None
        self.camera_snapshot: Optional[Dict[str, Any]] = None
        self.finished = False
        self.final_status_requested = FAIL_STATUS
        self.final_detail = ""
        self.payload: Dict[str, Any] = {
            "schema": OUTPUT_SCHEMA,
            "status": "RUNNING",
            "started_utc": datetime.now(timezone.utc).isoformat(),
            "stamp": stamp,
            "target_map": TARGET_MAP,
            "target_map_sha256_before": map_sha,
            "install_receipt": project_relative(INSTALL_RECEIPT),
            "install_receipt_sha256_before": receipt_sha,
            "validator_script": project_relative(SCRIPT_FILE),
            "validator_script_sha256": sha256(SCRIPT_FILE),
            "run_directory": project_relative(run_dir),
            "screenshot": None,
            "install_contract": dict(install_contract),
            "regular_pie": True,
            "simulated_editor_session": False,
            "real_rhi": True,
            "scene_capture_2d_used": False,
            "coordinator_step_or_freeze_used": False,
            "player_place_order_call_count": 0,
            "native_ui_screenshot_request_call_count": 0,
            "map_save_calls": 0,
            "content_save_calls": 0,
            "import_calls": 0,
            "build_calls": 0,
            "cook_calls": 0,
            "visibility_or_actor_property_mutations": 0,
            "runtime": {},
            "protected_before": dict(protected_before),
            "protected_after": None,
            "dirty_packages_before_pie": dict(dirty_before_pie),
            "dirty_packages_after_pie": None,
            "failures": [],
        }

    def log_failure(self, message: str) -> None:
        if message not in self.payload["failures"]:
            self.payload["failures"].append(message)
        _require_unreal().log_error("PRESSSHOP_2126_V006_LIVE_HUD_CAPTURE_FAIL " + message)

    def request_end(self, status: str, detail: str = "") -> None:
        if self.phase in ("ENDING_PIE", "FINALIZING"):
            return
        self.final_status_requested = status
        self.final_detail = detail
        self.phase = "ENDING_PIE"
        self.phase_started = time.monotonic()
        self.levels.editor_request_end_play()

    def fail_run(self, message: str) -> None:
        self.log_failure(message)
        try:
            controller = self.objects.get("controller")
            pawn = self.objects.get("pawn")
            if controller is not None and pawn is not None:
                restored = ensure_possessed_pawn_view_target(controller, pawn)
                self.payload["runtime"]["view_target_restored_to_possessed_pawn"] = restored
                if not restored:
                    self.log_failure(
                        "failure-path player view/possession could not be restored"
                    )
        except Exception as exc:
            self.log_failure("failure-path pawn view restoration also failed: " + repr(exc))
        self.request_end(FAIL_STATUS, message)

    def request_resize(self, world: Any, now: float) -> None:
        ue = _require_unreal()
        result = ue.LBOneFactoryCaptureBridge.resize_pie_window_for_game_widget_size(
            world, SCREENSHOT_SIZE[0], SCREENSHOT_SIZE[1]
        )
        size = int(result.x), int(result.y)
        if size[0] <= 0 or size[1] <= 0:
            fail("native PIE game-widget/window resize request was refused")
        self.resize_last_attempt = now

    def exact_ui_size(self, world: Any, now: float, retry=True) -> bool:
        ue = _require_unreal()
        size = ue.LBOneFactoryCaptureBridge.get_pie_game_widget_draw_size(world)
        current = int(size.x), int(size.y)
        if current != SCREENSHOT_SIZE:
            self.resize_exact_since = None
            if retry and now - self.resize_last_attempt >= 0.75:
                self.request_resize(world, now)
            return False
        if self.resize_exact_since is None:
            self.resize_exact_since = now
            return False
        return now - self.resize_exact_since >= 0.5

    def begin_order(self, world: Any, now: float) -> None:
        self.before_unit_ids = current_unit_ids(self.objects["production"])
        if self.before_unit_ids:
            fail("regular PIE was not empty before the player order")
        self.request_resize(world, now)
        self.payload["runtime"]["player_order_seam"] = (
            "ALBOneFactoryPlayerController.PlaceOrder / + NEW ORDER"
        )
        self.payload["player_place_order_call_count"] = 1
        self.objects["controller"].place_order()
        self.order_started = now
        self.phase = "WAIT_ORDER"
        self.phase_started = now

    def find_order(self, now: float) -> None:
        after = current_unit_ids(self.objects["production"])
        created = sorted(set(after) - set(self.before_unit_ids))
        if len(created) == 1 and len(after) == 1:
            self.unit_id = _require_unreal().Name(created[0])
            initial = status_snapshot(self.objects["coordinator"], self.unit_id)
            if initial["unit_id"] != created[0] or not initial["started"]:
                fail("PlaceOrder did not create one started canonical unit")
            self.payload["runtime"]["player_order"] = {
                "before_unit_ids": list(self.before_unit_ids),
                "after_unit_ids": list(after),
                "created_unit_id": created[0],
                "initial_status": initial,
            }
            self.press_wait_started = now
            self.phase = "WAIT_NATURAL_PRESS"
            self.phase_started = now
            return
        if self.order_started is not None and now - self.order_started > ORDER_TIMEOUT_SECONDS:
            fail("PlaceOrder did not create exactly one started unit: {!r}".format(after))

    def wait_natural_press(self, world: Any, now: float) -> None:
        if self.unit_id is None:
            fail("natural Press wait has no player-created UnitId")
        if self.press_wait_started is not None and now - self.press_wait_started > NATURAL_PRESS_TIMEOUT_SECONDS:
            fail("player-created unit did not naturally reach the reviewed S04 window")
        self.exact_ui_size(world, now, retry=True)
        status = status_snapshot(self.objects["coordinator"], self.unit_id)
        if status["completed"] or status["dispatched"]:
            fail("player-created unit passed the Press train without a capture window")
        if status["station_id"] != PRESS_STATION_ID:
            return
        progress = float(status["progress01"])
        if progress > TARGET_PRESS_PROGRESS_MAX:
            fail("natural S04 capture window was missed at progress {:.4f}".format(progress))
        if progress < TARGET_PRESS_PROGRESS_MIN:
            return
        if not self.exact_ui_size(world, now, retry=False):
            fail("PIE game widget was not stably 1920x1080 at the natural capture window")
        natural = live_press_snapshot(
            world, self.objects["coordinator"], self.objects["presentation"], self.unit_id
        )
        self.payload["runtime"]["natural_press_state_before_view_switch"] = natural
        self.payload["runtime"]["ui_before_view_switch"] = ui_snapshot(self.objects)
        camera, snapshot = find_saved_steam_hero(world)
        if self.objects["controller"].get_view_target() != self.objects["pawn"]:
            fail("player view target left the possessed pawn before the reviewed switch")
        self.camera = camera
        self.camera_snapshot = snapshot
        self.objects["controller"].set_view_target_with_blend(camera, 0.0)
        self.phase = "WAIT_CAMERA_VIEW"
        self.phase_started = now

    def start_ui_capture(self, world: Any, now: float) -> None:
        ue = _require_unreal()
        if self.screenshot.exists():
            fail("refusing to overwrite live-HUD screenshot: " + str(self.screenshot))

        # finish_loading_before_screenshot() may pump Slate while this post-tick
        # callback is still on the stack.  Publish an in-flight phase before the
        # flush so a nested post-tick cannot submit the same global screenshot
        # request again and misread the first request as a bridge refusal.
        if self.phase != "WAIT_CAMERA_VIEW":
            fail("live-HUD capture request entered from unexpected phase " + self.phase)
        self.phase = "REQUESTING_CAPTURE"
        self.phase_started = now
        self.payload["runtime"]["capture_request_phase_guard"] = {
            "phase": self.phase,
            "set_before_loading_flush": True,
        }
        ue.AutomationLibrary.finish_loading_before_screenshot()
        post_flush_size_value = (
            ue.LBOneFactoryCaptureBridge.get_pie_game_widget_draw_size(world)
        )
        post_flush_size = (
            int(post_flush_size_value.x),
            int(post_flush_size_value.y),
        )
        self.payload["runtime"]["game_widget_draw_size_after_loading_flush"] = list(
            post_flush_size
        )
        if post_flush_size != SCREENSHOT_SIZE:
            fail(
                "PIE game widget changed size during screenshot loading flush: "
                + repr(post_flush_size)
            )
        request_count = int(
            self.payload.get("native_ui_screenshot_request_call_count", 0)
        ) + 1
        self.payload["native_ui_screenshot_request_call_count"] = request_count
        if request_count != 1:
            fail("native restricted UI screenshot request call count was not exactly one")
        accepted = ue.LBOneFactoryCaptureBridge.request_pie_restricted_ui_screenshot(
            world, str(self.screenshot), SCREENSHOT_SIZE[0], SCREENSHOT_SIZE[1]
        )
        self.payload["runtime"]["native_capture_request_accepted"] = bool(accepted)
        if not accepted:
            fail("native restricted 1920x1080 UI screenshot request was refused")
        self.capture_started = time.monotonic()
        self.phase = "WAIT_CAPTURE"
        self.phase_started = self.capture_started

    def finish_capture(self, world: Any, now: float) -> None:
        if self.capture_started is None:
            fail("capture wait has no request timestamp")
        if not file_ready(self.screenshot):
            if now - self.capture_started > CAPTURE_TIMEOUT_SECONDS:
                fail("native restricted UI screenshot did not become ready")
            return
        if self.objects["controller"].get_view_target() != self.camera:
            fail("SteamHero CameraActor was not still the view target when capture completed")
        final_press = live_press_snapshot(
            world,
            self.objects["coordinator"],
            self.objects["presentation"],
            self.unit_id,
            require_capture_window=False,
        )
        self.payload["runtime"]["natural_press_state_at_capture_completion"] = final_press
        self.payload["runtime"]["ui_at_capture"] = ui_snapshot(self.objects)
        self.payload["runtime"]["steam_hero_camera"] = dict(self.camera_snapshot or {})
        self.payload["runtime"]["view_target_at_capture"] = str(
            self.objects["controller"].get_view_target().get_path_name()
        )
        self.payload["screenshot"] = {
            "path": project_relative(self.screenshot),
            "sha256": sha256(self.screenshot),
            "bytes": self.screenshot.stat().st_size,
            "dimensions": list(png_dimensions(self.screenshot) or ()),
            "source": (
                "LBOneFactoryCaptureBridge.request_pie_restricted_ui_screenshot"
            ),
            "show_ui": True,
            "restrict_to_game_viewport": True,
            "scene_capture_2d": False,
            "high_resolution_editor_capture": False,
            "real_rhi": True,
        }
        self.objects["controller"].set_view_target_with_blend(
            self.objects["pawn"], 0.0
        )
        self.phase = "WAIT_VIEW_RESTORE"
        self.phase_started = now

    def finalize(self) -> None:
        if self.finished:
            return
        self.finished = True
        self.phase = "FINALIZING"
        try:
            if sha256(TARGET_FILE) != self.map_sha:
                self.payload["failures"].append("v006 target map changed during regular PIE")
            if sha256(INSTALL_RECEIPT) != self.receipt_sha:
                self.payload["failures"].append("v006 install receipt changed during regular PIE")
            protected_after = protected_snapshot((TARGET_FILE, INSTALL_RECEIPT))
            self.payload["protected_after"] = protected_after
            if protected_after != self.protected_before:
                self.payload["failures"].append(
                    "protected maps/config/savegames/target evidence changed during capture"
                )
            dirty_after = dirty_packages()
            self.payload["dirty_packages_after_pie"] = dirty_after
            if dirty_after != self.dirty_before_pie:
                self.payload["failures"].append(
                    "editor dirty-package inventory changed during read-only capture"
                )
            editor_world = self.editor_worlds.get_editor_world()
            if editor_world is None or not world_is_exact_target(editor_world):
                self.payload["failures"].append(
                    "editor did not return to the exact v006 map after PIE"
                )
            else:
                _camera, editor_camera = find_saved_steam_hero(editor_world)
                editor_pre_pie = self.payload["runtime"].get(
                    "saved_steam_hero_editor_pre_pie"
                )
                if saved_camera_contract_changed(
                    editor_camera, editor_pre_pie, self.camera_snapshot
                ):
                    self.payload["failures"].append(
                        "saved SteamHero CameraActor changed during temporary PIE view targeting"
                    )
            if self.payload.get("screenshot") is None or not file_ready(self.screenshot):
                self.payload["failures"].append("required 1920x1080 live-HUD screenshot is absent")
            elif sha256(self.screenshot) != self.payload["screenshot"]["sha256"]:
                self.payload["failures"].append("live-HUD screenshot changed before finalization")
            if self.payload["player_place_order_call_count"] != 1:
                self.payload["failures"].append("capture did not use exactly one player PlaceOrder")
            if self.payload["runtime"].get("view_target_restored_to_possessed_pawn") is not True:
                self.payload["failures"].append("player pawn view target was not proven restored")
        except Exception as exc:
            self.payload["failures"].append(
                "finalization failed: {}: {}".format(type(exc).__name__, exc)
            )
            self.payload["finalization_traceback"] = traceback.format_exc()
        self.payload["target_map_sha256_after"] = (
            sha256(TARGET_FILE) if TARGET_FILE.is_file() else None
        )
        self.payload["install_receipt_sha256_after"] = (
            sha256(INSTALL_RECEIPT) if INSTALL_RECEIPT.is_file() else None
        )
        self.payload["detail"] = self.final_detail
        self.payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
        self.payload["status"] = (
            PASS_STATUS
            if self.final_status_requested == PASS_STATUS and not self.payload["failures"]
            else FAIL_STATUS
        )
        self.payload["steam_visual_quality_human_approved"] = False
        self.payload["honest_status"] = (
            "Regular-PIE, real-player, native-UMG and live natural Press-state capture "
            "evidence only. Human Steam-art approval, packaged behavior, performance and "
            "shipping readiness are not claimed."
        )
        write_json_new(self.receipt_path, self.payload)
        if self.handle is not None:
            try:
                _require_unreal().unregister_slate_post_tick_callback(self.handle)
            except Exception:
                pass
            self.handle = None
        _require_unreal().EditorPythonScripting.set_keep_python_script_alive(False)
        if self.payload["status"] == PASS_STATUS:
            _require_unreal().log(
                "PRESSSHOP_2126_V006_LIVE_HUD_CAPTURE_PASS screenshot={} receipt={}".format(
                    self.screenshot, self.receipt_path
                )
            )
        else:
            _require_unreal().log_error(
                "PRESSSHOP_2126_V006_LIVE_HUD_CAPTURE_FAIL receipt=" + str(self.receipt_path)
            )
        _require_unreal().SystemLibrary.quit_editor()

    def tick(self, _delta_seconds: float) -> None:
        if self.finished:
            return
        ue = _require_unreal()
        now = time.monotonic()
        world = self.editor_worlds.get_game_world()
        if self.phase == "ENDING_PIE":
            if world is None or now - self.phase_started > 20.0:
                self.finalize()
            return
        if self.phase == "FINALIZING":
            return
        if now - self.started > TOTAL_TIMEOUT_SECONDS:
            self.fail_run("timed out in live-HUD phase " + self.phase)
            return
        if world is None:
            if now - self.started > GAME_WORLD_TIMEOUT_SECONDS:
                self.fail_run("regular PIE game world did not appear")
            return
        try:
            if not world_is_exact_target(world):
                fail("regular PIE started a different world: " + _world_package_name(world))
            if self.game_world_seen is None:
                self.game_world_seen = now
                self.activation_started = now
            if self.phase == "WAIT_WORLD":
                if now - self.game_world_seen < 2.0:
                    return
                try:
                    activation, objects = capture_activation(world)
                except CaptureGuardError as exc:
                    if self.activation_started is not None and now - self.activation_started < ACTIVATION_TIMEOUT_SECONDS:
                        return
                    raise exc
                self.payload["runtime"]["activation"] = activation
                self.objects = objects
                _editor_camera, editor_camera = find_saved_steam_hero(world)
                self.payload["runtime"]["saved_steam_hero_before_order"] = editor_camera
                self.begin_order(world, now)
                return
            if self.phase == "WAIT_ORDER":
                self.find_order(now)
                return
            if self.phase == "WAIT_NATURAL_PRESS":
                self.wait_natural_press(world, now)
                return
            if self.phase == "WAIT_CAMERA_VIEW":
                if now - self.phase_started < 0.15:
                    return
                if self.objects["controller"].get_view_target() != self.camera:
                    fail("controller did not accept the exact saved SteamHero CameraActor")
                if not self.exact_ui_size(world, now, retry=False):
                    fail("PIE game widget lost exact 1920x1080 size before capture")
                # Recheck natural status after the view switch; no coordinator or
                # presentation method is invoked to manufacture this frame.
                natural = live_press_snapshot(
                    world,
                    self.objects["coordinator"],
                    self.objects["presentation"],
                    self.unit_id,
                    require_capture_window=False,
                )
                self.payload["runtime"]["natural_press_state_at_capture_request"] = natural
                self.payload["runtime"]["ui_at_capture_request"] = ui_snapshot(self.objects)
                self.start_ui_capture(world, now)
                return
            if self.phase == "REQUESTING_CAPTURE":
                # A synchronous loading flush can pump this Slate callback
                # re-entrantly.  The outer call owns the one native request.
                return
            if self.phase == "WAIT_CAPTURE":
                self.finish_capture(world, now)
                return
            if self.phase == "WAIT_VIEW_RESTORE":
                if now - self.phase_started < 0.15:
                    return
                controller = self.objects["controller"]
                pawn = self.objects["pawn"]
                if not ensure_possessed_pawn_view_target(controller, pawn):
                    fail("possessed management pawn was not restored as view target")
                self.payload["runtime"]["view_target_restored_to_possessed_pawn"] = True
                self.request_end(PASS_STATUS)
                return
        except Exception as exc:
            self.fail_run("{}: {}".format(type(exc).__name__, exc))


def write_pre_pie_failure(
    receipt_path: Path,
    stamp: str,
    message: str,
    map_sha: Optional[str],
    receipt_sha: Optional[str],
) -> None:
    write_json_new(receipt_path, {
        "schema": OUTPUT_SCHEMA,
        "status": FAIL_STATUS,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "finished_utc": datetime.now(timezone.utc).isoformat(),
        "stamp": stamp,
        "target_map": TARGET_MAP,
        "target_map_sha256_before": map_sha,
        "install_receipt_sha256_before": receipt_sha,
        "validator_script": project_relative(SCRIPT_FILE),
        "validator_script_sha256": sha256(SCRIPT_FILE),
        "regular_pie": False,
        "failures": [message],
        "steam_visual_quality_human_approved": False,
    })


def main() -> None:
    ue = _require_unreal()
    command_line = str(ue.SystemLibrary.get_command_line())
    if "-nullrhi" in command_line.lower():
        fail("live-HUD capture refuses NullRHI")
    map_sha, receipt_sha = required_guard_hashes(os.environ)
    stamp, run_dir, screenshot, receipt_path = create_run_paths(os.environ)
    runner: Optional[LiveHudCaptureRunner] = None
    try:
        _receipt, install_contract = load_guarded_install_receipt(map_sha, receipt_sha)
        verify_protected_authorities()
        protected_before = protected_snapshot((TARGET_FILE, INSTALL_RECEIPT))
        if not ue.EditorLoadingAndSavingUtils.load_map(TARGET_MAP):
            fail("could not load exact v006 candidate map")
        editor_world = ue.get_editor_subsystem(ue.UnrealEditorSubsystem).get_editor_world()
        if editor_world is None or not world_is_exact_target(editor_world):
            fail("editor did not load the exact v006 candidate map")
        _camera, editor_camera = find_saved_steam_hero(editor_world)
        dirty_before = dirty_packages()
        if dirty_before != {"content": [], "maps": []}:
            fail("fresh v006 map has dirty packages before regular PIE: {!r}".format(dirty_before))
        runner = LiveHudCaptureRunner(
            stamp, run_dir, screenshot, receipt_path, map_sha, receipt_sha,
            install_contract, protected_before, dirty_before,
        )
        runner.payload["command_line"] = command_line
        runner.payload["runtime"]["saved_steam_hero_editor_pre_pie"] = editor_camera
        ue.EditorPythonScripting.set_keep_python_script_alive(True)
        runner.handle = ue.register_slate_post_tick_callback(runner.tick)
        # Normal PIE creates the configured GameMode, native controller,
        # possessed management pawn, ProductionHUD and its native UMG widgets.
        runner.levels.editor_request_begin_play()
    except Exception as exc:
        message = "pre-PIE {}: {}".format(type(exc).__name__, exc)
        ue.log_error("PRESSSHOP_2126_V006_LIVE_HUD_CAPTURE_FAIL " + message)
        if runner is not None:
            runner.log_failure(message)
            runner.final_status_requested = FAIL_STATUS
            runner.final_detail = message
            runner.finalize()
        else:
            write_pre_pie_failure(receipt_path, stamp, message, map_sha, receipt_sha)
            ue.EditorPythonScripting.set_keep_python_script_alive(False)
            ue.SystemLibrary.quit_editor()


if __name__ == "__main__":
    main()
