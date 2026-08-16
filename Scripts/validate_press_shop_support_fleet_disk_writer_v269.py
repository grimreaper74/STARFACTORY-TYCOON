"""Write the exact v269 four-unit fleet to an isolated campaign disk slot."""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269"
SLOT = "LB_AUTOMATION_SUPPORT_FLEET_V269_DISK_ROUNDTRIP"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/SupportRobots/press_shop_support_fleet_disk_writer_v269.json"
SAVE_FILE = Path(unreal.Paths.project_saved_dir()) / "SaveGames" / f"{SLOT}.sav"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
if unreal.GameplayStatics.does_save_game_exist(SLOT, 0):
    if not unreal.GameplayStatics.delete_game_in_slot(SLOT, 0):
        raise RuntimeError(f"Could not clear isolated slot {SLOT}")
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
handle = None


def finish(status, failure=None, evidence=None):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "$schema": "cairnwell/audit/support-fleet-disk-writer-v269/v1",
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
        f"LINE_BOSS_SUPPORT_FLEET_DISK_WRITER_V269 {'FAIL ' + failure if failure else 'PASS'}")
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    if time.monotonic() - started > 45.0:
        finish("SUPPORT_FLEET_V269_DISK_WRITE_FAIL__NOT_PROMOTED", "timeout")
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
    if not controller.save_fleet_to_campaign_slot():
        finish("SUPPORT_FLEET_V269_DISK_WRITE_FAIL__NOT_PROMOTED", "SaveFleetToCampaignSlot rejected")
        return
    if not SAVE_FILE.exists() or SAVE_FILE.stat().st_size < 512:
        finish("SUPPORT_FLEET_V269_DISK_WRITE_FAIL__NOT_PROMOTED", "slot missing or too small")
        return
    root = unreal.GameplayStatics.load_game_from_slot(SLOT, 0)
    cleaning = list(root.get_editor_property("cleaning_robots")) if root else []
    maintenance = list(root.get_editor_property("maintenance_robots")) if root else []
    ids = sorted([str(s.common.unit_id) for s in cleaning + maintenance])
    finish("SUPPORT_FLEET_V269_DISK_WRITE_PASS__AWAITING_FRESH_PROCESS_READBACK__NOT_PROMOTED", evidence={
        "save_format_version": root.get_editor_property("save_format_version"),
        "cleaning_count": len(cleaning),
        "maintenance_count": len(maintenance),
        "unit_ids": ids,
        "slot_file_bytes": SAVE_FILE.stat().st_size,
        "slot_file_sha256": hashlib.sha256(SAVE_FILE.read_bytes()).hexdigest(),
    })


handle = unreal.register_slate_post_tick_callback(tick)
