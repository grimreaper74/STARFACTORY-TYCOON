import os,time
from pathlib import Path
import unreal
MAP="/Game/LineBoss/Maps/LB_PressShop_PR004SafetyPaintCandidate_v010";V={"detail":("LB_AUDIT_PR004_RobotAuthoredDetails_v009","pr004_v010_detail.png"),"cell":("LB_INT_PR004_V009_CAM_PR004CloseDirty","pr004_v010_cell.png"),"front":("LB_INT_PR004_V009_CAM_FrontEndDirty","pr004_v010_front.png")};key=os.environ.get("LB_PR004_V010_CAPTURE","detail");label,name=V[key];out=Path(unreal.Paths.project_saved_dir())/"ValidationScreenshots/PressShopIntegration/v010_pr004_safety_paint"/name
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem);levels.load_level(MAP);camera=next(a for a in actors.get_all_level_actors() if a.get_actor_label()==label);out.parent.mkdir(parents=True,exist_ok=True)
if out.exists():out.unlink()
world=unreal.EditorLevelLibrary.get_editor_world();unreal.SystemLibrary.execute_console_command(world,"viewmode lit");unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot();unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(out),camera=camera,force_game_view=True);start=time.monotonic();handle=None
def tick(_d):
 global handle
 if time.monotonic()-start<3 or not out.exists() or out.stat().st_size<1024:
  if time.monotonic()-start<55:return
 unreal.unregister_slate_post_tick_callback(handle);handle=None;unreal.SystemLibrary.quit_editor()
handle=unreal.register_slate_post_tick_callback(tick)
