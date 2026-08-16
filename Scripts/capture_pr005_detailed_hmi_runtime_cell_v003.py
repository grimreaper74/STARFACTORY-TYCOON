"""Transient PR005 detailed-HMI player-camera evidence.
Stages a single real ALBFactoryBuildMachine in temporary simulation on v913, captures it
from the measured overview-camera family, then exits without saving the protected map.
"""
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShop/PR005_DetailedHMI_v001/pr005_runtime_cell_overview_v003.png"
TAG = unreal.Name("LB.Capture.PR005DetailedHMI.RuntimeCell.v003")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

# Transient placement mirrors the proven player-built branch capture; this actor is
# never saved into v913 and has no transport links or interaction changes.
pr005 = actors.spawn_actor_from_class(
    unreal.LBFactoryBuildMachine, unreal.Vector(0.0, -1400.0, 350.0), unreal.Rotator())
if not pr005 or not pr005.configure("PR005-ART-REVIEW", unreal.LBFactoryBuildMachineType.DECOILER_FEEDER):
    raise RuntimeError("could not configure transient PR005 review actor")
pr005.set_actor_label("LB_CAPTURE_PR005_DETAILED_HMI_RUNTIME_CELL_NOT_SAVED")

camera = actors.spawn_actor_from_class(
    unreal.CameraActor, unreal.Vector(-7200.0, -7800.0, 7600.0), unreal.Rotator())
camera.set_actor_label("LB_CAPTURE_PR005_DETAILED_HMI_OVERVIEW_V003_NOT_SAVED")
camera.tags = [TAG]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(0.0, -1400.0, 250.0)), False)
camera.camera_component.set_field_of_view(48.0)
OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    raise RuntimeError(f"Refusing to overwrite evidence: {OUT}")

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_started = None
handle = None
runtime_checked = False

def finish(ok, message):
    global handle
    (unreal.log if ok else unreal.log_error)(
        f"LINE_BOSS_PR005_DETAILED_HMI_RUNTIME_CELL_{'PASS' if ok else 'FAIL'} {message}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()

def tick(_delta):
    global capture_started, runtime_checked
    now = time.monotonic()
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, TAG)
    if not runtime_checked:
        machines = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBFactoryBuildMachine)
        pr005s = [m for m in machines if str(m.get_editor_property("machine_id")) == "PR005-ART-REVIEW"]
        if len(pr005s) != 1:
            finish(False, f"expected one transient PR005; found {len(pr005s)}")
            return
        hmi = next((c for c in pr005s[0].get_components_by_class(unreal.StaticMeshComponent)
                    if c.get_name() == "PR005DetailedHMIVisual"), None)
        if hmi is None:
            finish(False, "detailed HMI component missing")
            return
        mesh = hmi.get_editor_property("static_mesh")
        visible = hmi.is_visible()
        collision = hmi.get_collision_enabled()
        nav = hmi.can_ever_affect_navigation()
        materials = hmi.get_materials()
        unreal.log(
            "LINE_BOSS_PR005_DETAILED_HMI_RUNTIME_CELL "
            f"visible={visible} mesh={mesh} collision={collision} nav={nav} "
            f"materials={materials} transform={hmi.get_relative_transform()}"
        )
        if not visible or mesh is None or collision != unreal.CollisionEnabled.NO_COLLISION or nav:
            finish(False, "HMI visual-only assertion failed")
            return
        runtime_checked = True
    if capture_started is None and now - started >= 9.0 and cameras:
        unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
        unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1920, 1080, str(OUT), camera=cameras[0], force_game_view=True)
        if not task.is_valid_task():
            finish(False, "invalid screenshot task")
            return
        capture_started = now
    elif capture_started is not None and OUT.exists() and OUT.stat().st_size > 1024:
        finish(True, str(OUT))
    elif now - started > 100.0:
        finish(False, "timeout")

handle = unreal.register_slate_post_tick_callback(tick)
