'''Three-view proof of the floor-seated, flow-aligned approved Press Train A.'''
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP_PATH = '/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913'
OUT_DIR = Path(unreal.Paths.project_saved_dir()) / 'ValidationScreenshots/PressShop/PlayerBuildable_v964'
VIEWS = (
    ('side', unreal.Name('LB.Capture.PressTrain.v964.Side')),
    ('front', unreal.Name('LB.Capture.PressTrain.v964.Front')),
    ('overhead', unreal.Name('LB.Capture.PressTrain.v964.Overhead')),
)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP_PATH):
    raise RuntimeError(MAP_PATH)

train = actors.spawn_actor_from_class(unreal.LBPressTrainAStation, unreal.Vector(0.0, -3400.0, 0.0))
if not train.configure_train_variant('TRAIN_A', 'PRESS TRAIN A', 'SMOT / SMOTR / ROOF OUTER', unreal.LinearColor(0.20, 0.55, 0.82, 1)):
    raise RuntimeError('configure failed')
if not train.enable_completed_runtime_visual():
    raise RuntimeError('approved visual failed')

target = unreal.Vector(0.0, -300.0, 330.0)
side = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-6000.0, -300.0, 1300.0))
side.tags = [VIEWS[0][1]]
side.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(side.get_actor_location(), target), False)
side.camera_component.set_field_of_view(62.0)

front = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(0.0, -5600.0, 1050.0))
front.tags = [VIEWS[1][1]]
front.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(front.get_actor_location(), target), False)
front.camera_component.set_field_of_view(54.0)

overhead = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(0.0, -300.0, 9000.0))
overhead.tags = [VIEWS[2][1]]
overhead.set_actor_rotation(unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0), False)
overhead.camera_component.set_editor_property('projection_mode', unreal.CameraProjectionMode.ORTHOGRAPHIC)
overhead.camera_component.set_editor_property('ortho_width', 13000.0)

OUT_DIR.mkdir(parents=True, exist_ok=True)
outputs = [OUT_DIR / f'corrected_press_train_{name}.png' for name, _tag in VIEWS]
for output in outputs:
    if output.exists():
        output.unlink()

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_index = 0
capture_started = None
handle = None

def finish(ok, detail):
    global handle
    status = 'PASS' if ok else 'FAIL'
    (unreal.log if ok else unreal.log_error)(f'LINE_BOSS_PRESS_TRAIN_V964_{status} {detail}')
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()

def tick(_delta):
    global capture_index, capture_started
    now = time.monotonic()
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    trains = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)
    if len(trains) != 1:
        if now - started > 30:
            finish(False, f'unexpected train count {len(trains)}')
        return
    if not trains[0].has_completed_runtime_visual():
        finish(False, 'approved visual inactive')
        return
    if capture_index >= len(VIEWS):
        finish(True, str(OUT_DIR))
        return
    output = outputs[capture_index]
    if capture_started is None and now - started >= 10:
        cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, VIEWS[capture_index][1])
        if not cameras:
            finish(False, f'missing camera {VIEWS[capture_index][0]}')
            return
        unreal.SystemLibrary.execute_console_command(world, 'r.Streaming.FullyLoadUsedTextures 1')
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(2560, 1440, str(output), camera=cameras[0], force_game_view=True)
        if not task.is_valid_task():
            finish(False, f'invalid screenshot task {VIEWS[capture_index][0]}')
            return
        capture_started = now
    elif capture_started is not None and output.exists() and output.stat().st_size > 1024:
        capture_index += 1
        capture_started = None
    elif now - started > 160:
        finish(False, 'timeout')

handle = unreal.register_slate_post_tick_callback(tick)
