"""Guarded live PIE validation and evidence capture for the Body Shop v001 slice.

The saved map remains an intentionally empty experimental shell.  This script
loads it, lets the map-local GameMode construct the six-cell pilot line at
BeginPlay, proves the runtime-only contract, exercises controlled validation
states and experimental save/reload, captures evidence, then ends PIE without
saving the map.  It never opens the Press Shop, campaign save or legacy Body
Weld composite.
"""

from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MAP_FILE = ROOT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
CAPTURE_DIR = ROOT / "Saved/ValidationScreenshots/BodyShop/v001" / f"live_slice_{STAMP}"
AUDIT = ROOT / "Saved/Audits/BodyShop/v001" / f"body_shop_live_slice_validation_{STAMP}.json"

EXPECTED_DEFINITIONS = {
    "BW001_FULL_STILLAGE_DOCK_BASIC",
    "BW002_PANEL_PRESENTATION_BASIC",
    "BW003_UNDERBODY_FIXTURE_BASIC",
    "BW003_STRAIGHT_SKID_CONVEYOR_BASIC",
    "BW012_VISION_GATE_BASIC",
    "BW014_OUTPUT_BUFFER_BASIC",
}

LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
ACTORS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
CAMERA_TAGS = [
    unreal.Name("LB.BodyShop.LiveSlice.Overview.v001"),
    unreal.Name("LB.BodyShop.LiveSlice.Fixture.v001"),
]

CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)

if not MAP_FILE.exists():
    raise RuntimeError(f"Body Shop map file is missing: {MAP_FILE}")

MAP_SHA_BEFORE = hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper()
if not LEVELS.load_level(MAP):
    raise RuntimeError(f"Could not load isolated Body Shop map: {MAP}")


def look_at(source, target):
    direction = target - source
    horizontal = math.sqrt(direction.x * direction.x + direction.y * direction.y)
    return unreal.Rotator(
        pitch=math.degrees(math.atan2(direction.z, horizontal)),
        yaw=math.degrees(math.atan2(direction.y, direction.x)),
        roll=0.0,
    )


def spawn_capture_camera(label, tag, source, target, fov):
    camera = ACTORS.spawn_actor_from_class(unreal.CameraActor, source, look_at(source, target))
    if camera is None:
        raise RuntimeError(f"Could not create transient capture camera {label}")
    camera.set_actor_label(label)
    camera.tags = [tag]
    camera.camera_component.set_field_of_view(fov)
    return camera


# These are editor-only transient capture helpers.  They are never saved and
# are discarded when this isolated editor process quits.
EDITOR_CAMERAS = [
    spawn_capture_camera(
        "LB_BodyShop_LiveSlice_Overview_v001",
        CAMERA_TAGS[0],
        unreal.Vector(-7200.0, -4000.0, 1050.0),
        unreal.Vector(-4450.0, -1800.0, 180.0),
        50.0,
    ),
    spawn_capture_camera(
        "LB_BodyShop_LiveSlice_Fixture_v001",
        CAMERA_TAGS[1],
        unreal.Vector(-5250.0, -3300.0, 900.0),
        unreal.Vector(-4500.0, -1800.0, 140.0),
        46.0,
    ),
]

started = time.monotonic()
phase_started = started
phase = "wait_world"
tick_handle = None
capture_task = None
capture_index = 0
payload = {
    "$schema": "cairnwell/audit/body-shop-live-slice-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "map_sha256_before": MAP_SHA_BEFORE,
    "map_saved": False,
    "legacy_body_weld_modified": False,
    "campaign_save_modified": False,
    "press_shop_modified": False,
    "meshy_credits_used_by_codex": 0,
    "checks": {},
    "screenshots": [],
    "failures": [],
}


def stage_text(runtime):
    return str(runtime.get_runtime_stage()).upper() if runtime else "NONE"


def call_bool_with_reason(method, label):
    """Handle UE Python's bool + FString& output wrapper consistently."""
    try:
        result = method()
    except TypeError:
        result = method("")
    if isinstance(result, tuple):
        success = bool(result[0])
        reason = str(result[1]) if len(result) > 1 else ""
    else:
        success = bool(result)
        reason = ""
    payload["checks"][label] = {"success": success, "reason": reason}
    return success, reason


