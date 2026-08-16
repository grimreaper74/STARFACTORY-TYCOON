import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP='/Game/LineBoss/Developer/Validation/Maps/LB_S01_CleaningRobot_MaterialProof_v944'; OUT=Path(unreal.Paths.project_saved_dir())/'ValidationScreenshots/PressShop/MaterialProof_v944/s01_cleaning_robot_unreal.png'; TAG=unreal.Name('LB.Capture.S01Cleaner.v944')
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
cam=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(1050,-1450,780)); cam.tags=[TAG]; cam.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cam.get_actor_location(),unreal.Vector(0,0,155)),False); cam.camera_component.set_field_of_view(58); OUT.parent.mkdir(parents=True,exist_ok=True)
if OUT.exists(): OUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate(); start=time.monotonic(); shot=None; handle=None
def finish(ok,msg):
 global handle
 (unreal.log if ok else unreal.log_error)(f"LINE_BOSS_S01_CLEANER_UNREAL_PROOF_V943_{'PASS' if ok else 'FAIL'} {msg}")
 if handle: unreal.unregister_slate_post_tick_callback(handle); handle=None
 unreal.EditorLevelLibrary.editor_end_play(); unreal.SystemLibrary.quit_editor()
def tick(_dt):
 global shot
 now=time.monotonic(); world=unreal.EditorLevelLibrary.get_game_world()
 if not world:return
 cams=unreal.GameplayStatics.get_all_actors_with_tag(world,TAG)
 if shot is None and now-start>6 and cams:
  unreal.SystemLibrary.execute_console_command(world,'r.Streaming.FullyLoadUsedTextures 1'); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation(); unreal.AutomationLibrary.finish_loading_before_screenshot(); task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(OUT),camera=cams[0],force_game_view=True)
  if not task.is_valid_task():finish(False,'invalid task');return
  shot=now
 elif shot is not None and OUT.exists() and OUT.stat().st_size>1024:finish(True,str(OUT))
 elif now-start>90:finish(False,'timeout')
handle=unreal.register_slate_post_tick_callback(tick)
