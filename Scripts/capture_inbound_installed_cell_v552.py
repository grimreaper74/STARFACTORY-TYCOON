"""Capture overview, hero and two detail gates for inbound isolated v552."""
from pathlib import Path
import time
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v552"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v552"
SHOTS = [
    ("LB_CAM_InboundHall_ProcessOverview_v552", "inbound_process_overview.png"),
    ("LB_CAM_InboundHall_CraneHero_v552", "inbound_crane_hero.png"),
    ("LB_CAM_InboundHall_DockDetail_v552", "inbound_dock_detail.png"),
    ("LB_CAM_InboundHall_HandoffDetail_v552", "inbound_handoff_detail.png"),
]
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("Could not load inbound v552")
OUT.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()

index = 0
task = None
started = 0.0
handle = None

def begin():
    global task, started
    label, filename = SHOTS[index]
    cam = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == label), None)
    if cam is None:
        raise RuntimeError(f"Missing v552 camera {label}")
    task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(OUT / filename), camera=cam,
        mask_enabled=False, capture_hdr=False, delay=0, force_game_view=True)
    if not task.is_valid_task():
        raise RuntimeError(f"Invalid screenshot task for {label}")
    started = time.monotonic()

def tick(_dt):
    global index, handle
    if not task.is_task_done() and time.monotonic() - started < 45:
        return
    label, filename = SHOTS[index]
    path = OUT / filename
    if not path.exists() or path.stat().st_size <= 1024:
        unreal.log_error(f"LINE_BOSS_INBOUND_V552_CAPTURE_FAIL {label} {path}")
        unreal.SystemLibrary.quit_editor()
        return
    unreal.log(f"LINE_BOSS_INBOUND_V552_CAPTURE_PASS {label} {path}")
    index += 1
    if index < len(SHOTS):
        begin()
        return
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()

begin()
handle = unreal.register_slate_post_tick_callback(tick)
