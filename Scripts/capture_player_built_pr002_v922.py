"""Runtime visual proof for the approved player-built PR002 weigh/inspection cell."""
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShop/PlayerBuildable_v922/player_built_pr002_loaded.png"
TAG = unreal.Name("LB.Capture.PlayerBuiltPR002.v922")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
station = actors.spawn_actor_from_class(unreal.LBFactoryBuildMachine, unreal.Vector(-5600, -2100, 182))
if not station.configure("PR002-CAPTURE", unreal.LBFactoryBuildMachineType.COIL_WEIGH_INSPECTION_CELL):
    raise RuntimeError("PR002 configure failed")
if not station.accept_input_unit("COIL-PR002-CAPTURE"):
    raise RuntimeError("PR002 load failed")
camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-6350, -3000, 490))
camera.tags = [TAG]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(-5600, -2100, 175)), False)
camera.camera_component.set_field_of_view(43)
OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists(): OUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic(); capture_started = None; handle = None

def finish(ok, detail):
    global handle
    (unreal.log if ok else unreal.log_error)(f"LINE_BOSS_PR002_V922_{'PASS' if ok else 'FAIL'} {detail}")
    if handle is not None: unreal.unregister_slate_post_tick_callback(handle); handle = None
    unreal.EditorLevelLibrary.editor_end_play(); unreal.SystemLibrary.quit_editor()

def tick(_delta):
    global capture_started
    now = time.monotonic(); world = unreal.EditorLevelLibrary.get_game_world()
    if not world: return
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, TAG)
    machines = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBFactoryBuildMachine)
    proof = next((m for m in machines if str(m.get_machine_id()) == "PR002-CAPTURE"), None)
    if capture_started is None and now-started >= 4 and cameras and proof:
        if not proof.is_pr002_payload_visible() and not proof.set_pr002_payload_visible(True):
            finish(False, "loaded payload invisible"); return
        task = unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, str(OUT), camera=cameras[0], force_game_view=True)
        if not task.is_valid_task(): finish(False, "invalid screenshot task"); return
        capture_started = now
    elif capture_started is not None and OUT.exists() and OUT.stat().st_size > 1024: finish(True, str(OUT))
    elif now-started > 75: finish(False, "timeout")
handle = unreal.register_slate_post_tick_callback(tick)
