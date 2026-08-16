"""Capture one fixed in-hall native service-dock family per isolated editor run."""
import os
import time
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273"
FAMILY = os.environ.get("LB_DOCK_V273_FAMILY", "").upper()
if FAMILY not in {"MR01", "CR01"}:
    raise RuntimeError("set LB_DOCK_V273_FAMILY to MR01 or CR01")
CAMERA = f"LB_DOCK_V273_CAM_{FAMILY}_PAIR"
OUT = Path(unreal.Paths.project_saved_dir()).resolve() / f"ValidationScreenshots/SupportRobots/PressShopNativeDocks_v273/press_shop_native_docks_v273_{FAMILY.lower()}_pair.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((a for a in actors.get_all_level_actors() if isinstance(a, unreal.CameraActor) and a.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(CAMERA)
OUT.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(OUT), camera=camera, delay=1.0, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("invalid screenshot task")
started = time.monotonic()
handle = None
def finish(_delta):
    global handle
    if not task.is_task_done() and time.monotonic() - started < 60:
        return
    passed = OUT.exists() and OUT.stat().st_size >= 1024
    unreal.log(f"LINE_BOSS_NATIVE_DOCKS_V273_{FAMILY}_{'PASS' if passed else 'FAIL'} {OUT}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()
handle = unreal.register_slate_post_tick_callback(finish)
