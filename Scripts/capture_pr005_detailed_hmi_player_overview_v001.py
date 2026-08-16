import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShop/PressShop/PR005_DetailedHMI_v001/player_overview_candidate.png"
TAG = unreal.Name("LB.Capture.PR005DetailedHMI.v001")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

camera = actors.spawn_actor_from_class(
    unreal.CameraActor,
    unreal.Vector(-6051.84, 4237.55, 9456.13),
    unreal.Rotator(),
)
camera.set_actor_label("LB_CAPTURE_PR005DetailedHMI_v001_NOT_SAVED")
camera.tags = [TAG]
camera.set_actor_rotation(
    unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(0.0, 0.0, 0.0)),
    False,
)
camera.camera_component.set_field_of_view(48.0)
OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    OUT.unlink()

unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_started = None
handle = None
runtime_audited = False\npr005_audited = False

def finish(ok, message):
    global handle
    (unreal.log if ok else unreal.log_error)(f"LINE_BOSS_PR005_DETAILED_HMI_PLAYER_CAPTURE_{'PASS' if ok else 'FAIL'} {message}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()

def tick(_delta):
    global capture_started, runtime_audited, pr005_audited
    now = time.monotonic()
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    runtime_cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, TAG)
    if not runtime_audited:
        meshes = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor)
        floors = [a for a in meshes if abs(a.get_actor_location().z + 25.0) < 0.1]
        roofs = [a for a in meshes if a.get_actor_location().z >= 1600.0]
        unreal.log(f"LINE_BOSS_PR005_DETAILED_HMI_RUNTIME_MESHES count={len(meshes)} floors={len(floors)}")
        for roof in roofs:
            unreal.log(f"LINE_BOSS_PR005_DETAILED_HMI_RUNTIME_ROOF name={roof.get_name()} hidden={roof.get_editor_property('hidden')} component_visible={roof.static_mesh_component.is_visible()} z={roof.get_actor_location().z}")
        for sample in meshes[:8]:
            unreal.log(f"LINE_BOSS_PR005_DETAILED_HMI_RUNTIME_SAMPLE name={sample.get_name()} loc={sample.get_actor_location()} scale={sample.get_actor_scale3d()}")
        for floor in floors:
            component = floor.static_mesh_component
            unreal.log(
                f"LINE_BOSS_PR005_DETAILED_HMI_RUNTIME_FLOOR name={floor.get_name()} "
                f"visible={component.is_visible()} scale={floor.get_actor_scale3d()} "
                f"mesh={component.static_mesh} materials={component.get_materials()}"
            )
        runtime_audited = True
    if not pr005_audited:
        machines = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBFactoryBuildMachine)
        pr005 = [m for m in machines if str(m.get_editor_property("machine_id")) == "PR005"]
        if len(pr005) != 1:
            finish(False, f"expected exactly one runtime PR005; found {len(pr005)}")
            return
        components = pr005[0].get_components_by_class(unreal.StaticMeshComponent)
        hmi = next((c for c in components if c.get_name() == "PR005DetailedHMIVisual"), None)
        if hmi is None:
            finish(False, "PR005 detailed HMI component missing at runtime")
            return
        mesh = hmi.get_editor_property("static_mesh")
        visible = hmi.is_visible()
        collision = hmi.get_collision_enabled()
        nav = hmi.can_ever_affect_navigation()
        unreal.log(f"LINE_BOSS_PR005_DETAILED_HMI_RUNTIME component={hmi.get_name()} visible={visible} mesh={mesh} collision={collision} nav={nav} transform={hmi.get_relative_transform()}")
        if not visible or mesh is None or collision != unreal.CollisionEnabled.NO_COLLISION or nav:
            finish(False, "PR005 detailed HMI runtime safety/visibility assertion failed")
            return
        pr005_audited = True
    if capture_started is None and now - started >= 5.0 and runtime_cameras:
        unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
        unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
        unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 32")
        unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1280, 720, str(OUT), camera=runtime_cameras[0], force_game_view=True)
        if not task.is_valid_task():
            finish(False, "invalid screenshot task")
            return
        capture_started = now
    elif capture_started is not None and OUT.exists() and OUT.stat().st_size >= 1024:
        finish(True, str(OUT))
    elif now - started > 75.0:
        finish(False, "timeout")

handle = unreal.register_slate_post_tick_callback(tick)

