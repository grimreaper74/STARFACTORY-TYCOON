"""Write an exact-v198 running PR005 snapshot to a named campaign disk slot."""

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import unreal


unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005AudioRuntimeCandidate_v198"
SLOT = "LB_AUTOMATION_PR005_V198_DISK_ROUNDTRIP"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_pr005_disk_slot_writer_v198.json"
SAVE_FILE = Path(unreal.Paths.project_saved_dir()) / "SaveGames" / f"{SLOT}.sav"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
if unreal.GameplayStatics.does_save_game_exist(SLOT, 0):
    if not unreal.GameplayStatics.delete_game_in_slot(SLOT, 0):
        raise RuntimeError(f"Could not clear isolated automation slot {SLOT}")
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
phase = "setup"
handle = None


def finish(status, failure=None, evidence=None):
    global handle
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    payload = {
        "$schema": "cairnwell/audit/press-shop-pr005-disk-slot-writer-v198/v1",
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
    if failure:
        unreal.log_error(f"LINE_BOSS_PR005_DISK_WRITER_V198_FAIL {failure}")
    else:
        unreal.log("LINE_BOSS_PR005_DISK_WRITER_V198_PASS")
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global phase
    if time.monotonic() - started > 30.0:
        finish("RUNTIME_PR005_V198_DISK_WRITER_FAIL__NOT_PROMOTED", "timeout")
        return
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    rows = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPR005Station)
    if len(rows) != 1:
        return
    station = rows[0]
    state = str(station.get_machine_state()).upper()
    if phase == "setup":
        station.set_control_power(True)
        station.set_utilities_available(True)
        loaded = station.load_coil_with_traceability("MCX-U-CS10-0001", "HT-CW26-08417", "LOT-MCXU-260804-A", "503184064100010", 1500.0)
        recipe = station.select_recipe(unreal.Name("U_SERIES_1500"), 1500.0)
        station.set_coil_car_positioned(True)
        station.set_mandrel_expanded(True)
        station.set_keeper_and_snubber(True, True)
        station.set_guards_closed(True)
        station.set_safety_circuit_healthy(True)
        station.set_strip_threaded(True)
        commissioned = station.begin_commissioning()
        manual = station.set_control_mode(unreal.LBPR005ControlMode.MANUAL)
        dry = station.press_cycle_start()
        if not all((loaded, recipe, commissioned, manual, dry)):
            finish("RUNTIME_PR005_V198_DISK_WRITER_FAIL__NOT_PROMOTED", "setup rejected")
            return
        phase = "first_off"
        return
    if phase == "first_off" and "FIRST_OFF_VALIDATION" in state:
        station.record_first_off_produced()
        if not station.approve_first_off() or not station.set_control_mode(unreal.LBPR005ControlMode.AUTOMATIC) or not station.press_cycle_start():
            finish("RUNTIME_PR005_V198_DISK_WRITER_FAIL__NOT_PROMOTED", "automatic start rejected")
            return
        phase = "running"
        return
    if phase == "running" and "RUNNING" in state:
        saved = station.capture_save_state()
        root = unreal.GameplayStatics.create_save_game_object(unreal.LBPressShopSaveGame)
        root.set_editor_property("pr005", saved)
        if root.get_editor_property("save_format_version") != 10:
            finish("RUNTIME_PR005_V198_DISK_WRITER_FAIL__NOT_PROMOTED", "wrong campaign format")
            return
        if not unreal.GameplayStatics.save_game_to_slot(root, SLOT, 0):
            finish("RUNTIME_PR005_V198_DISK_WRITER_FAIL__NOT_PROMOTED", "SaveGameToSlot returned false")
            return
        if not SAVE_FILE.exists() or SAVE_FILE.stat().st_size < 256:
            finish("RUNTIME_PR005_V198_DISK_WRITER_FAIL__NOT_PROMOTED", "slot file missing or too small")
            return
        digest = hashlib.sha256(SAVE_FILE.read_bytes()).hexdigest()
        finish("RUNTIME_PR005_V198_RUNNING_CAMPAIGN_DISK_SLOT_WRITE_PASS__AWAITING_FRESH_PROCESS_READBACK__NOT_PROMOTED", evidence={
            "save_format_version": root.get_editor_property("save_format_version"),
            "station_snapshot_version": saved.version,
            "saved_machine_state": str(saved.machine_state),
            "coil_id": saved.coil_id,
            "heat_id": saved.heat_id,
            "supplier_lot_id": saved.supplier_lot_id,
            "barcode": saved.traceability_barcode,
            "slot_file_bytes": SAVE_FILE.stat().st_size,
            "slot_file_sha256": digest,
        })


handle = unreal.register_slate_post_tick_callback(tick)
