"""Capture authored-detail PR004 candidate from fixed cameras."""
import os, time
from pathlib import Path
import unreal
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR004AuthoredDetailsCandidate_v009"
VIEWS = {"detail": ("LB_AUDIT_PR004_RobotAuthoredDetails_v009", "pr004_v009_authored_detail.png"), "cell": ("LB_INT_PR004_V009_CAM_PR004CloseDirty", "pr004_v009_cell.png"), "front": ("LB_INT_PR004_V009_CAM_FrontEndDirty", "pr004_v009_front_end.png")}
key = os.environ.get("LB_PR004_V009_CAPTURE", "detail"); label, name = VIEWS[key]
out = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v009_pr004_authored_details" / name
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP); camera=next((a for a in actors.get_all_level_actors() if a.get_actor_label()==label), None)
if camera is None: raise RuntimeError(f"Missing {label}")
out.parent.mkdir(parents=True,exist_ok=True)
if out.exists(): out.unlink()
world=unreal.EditorLevelLibrary.get_editor_world(); unreal.SystemLibrary.execute_console_command(world,"viewmode lit"); unreal.SystemLibrary.execute_console_command(world,"r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation(); unreal.AutomationLibrary.finish_loading_before_screenshot()
unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(out),camera=camera,force_game_view=True)
started=time.monotonic(); handle=None
def tick(_d):
    global handle
    if time.monotonic()-started < 3 or not out.exists() or out.stat().st_size<1024:
        if time.monotonic()-started<55:return
    unreal.unregister_slate_post_tick_callback(handle);handle=None;unreal.SystemLibrary.quit_editor()
handle=unreal.register_slate_post_tick_callback(tick)
