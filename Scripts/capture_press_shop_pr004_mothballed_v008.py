"""Capture one fixed-camera view of the v008 mothballed candidate."""
import os, time
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004MothballedCandidate_v008b"
choices = {
    "close": ("LB_AUDIT_PR004_RobotCondition_Close_v008", "press_shop_v008_robot_condition_close.png"),
    "cell": ("LB_INT_PR004_V009_CAM_PR004CloseDirty", "press_shop_v008_pr004_cell.png"),
    "front": ("LB_INT_PR004_V009_CAM_FrontEndDirty", "press_shop_v008_front_end.png"),
}
which = os.environ.get("LB_PR004_V008_CAPTURE", "close")
label, filename = choices[which]
out = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v008_pr004_mothballed" / filename
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError("Map load failed")
camera = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == label), None)
if camera is None: raise RuntimeError(f"Missing camera {label}")
out.parent.mkdir(parents=True, exist_ok=True)
if out.exists(): out.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, str(out), camera=camera, force_game_view=True)
started = time.monotonic(); handle = None
def tick(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed < 3 or not out.exists() or out.stat().st_size < 1024:
        if elapsed < 55: return
        unreal.log_error(f"LINE_BOSS_PR004_V008_CAPTURE_FAIL {which}")
    else: unreal.log(f"LINE_BOSS_PR004_V008_CAPTURE_PASS {which} {out}")
    unreal.unregister_slate_post_tick_callback(handle); handle = None
    unreal.SystemLibrary.quit_editor()
handle = unreal.register_slate_post_tick_callback(tick)
