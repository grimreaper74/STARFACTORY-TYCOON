"""Independent fresh-process real-RHI/PIE gate for OneFactory v002.

The validator never saves a map.  It fresh-loads the new successor, proves the
preserved shell contract, starts the actual OneFactory GameMode/pawn/HUD, waits
for a usable RecastNavMesh, exercises five canonical routes, transiently builds
the native Press starter, and captures five scene frames plus one native-UMG
frame at 1920x1080.  The exact Paint-B luminance/clipping envelope and a
top-left warning-red gate are measured directly from the PNG bytes.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import traceback
from typing import Any

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
SCRIPTS = ROOT / "Scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import one_factory_visual_navigation_v002_contract as contract
import one_factory_visual_navigation_v002_unreal as gate


SCRIPT_FILE = ROOT / "Scripts/validate_one_factory_visual_navigation_v002.py"
SOURCE_FILE = ROOT / contract.SOURCE_MAP_RELATIVE
TARGET_FILE = ROOT / contract.TARGET_MAP_RELATIVE
BUILD_RECEIPT = ROOT / contract.BUILD_RECEIPT_RELATIVE
RECEIPT = ROOT / contract.VALIDATION_RECEIPT_RELATIVE
FAILURE_RECEIPT = RECEIPT.with_name(
    "one_factory_visual_navigation_validation_v002_failed.json"
)
CAPTURE_DIR = ROOT / contract.SCREENSHOT_RELATIVE_ROOT

LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
EDITOR_WORLDS = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
ACTORS_API = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def frozen_anchor_snapshot() -> dict[str, str]:
    rows = {}
    for name, expected in contract.STATIC_PROTECTED_HASHES.items():
        path = ROOT / name
        if not path.is_file():
            raise RuntimeError(f"Protected anchor is absent: {name}")
        actual = contract.sha256(path)
        if actual != expected:
            raise RuntimeError(
                f"Protected anchor drift: {name} {actual} != {expected}"
            )
        rows[name] = actual
    return rows


def guarded_workspace_snapshot() -> dict[str, str]:
    rows: dict[str, str] = {}
    patterns = (
        (ROOT / "Source", "*"),
        (ROOT / "Config", "*"),
        (ROOT / "Saved/SaveGames", "*.sav"),
        (ROOT / "Content", "*"),
    )
    target = TARGET_FILE.resolve()
    for root, pattern in patterns:
        if not root.exists():
            continue
        for path in sorted((p for p in root.rglob(pattern) if p.is_file()), key=str):
            if path.resolve() == target:
                continue
            rows[relative(path)] = contract.sha256(path)
    return rows


def actors_of(world: Any, actor_class: Any) -> list[Any]:
    return list(unreal.GameplayStatics.get_all_actors_of_class(world, actor_class))


def require_runtime_one(world: Any, actor_class: Any, description: str) -> Any:
    rows = actors_of(world, actor_class)
    if len(rows) != 1:
        raise RuntimeError(
            f"Expected exactly one runtime {description}, found {len(rows)}"
        )
    return rows[0]


def runtime_by_label(world: Any) -> dict[str, list[Any]]:
    rows: dict[str, list[Any]] = {}
    for actor in actors_of(world, unreal.Actor):
        rows.setdefault(actor.get_actor_label(), []).append(actor)
    return rows


def get_builder(world: Any) -> Any:
    rows = [
        obj
        for obj in unreal.ObjectIterator(unreal.LBOneFactoryPlayerBuilderSubsystem)
        if obj.get_world() == world
    ]
    if len(rows) != 1:
        raise RuntimeError(
            f"Expected one OneFactory player-builder subsystem, found {len(rows)}"
        )
    return rows[0]


def file_ready(path: Path) -> bool:
    return path.is_file() and path.stat().st_size >= contract.MINIMUM_SCREENSHOT_BYTES


def preflight() -> dict[str, Any]:
    command_line = str(unreal.SystemLibrary.get_command_line())
    if "-nullrhi" in command_line.lower():
        raise RuntimeError("Real-player visual validator refuses NullRHI")
    if LEVELS is None or EDITOR_WORLDS is None or ACTORS_API is None:
        raise RuntimeError("Required editor subsystems are unavailable")
    if RECEIPT.exists() or FAILURE_RECEIPT.exists():
        raise RuntimeError("Refusing to overwrite prior v002 validation evidence")
    if CAPTURE_DIR.exists():
        raise RuntimeError(f"Refusing to overwrite screenshot root: {CAPTURE_DIR}")
    if not TARGET_FILE.is_file() or not BUILD_RECEIPT.is_file():
        raise RuntimeError("Built OneFactory v002 map/receipt is absent")
    if contract.sha256(SOURCE_FILE) != contract.SOURCE_MAP_SHA256:
        raise RuntimeError("Source OneFactory v001 map hash drifted")
    build = load_json(BUILD_RECEIPT)
    target_hash = contract.sha256(TARGET_FILE)
    if (
        build.get("$schema")
        != "lineboss/audit/one-factory/visual-navigation-build-v002/v1"
        or build.get("status") != contract.BUILD_STATUS
        or build.get("source_map_sha256_before") != contract.SOURCE_MAP_SHA256
        or build.get("source_map_sha256_after") != contract.SOURCE_MAP_SHA256
        or build.get("target_map") != contract.TARGET_MAP
        or build.get("target_map_sha256") != target_hash
        or build.get("navigation_build", {}).get(
            "explicit_build_completed_before_save"
        ) is not True
    ):
        raise RuntimeError("Builder receipt/target-map chain is not exact")
    return {
        "command_line": command_line,
        "real_rhi": True,
        "build_receipt_sha256": contract.sha256(BUILD_RECEIPT),
        "target_map_sha256": target_hash,
    }


PREREQUISITES = preflight()
ANCHORS_BEFORE = frozen_anchor_snapshot()
WORKSPACE_BEFORE = guarded_workspace_snapshot()
TARGET_HASH_BEFORE = contract.sha256(TARGET_FILE)
CAPTURE_DIR.mkdir(parents=True, exist_ok=False)
RECEIPT.parent.mkdir(parents=True, exist_ok=True)

payload: dict[str, Any] = {
    "$schema": "lineboss/audit/one-factory/visual-navigation-validation-v002/v1",
    "started_utc": datetime.now(timezone.utc).isoformat(),
    "status": "RUNNING",
    "validator_script": relative(SCRIPT_FILE),
    "validator_script_sha256": contract.sha256(SCRIPT_FILE),
    "source_map": contract.SOURCE_MAP,
    "source_map_sha256": contract.SOURCE_MAP_SHA256,
    "target_map": contract.TARGET_MAP,
    "target_map_sha256_before": TARGET_HASH_BEFORE,
    "prerequisites": PREREQUISITES,
    "editor_fresh_reload": None,
    "runtime": {},
    "screenshots": {},
    "visual_gates": contract.VISUAL_GATES,
    "failures": [],
}

started = time.monotonic()
phase_started = started
phase = "starting"
tick_handle = None
capture_task = None
capture_path: Path | None = None
capture_next_phase: str | None = None
capture_kind: str | None = None
final_status_requested: str | None = None
final_detail = ""
navigation_wait_started = 0.0
ui_resize_last_attempt = 0.0
ui_resize_exact_since: float | None = None


CAMERAS = {
    "01_empty_factory_overview.png": {
        "target": (0.0, 0.0, 0.0), "pitch": -58.0, "zoom": 42_000.0,
    },
    "02_populated_press_bay.png": {
        "target": (-14_500.0, 8_000.0, 0.0), "pitch": -50.0, "zoom": 22_000.0,
    },
    "03_body_bay.png": {
        "target": (-11_000.0, -8_500.0, 0.0), "pitch": -50.0, "zoom": 18_000.0,
    },
    "04_paint_bay.png": {
        "target": (10_000.0, -8_500.0, 0.0), "pitch": -50.0, "zoom": 20_000.0,
    },
    "05_assembly_bay.png": {
        "target": (16_500.0, 8_500.0, 0.0), "pitch": -50.0, "zoom": 20_000.0,
    },
}


def set_camera(pawn: Any, name: str) -> None:
    spec = CAMERAS[name]
    if not pawn.set_automation_camera(
        unreal.Vector(*spec["target"]), spec["pitch"], spec["zoom"]
    ):
        raise RuntimeError(f"Could not set management camera for {name}")


def start_scene_capture(filename: str, next_phase: str) -> None:
    global phase, phase_started, capture_task, capture_path, capture_next_phase, capture_kind
    path = CAPTURE_DIR / filename
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite screenshot: {path}")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        contract.SCREENSHOT_SIZE[0],
        contract.SCREENSHOT_SIZE[1],
        str(path),
        force_game_view=False,
    )
    if not task.is_valid_task():
        raise RuntimeError(f"Invalid high-resolution screenshot task: {filename}")
    capture_task = task
    capture_path = path
    capture_next_phase = next_phase
    capture_kind = "scene"
    phase = "wait_capture"
    phase_started = time.monotonic()


def start_ui_capture(filename: str, next_phase: str) -> None:
    global phase, phase_started, capture_task, capture_path, capture_next_phase, capture_kind
    path = CAPTURE_DIR / filename
    if path.exists():
        raise RuntimeError(f"Refusing to overwrite UI screenshot: {path}")
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    accepted = unreal.LBOneFactoryCaptureBridge.request_pie_restricted_ui_screenshot(
        EDITOR_WORLDS.get_game_world(),
        str(path),
        contract.SCREENSHOT_SIZE[0],
        contract.SCREENSHOT_SIZE[1],
    )
    if not accepted:
        raise RuntimeError("Native 1920x1080 restricted UI screenshot was refused")
    capture_task = None
    capture_path = path
    capture_next_phase = next_phase
    capture_kind = "ui"
    phase = "wait_capture"
    phase_started = time.monotonic()


def record_screenshot(path: Path, kind: str) -> None:
    if not file_ready(path):
        raise RuntimeError(f"Screenshot is absent or too small: {path}")
    metrics = contract.png_metrics(path)
    if metrics["dimensions"] != list(contract.SCREENSHOT_SIZE):
        raise RuntimeError(f"Screenshot is not 1920x1080: {path.name}")
    if kind == "scene" and not contract.scene_metrics_pass(metrics):
        raise RuntimeError(
            f"Common factory visual gate failed for {path.name}: {metrics!r}"
        )
    if (
        kind == "ui"
        and metrics["top_left_warning_red_pixels"]
        > contract.VISUAL_GATES["maximum_top_left_warning_red_pixels"]
    ):
        raise RuntimeError(
            "UI frame retains warning-red pixels consistent with the v001 nav warning: "
            f"{metrics!r}"
        )
    payload["screenshots"][path.name] = {
        "path": relative(path),
        "sha256": contract.sha256(path),
        "bytes": path.stat().st_size,
        "kind": kind,
        "real_rhi": True,
        "metrics": metrics,
    }


def continue_capture(now: float) -> None:
    global phase, phase_started, capture_task, capture_path, capture_next_phase, capture_kind
    if capture_path is None:
        raise RuntimeError("Capture state has no path")
    if capture_kind == "scene":
        if now - phase_started < 1.5 or not capture_task.is_task_done():
            return
    elif capture_kind == "ui":
        if now - phase_started < 1.0:
            return
    else:
        raise RuntimeError(f"Unknown capture kind: {capture_kind}")
    if not file_ready(capture_path):
        if now - phase_started > 20.0:
            raise RuntimeError(f"Screenshot did not become ready: {capture_path}")
        return
    record_screenshot(capture_path, capture_kind)
    next_phase = capture_next_phase
    capture_task = None
    capture_path = None
    capture_next_phase = None
    capture_kind = None
    phase = str(next_phase)
    phase_started = now


def runtime_player_contract(world: Any) -> tuple[Any, Any, Any]:
    game_mode = require_runtime_one(
        world, unreal.LBOneFactoryGameMode, "OneFactory GameMode"
    )
    bootstrap = require_runtime_one(
        world, unreal.LBOneFactoryBootstrap, "OneFactory bootstrap"
    )
    authority = require_runtime_one(
        world, unreal.LBPressShopBuildAuthority, "Press build authority"
    )
    pawn = require_runtime_one(world, unreal.LBManagementPawn, "management pawn")
    hud = require_runtime_one(world, unreal.LBControlRoomHUD, "management HUD")
    controller = unreal.GameplayStatics.get_player_controller(world, 0)
    if controller is None:
        raise RuntimeError("PIE has no player controller")
    if (
        unreal.GameplayStatics.get_player_pawn(world, 0) != pawn
        or controller.get_controlled_pawn() != pawn
        or controller.get_view_target() != pawn
        or controller.get_hud() != hud
        or not game_mode.has_valid_one_factory_shell()
        or game_mode.get_one_factory_bootstrap() != bootstrap
        or not bootstrap.has_valid_shell()
        or bootstrap.get_press_build_authority() != authority
    ):
        raise RuntimeError("Actual OneFactory GameMode/pawn/HUD/bootstrap contract drift")
    if actors_of(world, unreal.LBOneFactoryPressStarterLayoutAuthority) or actors_of(
        world, unreal.LBOneFactoryPressStarterPresentationActor
    ):
        raise RuntimeError("PIE did not start from the exact empty saved shell")
    builder = get_builder(world)
    by_label = runtime_by_label(world)
    lighting = gate.audit_lighting(by_label)
    navigation = gate.audit_navigation(world, by_label, require_quiescent=True)
    payload["runtime"]["actual_player_shell"] = {
        "game_mode": gate.path_name(game_mode.get_class()),
        "pawn": gate.path_name(pawn.get_class()),
        "hud": gate.path_name(hud.get_class()),
        "bootstrap_ready": True,
        "press_build_authority": authority.get_actor_label(),
        "zero_starter_pair_before_player_action": True,
        "lighting": lighting,
        "navigation": navigation,
    }
    return pawn, hud, builder


def request_finish(status: str, detail: str = "") -> None:
    global phase, phase_started, final_status_requested, final_detail, capture_task
    if phase in {"ending_pie", "finalizing"}:
        return
    capture_task = None
    final_status_requested = status
    final_detail = detail
    phase = "ending_pie"
    phase_started = time.monotonic()
    LEVELS.editor_request_end_play()


def fail(message: str) -> None:
    unreal.log_error(
        "LINE_BOSS_ONE_FACTORY_VISUAL_NAVIGATION_VALIDATION_V002_FAIL " + message
    )
    if message not in payload["failures"]:
        payload["failures"].append(message)
    request_finish("FAIL__ONE_FACTORY_VISUAL_NAVIGATION_VALIDATION_V002", message)


def finalize_after_pie() -> None:
    global phase, tick_handle
    phase = "finalizing"
    try:
        if set(payload["screenshots"]) != set(contract.SCREENSHOT_NAMES):
            payload["failures"].append(
                "Screenshot inventory mismatch: "
                + ", ".join(sorted(payload["screenshots"]))
            )
        scene_means = [
            float(row["metrics"]["mean_luma"])
            for row in payload["screenshots"].values()
            if row["kind"] == "scene"
        ]
        spread = max(scene_means) - min(scene_means) if scene_means else None
        payload["runtime"]["factory_wide_scene_mean_luma_spread"] = spread
        if (
            spread is None
            or spread > contract.VISUAL_GATES["maximum_scene_mean_spread"]
        ):
            payload["failures"].append(
                f"Factory-wide scene mean-luma spread failed: {spread}"
            )

        if not LEVELS.load_level(contract.SOURCE_MAP):
            raise RuntimeError("Could not unload v002 for final independent reload")
        if not LEVELS.load_level(contract.TARGET_MAP):
            raise RuntimeError("Could not fresh-reload v002 after PIE")
        world = gate.editor_world()
        final_audit = gate.audit_complete_map(
            world,
            ACTORS_API,
            run_bootstrap_validation=True,
            require_navigation_quiescent=False,
            require_navigation_routes=False,
        )
        nonfoundation, _by_label = gate.actor_index(ACTORS_API)
        starter_classes = {
            "/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority",
            "/Script/LineBossCarFactory.LBOneFactoryPressStarterPresentationActor",
        }
        saved_starters = [
            actor.get_actor_label()
            for actor in nonfoundation
            if gate.path_name(actor.get_class()) in starter_classes
        ]
        if saved_starters:
            raise RuntimeError(f"Transient Press starter leaked into saved map: {saved_starters}")
        payload["editor_final_fresh_reload"] = final_audit
        payload["editor_final_fresh_reload"]["saved_starter_pair_count"] = 0

        target_after = contract.sha256(TARGET_FILE)
        source_after = contract.sha256(SOURCE_FILE)
        anchors_after = frozen_anchor_snapshot()
        workspace_after = guarded_workspace_snapshot()
        payload["target_map_sha256_after"] = target_after
        payload["source_map_sha256_after"] = source_after
        payload["target_map_byte_identical_during_validation"] = (
            target_after == TARGET_HASH_BEFORE
        )
        payload["protected_anchors_after"] = anchors_after
        payload["guarded_workspace_unchanged"] = workspace_after == WORKSPACE_BEFORE
        if target_after != TARGET_HASH_BEFORE:
            payload["failures"].append("Target map bytes changed during read-only validation")
        if source_after != contract.SOURCE_MAP_SHA256:
            payload["failures"].append("Source v001 map changed during validation")
        if anchors_after != ANCHORS_BEFORE:
            payload["failures"].append("Static protected anchors changed")
        if workspace_after != WORKSPACE_BEFORE:
            payload["failures"].append("Content/Source/Config/SaveGames changed")
    except Exception as exc:
        payload["failures"].append(f"Finalization failed: {type(exc).__name__}: {exc}")
        payload["finalization_traceback"] = traceback.format_exc()

    payload["detail"] = final_detail
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    payload["status"] = (
        contract.VALIDATION_STATUS
        if final_status_requested == contract.VALIDATION_STATUS
        and not payload["failures"]
        else "FAIL__ONE_FACTORY_VISUAL_NAVIGATION_VALIDATION_V002"
    )
    RECEIPT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    if payload["status"] == contract.VALIDATION_STATUS:
        unreal.log(
            "LINE_BOSS_ONE_FACTORY_VISUAL_NAVIGATION_VALIDATION_V002_PASS"
        )
    else:
        unreal.log_error(
            "LINE_BOSS_ONE_FACTORY_VISUAL_NAVIGATION_VALIDATION_V002_FAIL"
        )
    unreal.SystemLibrary.quit_editor()


def tick(_delta_seconds: float) -> None:
    global phase, phase_started, navigation_wait_started
    global ui_resize_last_attempt, ui_resize_exact_since
    now = time.monotonic()
    world = EDITOR_WORLDS.get_game_world()
    if phase == "ending_pie":
        if world is None or now - phase_started > 20.0:
            finalize_after_pie()
        return
    if phase == "finalizing":
        return
    if now - started > 240.0:
        fail(f"Timed out in phase {phase}")
        return
    if world is None:
        return
    try:
        if phase == "wait_capture":
            continue_capture(now)
            return
        pawn = require_runtime_one(world, unreal.LBManagementPawn, "management pawn")
        hud = require_runtime_one(world, unreal.LBControlRoomHUD, "management HUD")
        builder = get_builder(world)

        if phase == "wait_world":
            if now - phase_started < 4.0:
                return
            nav = unreal.NavigationSystemV1.get_navigation_system(world)
            if nav is None:
                raise RuntimeError("PIE NavigationSystemV1 is unavailable")
            bounds = actors_of(world, unreal.NavMeshBoundsVolume)
            if len(bounds) != 1:
                raise RuntimeError(f"PIE NavMesh bounds count is {len(bounds)}")
            nav.on_navigation_bounds_updated(bounds[0])
            phase = "wait_navigation"
            phase_started = now
            navigation_wait_started = now
            return

        if phase == "wait_navigation":
            if unreal.NavigationSystemV1.is_navigation_being_built_or_locked(world):
                if now - navigation_wait_started < 90.0:
                    return
                raise RuntimeError("PIE navigation did not become quiescent in 90 seconds")
            pawn, hud, builder = runtime_player_contract(world)
            set_camera(pawn, "01_empty_factory_overview.png")
            start_scene_capture("01_empty_factory_overview.png", "create_press")
            return

        if phase == "create_press":
            hud.open_factory_build()
            if not hud.activate_management_action(0):
                raise RuntimeError(
                    "Native UMG New Factory action failed: "
                    + str(builder.get_last_action_reason())
                )
            authorities = actors_of(
                world, unreal.LBOneFactoryPressStarterLayoutAuthority
            )
            presentations = actors_of(
                world, unreal.LBOneFactoryPressStarterPresentationActor
            )
            if len(authorities) != 1 or len(presentations) != 1:
                raise RuntimeError(
                    f"Transient Press starter pair drift: {len(authorities)}/{len(presentations)}"
                )
            payload["runtime"]["transient_native_press_starter"] = {
                "authority_count": 1,
                "presentation_count": 1,
                "saved": False,
                "reason": str(builder.get_last_action_reason()),
            }
            hud.close_management()
            set_camera(pawn, "02_populated_press_bay.png")
            start_scene_capture("02_populated_press_bay.png", "capture_body")
            return

        if phase == "capture_body":
            set_camera(pawn, "03_body_bay.png")
            start_scene_capture("03_body_bay.png", "capture_paint")
            return

        if phase == "capture_paint":
            set_camera(pawn, "04_paint_bay.png")
            start_scene_capture("04_paint_bay.png", "capture_assembly")
            return

        if phase == "capture_assembly":
            set_camera(pawn, "05_assembly_bay.png")
            start_scene_capture("05_assembly_bay.png", "prepare_ui")
            return

        if phase == "prepare_ui":
            set_camera(pawn, "02_populated_press_bay.png")
            hud.open_factory_build()
            size = unreal.LBOneFactoryCaptureBridge.resize_pie_window_for_game_widget_size(
                world, contract.SCREENSHOT_SIZE[0], contract.SCREENSHOT_SIZE[1]
            )
            if int(size.x) <= 0 or int(size.y) <= 0:
                raise RuntimeError("Native PIE window resize request was refused")
            ui_resize_last_attempt = now
            ui_resize_exact_since = None
            phase = "wait_ui_size"
            phase_started = now
            return

        if phase == "wait_ui_size":
            size = unreal.LBOneFactoryCaptureBridge.get_pie_game_widget_draw_size(world)
            current = [int(size.x), int(size.y)]
            if current != list(contract.SCREENSHOT_SIZE):
                ui_resize_exact_since = None
                if now - phase_started > 12.0:
                    raise RuntimeError(f"PIE UI size did not settle at 1920x1080: {current}")
                if now - ui_resize_last_attempt > 0.75:
                    result = unreal.LBOneFactoryCaptureBridge.resize_pie_window_for_game_widget_size(
                        world, contract.SCREENSHOT_SIZE[0], contract.SCREENSHOT_SIZE[1]
                    )
                    if int(result.x) <= 0 or int(result.y) <= 0:
                        raise RuntimeError("Corrective PIE resize request was refused")
                    ui_resize_last_attempt = now
                return
            if ui_resize_exact_since is None:
                ui_resize_exact_since = now
                return
            if now - ui_resize_exact_since < 0.5:
                return
            start_ui_capture(
                "06_populated_press_with_umg_nav_clean.png", "finish"
            )
            return

        if phase == "finish":
            request_finish(contract.VALIDATION_STATUS)
    except Exception as exc:
        fail(f"{type(exc).__name__}: {exc}")


try:
    if not LEVELS.load_level(contract.TARGET_MAP):
        raise RuntimeError(f"Could not fresh-load {contract.TARGET_MAP}")
    editor_world = gate.editor_world()
    payload["editor_fresh_reload"] = gate.audit_complete_map(
        editor_world,
        ACTORS_API,
        run_bootstrap_validation=True,
        require_navigation_quiescent=False,
        require_navigation_routes=False,
    )
    if contract.sha256(TARGET_FILE) != TARGET_HASH_BEFORE:
        raise RuntimeError("Target map changed during editor fresh-load audit")
    unreal.EditorPythonScripting.set_keep_python_script_alive(True)
    phase = "wait_world"
    phase_started = time.monotonic()
    tick_handle = unreal.register_slate_post_tick_callback(tick)
    LEVELS.editor_request_begin_play()
except Exception as exc:
    payload["failures"].append(f"Pre-PIE failure: {type(exc).__name__}: {exc}")
    payload["traceback"] = traceback.format_exc()
    payload["status"] = "FAIL__ONE_FACTORY_VISUAL_NAVIGATION_VALIDATION_V002"
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    FAILURE_RECEIPT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.log_error(
        "LINE_BOSS_ONE_FACTORY_VISUAL_NAVIGATION_VALIDATION_V002_PRE_PIE_FAIL "
        f"{type(exc).__name__}: {exc}"
    )
    unreal.SystemLibrary.quit_editor()
    raise
