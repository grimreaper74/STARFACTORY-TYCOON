"""Clean-map runtime orientation and spacing proof for player-buildable wider Press Trains A-D."""
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShop/PlayerBuildable_v924/player_built_new_press_trains_abcd.png"
TAG = unreal.Name("LB.Capture.PlayerBuiltNewTrainsABCD.v924")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP): raise RuntimeError(MAP)

specs = [
    ("TRAIN_A", "PRESS TRAIN A", "SMOT / SMOTR / ROOF OUTER", unreal.LinearColor(0.20, 0.55, 0.82, 1)),
    ("TRAIN_B", "PRESS TRAIN B", "FLOORS / TUNNEL / CROSSMEMBERS", unreal.LinearColor(0.20, 0.72, 0.38, 1)),
    ("TRAIN_C", "PRESS TRAIN C", "DOORS / BONNET / OUTER PANELS", unreal.LinearColor(0.90, 0.48, 0.12, 1)),
    ("TRAIN_D", "PRESS TRAIN D", "FRONT WINGS / WHEELHOUSES", unreal.LinearColor(0.62, 0.32, 0.78, 1)),
]
for index, spec in enumerate(specs):
    train = actors.spawn_actor_from_class(unreal.LBPressTrainAStation,
        unreal.Vector(-3300.0 + index * 2200.0, -2350.0, 0.0))
    if not train.configure_train_variant(spec[0], spec[1], spec[2], spec[3]):
        raise RuntimeError(f"configure failed {spec[0]}")
    if not train.enable_completed_runtime_visual():
        raise RuntimeError(f"visual failed {spec[0]}")

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-8800, -7600, 6100))
camera.tags = [TAG]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(0, 350, 330)), False)
camera.camera_component.set_field_of_view(56)
OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists(): OUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate(); started=time.monotonic(); capture_started=None; handle=None

def finish(ok, detail):
    global handle
    (unreal.log if ok else unreal.log_error)(f"LINE_BOSS_NEW_TRAINS_ABCD_V924_{'PASS' if ok else 'FAIL'} {detail}")
    if handle is not None: unreal.unregister_slate_post_tick_callback(handle); handle=None
    unreal.EditorLevelLibrary.editor_end_play(); unreal.SystemLibrary.quit_editor()

def tick(_delta):
    global capture_started
    now=time.monotonic(); world=unreal.EditorLevelLibrary.get_game_world()
    if not world: return
    cameras=unreal.GameplayStatics.get_all_actors_with_tag(world,TAG)
    trains=unreal.GameplayStatics.get_all_actors_of_class(world,unreal.LBPressTrainAStation)
    if capture_started is None and now-started>=7 and cameras and len(trains)==4:
        if not all(t.has_completed_runtime_visual() for t in trains): finish(False,"approved visuals inactive"); return
        task=unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(OUT),camera=cameras[0],force_game_view=True)
        if not task.is_valid_task(): finish(False,"invalid screenshot task"); return
        capture_started=now
    elif capture_started is not None and OUT.exists() and OUT.stat().st_size>1024: finish(True,str(OUT))
    elif now-started>90: finish(False,"timeout")
handle=unreal.register_slate_post_tick_callback(tick)
