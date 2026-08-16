import os,time
from pathlib import Path
import unreal
MAP="/Game/LineBoss/Maps/LB_PressShop_PR004AgedDustCandidate_v013";V={"detail":("LB_AUDIT_PR004_RobotComplete_v012","pr004_v013_robot_complete.png"),"cell":("LB_INT_PR004_V009_CAM_PR004CloseDirty","pr004_v013_cell.png"),"front":("LB_INT_PR004_V009_CAM_FrontEndDirty","pr004_v013_front.png")};key=os.environ.get("LB_PR004_V013_CAPTURE","detail");label,name=V[key];out=Path(unreal.Paths.project_saved_dir())/"ValidationScreenshots/PressShopIntegration/v013_pr004_aged_dust"/name
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);levels.load_level(MAP);cam=next((a for a in actors.get_all_level_actors() if a.get_actor_label()==label),None)
if cam is None:raise RuntimeError(f"Missing {label}")
out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():out.unlink()
w=unreal.EditorLevelLibrary.get_editor_world();unreal.SystemLibrary.execute_console_command(w,"viewmode lit");unreal.SystemLibrary.execute_console_command(w,"r.Streaming.FullyLoadUsedTextures 1");unreal.SystemLibrary.execute_console_command(w,"r.HighResScreenshotDelay 28");unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot();t=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(out),camera=cam,force_game_view=True)
if not t.is_valid_task():raise RuntimeError("Invalid screenshot")
s=time.monotonic();h=None
def tick(_d):
 global h
 e=time.monotonic()-s
 if e>=3 and out.exists() and out.stat().st_size>=1024:unreal.log(f"LINE_BOSS_PR004_AGED_DUST_V013_CAPTURE_PASS view={key}")
 elif e<55:return
 else:unreal.log_error(f"LINE_BOSS_PR004_AGED_DUST_V013_CAPTURE_FAIL view={key}")
 if h is not None:unreal.unregister_slate_post_tick_callback(h);h=None
 unreal.SystemLibrary.quit_editor()
h=unreal.register_slate_post_tick_callback(tick)
