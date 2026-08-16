"""Capture one fixed view from PR-004 paint-specific candidate v012."""
import os,time
from pathlib import Path
import unreal
MAP="/Game/LineBoss/Maps/LB_PressShop_PR004PaintSpecificCandidate_v012"
VIEWS={"detail":("LB_AUDIT_PR004_RobotComplete_v012","pr004_v012_robot_complete.png"),"cell":("LB_INT_PR004_V009_CAM_PR004CloseDirty","pr004_v012_cell.png"),"front":("LB_INT_PR004_V009_CAM_FrontEndDirty","pr004_v012_front.png")}
key=os.environ.get("LB_PR004_V012_CAPTURE","detail").lower();label,name=VIEWS[key];out=Path(unreal.Paths.project_saved_dir())/"ValidationScreenshots/PressShopIntegration/v012_pr004_paint_specific"/name
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):raise RuntimeError(f"Could not load {MAP}")
camera=next((a for a in actors.get_all_level_actors() if a.get_actor_label()==label),None)
if camera is None:raise RuntimeError(f"Missing {label}")
out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():out.unlink()
world=unreal.EditorLevelLibrary.get_editor_world();unreal.SystemLibrary.execute_console_command(world,"viewmode lit");unreal.SystemLibrary.execute_console_command(world,"r.Streaming.FullyLoadUsedTextures 1");unreal.SystemLibrary.execute_console_command(world,"r.HighResScreenshotDelay 28");unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot();task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(out),camera=camera,force_game_view=True)
if not task.is_valid_task():raise RuntimeError("Invalid screenshot task")
start=time.monotonic();handle=None
def tick(_d):
 global handle
 elapsed=time.monotonic()-start
 if elapsed>=3 and out.exists() and out.stat().st_size>=1024:unreal.log(f"LINE_BOSS_PR004_PAINT_V012_CAPTURE_PASS view={key} path={out}")
 elif elapsed<55:return
 else:unreal.log_error(f"LINE_BOSS_PR004_PAINT_V012_CAPTURE_FAIL view={key}")
 if handle is not None:unreal.unregister_slate_post_tick_callback(handle);handle=None
 unreal.SystemLibrary.quit_editor()
handle=unreal.register_slate_post_tick_callback(tick)
