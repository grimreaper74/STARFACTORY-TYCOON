"""Transient PIE-only Body Shop management-camera comparison.

This script never saves Content.  It captures three candidate camera contracts
from the possessed prototype pawn so the release framing can be selected from
real runtime evidence instead of repeated source edits.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)

ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001"
MAP_FILE = ROOT / "Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap"
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUT = ROOT / "Saved/ValidationScreenshots/BodyShop/Experimental_v001/CameraCalibration_v005" / STAMP
AUDIT = ROOT / "Saved/Audits/BodyShop/Experimental_v001" / f"camera_calibration_v005_{STAMP}.json"
LEVELS = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
MAP_SHA = hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper()

TARGET = unreal.Vector(-4050.0, -1800.0, 180.0)
VARIANTS = [
    {"name": "D_cutaway_oblique_75", "pitch": -25.0, "yaw": 75.0,
     "arm_cm": 3000.0, "fov": 65.0},
    {"name": "E_cutaway_oblique_65", "pitch": -28.0, "yaw": 65.0,
     "arm_cm": 3200.0, "fov": 62.0},
    {"name": "F_cutaway_oblique_55", "pitch": -30.0, "yaw": 55.0,
     "arm_cm": 3400.0, "fov": 60.0},
]

OUT.mkdir(parents=True, exist_ok=False)
AUDIT.parent.mkdir(parents=True, exist_ok=True)

state = {"phase": "wait_world", "index": 0, "phase_started": time.monotonic(),
         "task": None, "tick": None, "rows": [], "failures": [],
         "hidden_cutaway_structure_count": 0}
started = time.monotonic()


def actors_of(world, cls):
    return list(unreal.GameplayStatics.get_all_actors_of_class(world, cls))


def finish(status: str):
    payload = {
        "$schema": "lineboss/audit/bodyshop/camera-calibration-v005/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "map_sha256_before": MAP_SHA,
        "map_sha256_after": hashlib.sha256(MAP_FILE.read_bytes()).hexdigest().upper(),
        "target_cm": [TARGET.x, TARGET.y, TARGET.z],
        "variants": state["rows"],
        "hidden_cutaway_structure_count": state["hidden_cutaway_structure_count"],
        "failures": state["failures"],
        "writes_to_content_source_config_or_saves": False,
    }
    payload["map_hash_unchanged"] = payload["map_sha256_before"] == payload["map_sha256_after"]
    if not payload["map_hash_unchanged"]:
        payload["failures"].append("Body Shop map hash changed")
        payload["status"] = "FAIL__BODYSHOP_CAMERA_CALIBRATION_V005"
    AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if state["tick"] is not None:
        unreal.unregister_slate_post_tick_callback(state["tick"])
        state["tick"] = None
    try:
        LEVELS.editor_request_end_play()
    finally:
        unreal.SystemLibrary.quit_editor()


def fail(message: str):
    unreal.log_error("LINE_BOSS_BODYSHOP_CAMERA_CALIBRATION_V005_FAIL " + message)
    state["failures"].append(message)
    finish("FAIL__BODYSHOP_CAMERA_CALIBRATION_V005")


def apply_variant(world, row):
    pawns = actors_of(world, unreal.LBBodyShopManagementPawn)
    if len(pawns) != 1:
        raise RuntimeError(f"Expected one Body Shop management pawn, found {len(pawns)}")
    pawn = pawns[0]
    controller = unreal.GameplayStatics.get_player_controller(world, 0)
    if controller is None or unreal.GameplayStatics.get_player_pawn(world, 0) != pawn:
        raise RuntimeError("Body Shop management pawn is not possessed")
    booms = pawn.get_components_by_class(unreal.SpringArmComponent)
    cameras = pawn.get_components_by_class(unreal.CameraComponent)
    if len(booms) != 1 or len(cameras) != 1:
        raise RuntimeError(f"Unexpected camera component counts: boom={len(booms)} camera={len(cameras)}")
    rotation = unreal.Rotator(roll=0.0, pitch=row["pitch"], yaw=row["yaw"])
    pawn.set_actor_location(TARGET, False, False)
    booms[0].set_editor_property("target_arm_length", row["arm_cm"])
    booms[0].set_relative_rotation(rotation, False, False)
    cameras[0].set_editor_property("field_of_view", row["fov"])
    controller.set_control_rotation(rotation)
    return pawn, booms[0], cameras[0]


def apply_transient_cutaway(world):
    hidden = 0
    for actor in actors_of(world, unreal.StaticMeshActor):
        try:
            identity = actor.get_actor_label()
        except Exception:
            identity = actor.get_name()
        if ("LB_BS_ENV_Truss_" in identity
                or "LB_BS_ENV_Column_South_" in identity):
            actor.set_actor_hidden_in_game(True)
            hidden += 1
    if hidden != 18:
        raise RuntimeError(f"Expected 18 transient cutaway structures, hid {hidden}")
    state["hidden_cutaway_structure_count"] = hidden


def tick(_delta):
    now = time.monotonic()
    if now - started > 75.0:
        fail("Timed out in phase " + state["phase"])
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if world is None:
        return
    try:
        if state["phase"] == "wait_world":
            if now - state["phase_started"] < 4.0:
                return
            apply_transient_cutaway(world)
            state["phase"] = "apply"

        if state["phase"] == "apply":
            if state["index"] >= len(VARIANTS):
                finish("PASS__TRANSIENT_BODYSHOP_CAMERA_CALIBRATION_V005")
                return
            row = dict(VARIANTS[state["index"]])
            pawn, boom, camera = apply_variant(world, row)
            output = OUT / f"{state['index'] + 1:02d}_{row['name']}.png"
            row.update({
                "path": str(output),
                "pawn_location_cm": [pawn.get_actor_location().x, pawn.get_actor_location().y,
                                     pawn.get_actor_location().z],
                "applied_arm_cm": float(boom.get_editor_property("target_arm_length")),
                "applied_fov": float(camera.get_editor_property("field_of_view")),
            })
            state["rows"].append(row)
            # Guard against Slate re-entry while the screenshot request pumps
            # the editor message loop.
            state["phase"] = "issuing_capture"
            unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
            unreal.AutomationLibrary.finish_loading_before_screenshot()
            task = unreal.AutomationLibrary.take_high_res_screenshot(
                1920, 1080, str(output), force_game_view=False)
            if not task.is_valid_task():
                raise RuntimeError("Invalid screenshot task for " + row["name"])
            state["task"] = task
            state["phase"] = "wait_capture"
            state["phase_started"] = now
            return

        if state["phase"] == "wait_capture":
            if not state["task"].is_task_done() or now - state["phase_started"] < 2.0:
                return
            path = Path(state["rows"][-1]["path"])
            if not path.is_file() or path.stat().st_size < 1024:
                raise RuntimeError("Camera calibration screenshot is missing: " + str(path))
            state["rows"][-1]["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest().upper()
            state["rows"][-1]["bytes"] = path.stat().st_size
            state["index"] += 1
            state["phase"] = "apply"
    except Exception as exc:
        fail(str(exc))


if not MAP_FILE.is_file() or not LEVELS.load_level(MAP):
    raise RuntimeError("Could not load the isolated Body Shop map")
LEVELS.editor_request_begin_play()
state["tick"] = unreal.register_slate_post_tick_callback(tick)