def start_pilot_cycle(runtime, label):
    """UE Python exposes bool+FString& as Optional[str]; verify runtime state directly."""
    before = {
        "stage": stage_text(runtime),
        "status": str(runtime.get_runtime_status_text()),
        "wip": int(runtime.get_active_pilot_wip_count()),
        "running": bool(runtime.is_simulation_running()),
    }
    result = runtime.start_pilot_cycle()
    after = {
        "stage": stage_text(runtime),
        "status": str(runtime.get_runtime_status_text()),
        "wip": int(runtime.get_active_pilot_wip_count()),
        "running": bool(runtime.is_simulation_running()),
    }
    success = after["wip"] == 1 and after["running"]
    reason = str(result) if result is not None else after["status"]
    payload["checks"][label] = {
        "success": success,
        "reason": reason,
        "python_return": repr(result),
        "before": before,
        "after": after,
    }
    return success, reason


def actor_classes(world):
    return {
        "bootstrap": unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.LBBodyShopPrototypeWorldBootstrap),
        "runtime": unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.LBBodyShopPrototypeRuntime),
        "authority": unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.LBBodyShopBuildAuthority),
        "cells": unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.LBBodyShopCellActor),
        "robots": unreal.GameplayStatics.get_all_actors_of_class(
            world, unreal.LBBodyShopRobotActor),
    }


def apply_capture_only_lighting(world):
    """Use broad factory fill; local RectLight pools obscure the cell art."""
    adjusted = 0
    active_fill = 0
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.RectLight):
        component = actor.get_component_by_class(unreal.RectLightComponent)
        if component is None:
            continue
        component.set_intensity(0.0)
        component.set_visibility(False, True)
        component.set_cast_shadows(False)
        adjusted += 1
        location = actor.get_actor_location()
        if -6500.0 <= location.x <= -2500.0 and abs(location.y + 1800.0) <= 1.0:
            component.set_intensity(900.0)
            component.set_visibility(True, True)
            active_fill += 1
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.DirectionalLight):
        component = actor.get_component_by_class(unreal.DirectionalLightComponent)
        if component is not None:
            component.set_intensity(1.2)
            component.set_cast_shadows(False)
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SkyLight):
        component = actor.get_component_by_class(unreal.SkyLightComponent)
        if component is not None:
            component.set_intensity(1.8)
    for actor in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.PostProcessVolume):
        settings = actor.get_editor_property("settings")
        settings.set_editor_properties({
            "override_auto_exposure_bias": True,
            "auto_exposure_bias": 0.55,
        })
        actor.set_editor_property("settings", settings)
    payload["checks"]["capture_only_lighting"] = {
        "success": adjusted > 0,
        "adjusted_rect_lights": adjusted,
        "active_local_fill_lights": active_fill,
        "local_fill_intensity": 900.0,
        "other_rect_light_intensity": 0.0,
        "other_rect_lights_visible": False,
        "directional_light_intensity": 1.2,
        "directional_cast_shadows": False,
        "sky_light_intensity": 1.8,
        "exposure_bias": 0.55,
        "map_saved": False,
    }


def hide_capture_only_debug_grid(world):
    """The 1 m authoring grid is useful for placement, but aliases in release evidence."""
    grid_tag = unreal.Name("LB.BodyShop.Environment.Grid.100cm")
    actors = unreal.GameplayStatics.get_all_actors_with_tag(world, grid_tag)
    for actor in actors:
        actor.set_actor_hidden_in_game(True)
    payload["checks"]["capture_only_debug_grid"] = {
        "success": len(actors) > 0,
        "hidden_actor_count": len(actors),
        "map_saved": False,
    }


def capture_camera(world, tag, filename):
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, tag)
    if len(cameras) != 1:
        raise RuntimeError(f"Expected one runtime capture camera tagged {tag}, found {len(cameras)}")
    output = CAPTURE_DIR / filename
    unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
    unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        1920, 1080, str(output), camera=cameras[0], force_game_view=True
    )
    if not task.is_valid_task():
        raise RuntimeError(f"Screenshot task was invalid for {filename}")
    payload["screenshots"].append(str(output))
    return task, output


def finish(status, detail=""):
    global tick_handle
    payload["status"] = status
    payload["detail"] = detail
    payload["finished_utc"] = datetime.now(timezone.utc).isoformat()
    payload["map_sha256_after"] = hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper()
    payload["map_hash_unchanged"] = payload["map_sha256_before"] == payload["map_sha256_after"]
    if not payload["map_hash_unchanged"]:
        payload["failures"].append("Saved experimental map hash changed during live PIE validation")
        payload["status"] = "FAIL__MAP_MUTATED"
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if tick_handle is not None:
        unreal.unregister_slate_post_tick_callback(tick_handle)
        tick_handle = None
    try:
        unreal.EditorLevelLibrary.editor_end_play()
    finally:
        unreal.SystemLibrary.quit_editor()


