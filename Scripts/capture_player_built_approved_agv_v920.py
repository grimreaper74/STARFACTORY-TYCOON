"""Runtime visual proof for the approved self-contained player-built Coil AGV."""
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP="/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
OUT=Path(unreal.Paths.project_saved_dir())/"ValidationScreenshots/PressShop/PlayerBuildable_v920/player_built_approved_coil_agv.png"
TAG=unreal.Name("LB.Capture.PlayerBuiltApprovedAGV.v920")
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)
agv=actors.spawn_actor_from_class(unreal.LBCoilAGVController,unreal.Vector(-6200,-2700,29))
camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(-7000,-3500,520)); camera.tags=[TAG]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(),unreal.Vector(-6200,-2700,85)),False)
camera.camera_component.set_field_of_view(42)
OUT.parent.mkdir(parents=True,exist_ok=True)
if OUT.exists(): OUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate(); started=time.monotonic(); capture_started=None; handle=None

def finish(ok,detail):
 global handle
 (unreal.log if ok else unreal.log_error)(f"LINE_BOSS_PLAYER_AGV_V920_{'PASS' if ok else 'FAIL'} {detail}")
 if handle is not None: unreal.unregister_slate_post_tick_callback(handle); handle=None
 unreal.EditorLevelLibrary.editor_end_play(); unreal.SystemLibrary.quit_editor()

def tick(_delta):
 global capture_started
 now=time.monotonic(); world=unreal.EditorLevelLibrary.get_game_world()
 if not world:return
 cameras=unreal.GameplayStatics.get_all_actors_with_tag(world,TAG); agvs=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.LBCoilAGVController)
 if capture_started is None and now-started>=5 and cameras and agvs:
  proof=agvs[0]
  if not proof.is_using_approved_player_built_presentation(): finish(False,"approved presentation inactive"); return
  unreal.log(f"LINE_BOSS_PLAYER_AGV_V920_RUNTIME approved={proof.is_using_approved_player_built_presentation()} phase={proof.get_phase()} location={proof.get_vehicle_location()}")
  task=unreal.AutomationLibrary.take_high_res_screenshot(1600,900,str(OUT),camera=cameras[0],force_game_view=True)
  if not task.is_valid_task():finish(False,"invalid screenshot task");return
  capture_started=now
 elif capture_started is not None and OUT.exists() and OUT.stat().st_size>1024:finish(True,str(OUT))
 elif now-started>75:finish(False,"timeout")
handle=unreal.register_slate_post_tick_callback(tick)
