"""Read the v269 fleet slot in a fresh Unreal process and prove safe revalidation."""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269"
SLOT = "LB_AUTOMATION_SUPPORT_FLEET_V269_DISK_ROUNDTRIP"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/SupportRobots/press_shop_support_fleet_disk_reader_v269.json"
SAVE_FILE = Path(unreal.Paths.project_saved_dir()) / "SaveGames" / f"{SLOT}.sav"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None


def finish(status, failure=None, evidence=None):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "$schema": "cairnwell/audit/support-fleet-disk-reader-v269/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "map": MAP,
        "slot": SLOT,
        "duration_seconds": time.monotonic() - started,
        "evidence": evidence or {},
        "failure": failure,
        "promotion_authorized": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    (unreal.log_error if failure else unreal.log)(
        f"LINE_BOSS_SUPPORT_FLEET_DISK_READER_V269 {'FAIL ' + failure if failure else 'PASS'}")
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    if time.monotonic() - started > 45.0:
        finish("SUPPORT_FLEET_V269_FRESH_PROCESS_READ_FAIL__NOT_PROMOTED", "timeout")
        return
    if not SAVE_FILE.exists():
        finish("SUPPORT_FLEET_V269_FRESH_PROCESS_READ_FAIL__NOT_PROMOTED", "writer slot absent")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    controllers = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopSupportFleetController)
    if len(controllers) != 1:
        return
    controller = controllers[0]
    if not controller.is_fleet_ready():
        return
    controller.set_editor_property("campaign_slot_name", SLOT)
    controller.set_editor_property("campaign_user_index", 0)
    if not controller.load_fleet_from_campaign_slot():
        finish("SUPPORT_FLEET_V269_FRESH_PROCESS_READ_FAIL__NOT_PROMOTED", "LoadFleetFromCampaignSlot rejected")
        return
    robots = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBSupportRobot)
    rows = []
    for robot in robots:
        state = robot.capture_common_save_state()
        if str(state.unit_id) not in {"LB-CR01-01", "LB-CR01-02", "LB-MR01-01", "LB-MR01-02"}:
            continue
        rows.append({
            "unit_id": str(state.unit_id),
            "variant_id": str(state.variant_id),
            "certified": bool(state.certified),
            "docked": bool(state.docked),
            "dock_id": str(state.dock_id),
            "route_revalidation_required": bool(state.route_revalidation_required),
            "battery_percent": float(state.battery_state_of_charge_percent),
            "mission_count": int(state.mission_count),
            "automatic_charging_route": bool(robot.has_automatic_charging_route()),
            "route_authority": bool(robot.has_route_authority()),
        })
    rows.sort(key=lambda row: row["unit_id"])
    expected_docks = {"LB-CR01-01": "LB-DOCK-CR01-01", "LB-CR01-02": "LB-DOCK-CR01-02",
                      "LB-MR01-01": "LB-DOCK-MR01-01", "LB-MR01-02": "LB-DOCK-MR01-02"}
    valid = len(rows) == 4 and controller.was_fleet_restored_from_disk()
    valid = valid and all(row["certified"] and row["docked"] and not row["route_revalidation_required"]
                          and row["automatic_charging_route"] and not row["route_authority"]
                          and row["dock_id"] == expected_docks[row["unit_id"]] for row in rows)
    finish(
        "SUPPORT_FLEET_V269_FRESH_PROCESS_DISK_READ_AND_SAFE_REVALIDATION_PASS__NOT_PROMOTED" if valid
        else "SUPPORT_FLEET_V269_FRESH_PROCESS_READ_FAIL__NOT_PROMOTED",
        None if valid else "restored fleet contract mismatch",
        {"fleet_ready": controller.is_fleet_ready(), "restored_from_disk": controller.was_fleet_restored_from_disk(),
         "robots": rows, "slot_file_sha256": hashlib.sha256(SAVE_FILE.read_bytes()).hexdigest()},
    )


handle = unreal.register_slate_post_tick_callback(tick)