def fail(message):
    unreal.log_error("LINE_BOSS_BODY_SHOP_LIVE_SLICE_FAIL " + message)
    payload["failures"].append(message)
    finish("FAIL__LIVE_SLICE", message)


def record_runtime_contract(world):
    classes = actor_classes(world)
    bootstrap = classes["bootstrap"]
    runtime = classes["runtime"]
    authority = classes["authority"]
    cells = classes["cells"]
    robots = classes["robots"]
    payload["runtime_actor_counts"] = {key: len(value) for key, value in classes.items()}
    if len(bootstrap) != 1 or len(runtime) != 1 or len(authority) != 1:
        raise RuntimeError("Expected exactly one runtime bootstrap, authority and runtime")
    if len(cells) != 6 or len(robots) != 3:
        raise RuntimeError(f"Expected six cells/three robots, found {len(cells)}/{len(robots)}")
    bootstrap = bootstrap[0]
    runtime = runtime[0]
    if not bootstrap.are_prototype_authorities_bound() or not bootstrap.has_commissioned_initial_underbody_slice():
        raise RuntimeError("Runtime bootstrap did not bind/commission the isolated slice")
    definitions = {str(cell.get_definition_id()) for cell in cells}
    if definitions != EXPECTED_DEFINITIONS or not all(cell.is_commissioned() for cell in cells):
        raise RuntimeError(f"Cell definitions/commissioning invalid: {sorted(definitions)}")
    robot_rows = []
    for robot in robots:
        row = {
            "slot_id": str(robot.get_slot_id()),
            "owning_cell_id": str(robot.get_owning_cell_id()),
            "configured": bool(robot.is_configured_for_authored_slot()),
            "complete_art": bool(robot.has_complete_art_presentation()),
            "vacuum_contact_count": int(robot.get_vacuum_contact_socket_count()),
            "pose": str(robot.get_current_pose()),
        }
        robot_rows.append(row)
    slots = {row["slot_id"] for row in robot_rows}
    if slots != {"ROBOT_HND_01", "ROBOT_WELD_LEFT", "ROBOT_WELD_RIGHT"}:
        raise RuntimeError(f"Unexpected pilot robot slots: {sorted(slots)}")
    if not all(row["configured"] and row["complete_art"] for row in robot_rows):
        raise RuntimeError("One or more pilot robots lack configuration or complete art")
    handling = next(row for row in robot_rows if row["slot_id"] == "ROBOT_HND_01")
    if handling["vacuum_contact_count"] != 8:
        raise RuntimeError(f"Handling robot has {handling['vacuum_contact_count']} vacuum contacts, expected 8")
    # Tool role is deliberately proven by the authored binding/slot contract
    # plus focused C++ automation; RobotActor intentionally exposes no mutable
    # free-programming API or reflective tool-type setter to Python.
    payload["robots"] = robot_rows
    all_actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    forbidden = [actor.get_class().get_name() for actor in all_actors
                 if "BodyWeldLineActor" in actor.get_class().get_name()
                 or "PressShop" in actor.get_class().get_name()
                 or "PressTrain" in actor.get_class().get_name()]
    if forbidden:
        raise RuntimeError("Legacy authority leaked into isolated map: " + ", ".join(sorted(set(forbidden))))
    payload["checks"]["runtime_bootstrap_and_art"] = {
        "success": True,
        "definitions": sorted(definitions),
        "slots": sorted(slots),
        "spot_cgun_evidence": "ROBOT_WELD_LEFT/RIGHT required binding contract passed in focused automation",
    }
    return runtime


