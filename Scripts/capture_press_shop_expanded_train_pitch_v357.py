"""Fresh fixed-camera evidence for isolated 22 m four-train layout v356."""
import os,time
from pathlib import Path
import unreal
unreal.EditorPythonScripting.set_keep_python_script_alive(True)
view=os.environ.get("LB_V357_VIEW","overview").lower()
views={
 "overview":((8350.0,-5350.0,2450.0),(3850.0,-1000.0,360.0),96.0),
 "aisle_ab":((850.0,-3200.0,240.0),(6500.0,-3200.0,330.0),92.0),
 "four_lines_end":((780.0,-5200.0,1350.0),(3850.0,-950.0,380.0),108.0),
}
if view not in views:raise RuntimeError(view)
out=Path(unreal.Paths.project_saved_dir())/f"ValidationScreenshots/PressShopIntegration/v357_expanded_train_pitch/{view}.png"
if out.exists():raise RuntimeError(f"Refusing to overwrite {out}")
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem);api=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level("/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainPitchCandidate_v356"):raise RuntimeError("v356 load failed")
loc,target,fov=views[view];camera=api.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator())
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(*target)),False)
camera.camera_component.set_editor_properties({"field_of_view":fov,"aspect_ratio":16.0/9.0,"constrain_aspect_ratio":True})
out.parent.mkdir(parents=True,exist_ok=True);world=unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world,"viewmode lit");unreal.SystemLibrary.execute_console_command(world,"r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation();unreal.AutomationLibrary.finish_loading_before_screenshot()
task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(out),camera=camera,force_game_view=True,delay=15)
if not task.is_valid_task():raise RuntimeError("invalid v357 task")
started=time.monotonic();handle=None
def tick(_):
 global handle
 elapsed=time.monotonic()-started
 if elapsed>=16 and out.exists() and out.stat().st_size>=1024:unreal.log(f"LB_V357_CAPTURE_PASS {view}")
 elif elapsed<90:return
 else:unreal.log_error(f"LB_V357_CAPTURE_FAIL {view}")
 if handle is not None:unreal.unregister_slate_post_tick_callback(handle);handle=None
 unreal.EditorPythonScripting.set_keep_python_script_alive(False);unreal.SystemLibrary.execute_console_command(world,"QUIT_EDITOR")
handle=unreal.register_slate_post_tick_callback(tick)
