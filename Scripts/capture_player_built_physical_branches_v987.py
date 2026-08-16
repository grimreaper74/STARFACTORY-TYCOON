"""Transient clean-map proof of the physically spaced, player-buildable A-D branch layout.

Nothing is saved. The script stages two coil-preparation packages, four local blank
buffers, four approved wider press trains at 22 m pitch, two inspection branches and
the twelve short automatic-route equivalents used by the focused runtime test.
"""
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
OUT = Path(unreal.Paths.project_saved_dir()) / (
    "ValidationScreenshots/PressShop/PlayerBuildable_v987/"
    "player_built_physical_branches_abcd.png")
TAG = unreal.Name("LB.Capture.PlayerBuiltPhysicalBranches.v987")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)


def spawn_machine(machine_id, machine_type, location):
    machine = actors.spawn_actor_from_class(unreal.LBFactoryBuildMachine, location)
    if not machine or not machine.configure(machine_id, machine_type):
        raise RuntimeError(f"machine configure failed: {machine_id}")
    return machine


def spawn_zone(zone_id, location):
    zone = actors.spawn_actor_from_class(unreal.LBPressShopStorageZone, location)
    if not zone or not zone.configure(
            zone_id, unreal.LBPressShopStorageType.PREPARED_BLANKS,
            8, unreal.Vector(300.0, 300.0, 300.0)):
        raise RuntimeError(f"storage configure failed: {zone_id}")
    return zone


def spawn_link(source, target, label):
    link = actors.spawn_actor_from_class(unreal.LBFactoryTransportLink, unreal.Vector())
    if not link or not link.configure(source, target):
        raise RuntimeError(f"transport configure failed: {label}")
    link.set_actor_label(f"LB_CAPTURE_{label}_NOT_SAVED")
    return link


prep = [
    spawn_machine("COIL-PREP-001", unreal.LBFactoryBuildMachineType.DECOILER_FEEDER,
                  unreal.Vector(-2200.0, -4800.0, 350.0)),
    spawn_machine("COIL-PREP-002", unreal.LBFactoryBuildMachineType.DECOILER_FEEDER,
                  unreal.Vector(2200.0, -4800.0, 350.0)),
]
train_x = [-3300.0, -1100.0, 1100.0, 3300.0]
buffers = [spawn_zone(f"SZ-BLANK-{chr(65+i)}", unreal.Vector(x, -2900.0, 0.0))
           for i, x in enumerate(train_x)]

specs = [
    ("TRAIN_A", "PRESS TRAIN A", "SMOT / SMOTR / ROOF OUTER", unreal.LinearColor(0.20, 0.55, 0.82, 1)),
    ("TRAIN_B", "PRESS TRAIN B", "FLOORS / TUNNEL / CROSSMEMBERS", unreal.LinearColor(0.20, 0.72, 0.38, 1)),
    ("TRAIN_C", "PRESS TRAIN C", "DOORS / BONNET / OUTER PANELS", unreal.LinearColor(0.90, 0.48, 0.12, 1)),
    ("TRAIN_D", "PRESS TRAIN D", "FRONT WINGS / WHEELHOUSES", unreal.LinearColor(0.62, 0.32, 0.78, 1)),
]
trains = []
for i, spec in enumerate(specs):
    train = actors.spawn_actor_from_class(
        unreal.LBPressTrainAStation, unreal.Vector(train_x[i], -2000.0, 0.0))
    if not train or not train.configure_train_variant(*spec) or not train.enable_completed_runtime_visual():
        raise RuntimeError(f"train configure failed: {spec[0]}")
    trains.append(train)

inspection = [
    spawn_machine("INSPECT-001", unreal.LBFactoryBuildMachineType.INSPECTION_CELL,
                  unreal.Vector(-2200.0, 5400.0, 300.0)),
    spawn_machine("INSPECT-002", unreal.LBFactoryBuildMachineType.INSPECTION_CELL,
                  unreal.Vector(2200.0, 5400.0, 300.0)),
]

for i in range(4):
    spawn_link(prep[i // 2].output_port, buffers[i].ingress_point, f"PREP_TO_BUFFER_{i}")
    spawn_link(buffers[i].egress_point, trains[i].factory_input_port, f"BUFFER_TO_TRAIN_{i}")
    spawn_link(trains[i].factory_output_port, inspection[i // 2].input_port, f"TRAIN_TO_INSPECT_{i}")

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-10500.0, -10500.0, 9200.0))
camera.tags = [TAG]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(0.0, 250.0, 450.0)), False)
camera.camera_component.set_field_of_view(59.0)

OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    OUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_started = None
handle = None


def finish(ok, detail):
    global handle
    (unreal.log if ok else unreal.log_error)(
        f"LINE_BOSS_PHYSICAL_BRANCHES_V987_{'PASS' if ok else 'FAIL'} {detail}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()


def tick(_delta):
    global capture_started
    now = time.monotonic()
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world:
        return
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, TAG)
    runtime_trains = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressTrainAStation)
    runtime_links = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBFactoryTransportLink)
    if capture_started is None and now - started >= 9.0 and cameras:
        if len(runtime_trains) != 4 or len(runtime_links) != 12:
            finish(False, f"unexpected runtime inventory trains={len(runtime_trains)} links={len(runtime_links)}")
            return
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
    elif now - started > 90.0:
        finish(False, "timeout")


handle = unreal.register_slate_post_tick_callback(tick)