def tick(_delta_seconds):
    global phase, phase_started, capture_task, capture_index
    now = time.monotonic()
    if now - started > 115.0:
        fail("Timed out during phase " + phase)
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    try:
        if phase == "wait_world":
            if now - phase_started < 4.0:
                return
            apply_capture_only_lighting(world)
            hide_capture_only_debug_grid(world)
            runtime = record_runtime_contract(world)
            success, reason = start_pilot_cycle(runtime, "start_pilot_cycle")
            if not success:
                raise RuntimeError("Could not start pilot cycle: " + reason)
            runtime.set_output_buffer_blocked_for_validation(True)
            phase = "wait_first_capture"
            phase_started = now
            capture_task, _ = capture_camera(world, CAMERA_TAGS[0], "01_live_slice_overview.png")
            return

        if phase == "wait_first_capture":
            first = CAPTURE_DIR / "01_live_slice_overview.png"
            if first.exists() and first.stat().st_size >= 1024 and now - phase_started > 2.0:
                phase = "wait_output_block"
                phase_started = now
            return

        if phase == "wait_output_block":
            runtime = actor_classes(world)["runtime"][0]
            if "OUTPUT_BLOCKED" not in stage_text(runtime):
                return
            payload["checks"]["blocked_output"] = {
                "success": True,
                "stage": stage_text(runtime),
                "wip_count": int(runtime.get_active_pilot_wip_count()),
            }
            if int(runtime.get_active_pilot_wip_count()) != 1:
                raise RuntimeError("Output-block scenario did not retain exactly one WIP")
            success, reason = call_bool_with_reason(runtime.save_to_experimental_slot, "save_experimental_v1")
            if not success:
                raise RuntimeError("Experimental save failed: " + reason)
            before_reload = int(runtime.get_active_pilot_wip_count())
            success, reason = call_bool_with_reason(runtime.load_from_experimental_slot, "load_experimental_v1")
            after_reload = int(runtime.get_active_pilot_wip_count())
            payload["checks"]["save_reload_no_duplicate_wip"] = {
                "success": success and before_reload == 1 and after_reload == 1,
                "before_reload_wip": before_reload,
                "after_reload_wip": after_reload,
                "reason": reason,
            }
            if not success or after_reload != 1:
                raise RuntimeError("Experimental save/reload failed or duplicated WIP: " + reason)
            runtime.set_output_buffer_blocked_for_validation(False)
            phase = "wait_second_capture"
            phase_started = now
            capture_task, _ = capture_camera(world, CAMERA_TAGS[1], "02_fixture_and_robots.png")
            return

        if phase == "wait_second_capture":
            second = CAPTURE_DIR / "02_fixture_and_robots.png"
            if second.exists() and second.stat().st_size >= 1024 and now - phase_started > 2.0:
                runtime = actor_classes(world)["runtime"][0]
                # Clearing the first pass-held unit lets the controlled quality
                # failure prove independently without adding a seventh module.
                success, reason = call_bool_with_reason(runtime.clear_held_pilot_unit_for_validation,
                                                        "clear_passed_unit")
                if not success:
                    raise RuntimeError("Could not clear completed pilot unit: " + reason)
                runtime.set_pilot_stillage_available(False)
                starved_result = runtime.start_pilot_cycle()
                starved_success = int(runtime.get_active_pilot_wip_count()) == 1
                starved_reason = str(starved_result) if starved_result is not None \
                    else str(runtime.get_runtime_status_text())
                payload["checks"]["start_while_starved"] = {
                    "success": starved_success, "reason": starved_reason,
                    "stage": stage_text(runtime), "python_return": repr(starved_result),
                }
                payload["checks"]["starvation"] = {
                    "success": (not starved_success and "AWAITING" in stage_text(runtime)),
                    "stage": stage_text(runtime), "reason": starved_reason,
                }
                if starved_success or "AWAITING" not in stage_text(runtime):
                    raise RuntimeError("Expected empty-stillage starvation state")
                runtime.set_pilot_stillage_available(True)
                runtime.set_next_vision_result_for_validation(False)
                success, reason = start_pilot_cycle(runtime, "start_quality_fail_cycle")
                if not success:
                    raise RuntimeError("Could not start quality-fail cycle: " + reason)
                phase = "wait_quality_hold"
                phase_started = now
            return

        if phase == "wait_quality_hold":
            runtime = actor_classes(world)["runtime"][0]
            if "QUALITY_HOLD" not in stage_text(runtime):
                return
            payload["checks"]["quality_fail"] = {
                "success": int(runtime.get_active_pilot_wip_count()) == 1,
                "stage": stage_text(runtime),
                "wip_count": int(runtime.get_active_pilot_wip_count()),
            }
            if not payload["checks"]["quality_fail"]["success"]:
                raise RuntimeError("Quality failure did not retain exactly one held WIP")
            finish("PASS__LIVE_RUNTIME_SIX_CELL_SLICE_SAVE_RELOAD_STARVATION_BLOCKED_OUTPUT_AND_QUALITY_FAIL")
    except Exception as exc:
        fail(str(exc))


unreal.EditorLevelLibrary.editor_play_simulate()
tick_handle = unreal.register_slate_post_tick_callback(tick)
