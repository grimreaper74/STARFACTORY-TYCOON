"""Runtime proof for grounded player-built approved wrapped-coil storage."""
import time
from pathlib import Path
import unreal

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
MAP = "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShop/PlayerBuildable_v917/player_built_coil_storage.png"
TAG = unreal.Name("LB.Capture.PlayerBuiltCoilStorage.v917")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

zone = actors.spawn_actor_from_class(unreal.LBPressShopStorageZone, unreal.Vector(0, 0, 125))
if not zone.configure("SZ-COIL-PROOF-001", unreal.LBPressShopStorageType.BARE_COILS, 12, unreal.Vector(710, 650, 125)):
    raise RuntimeError("storage configure")
if not zone.configure_layout(6, 2, unreal.Vector2D(220, 600), 25):
    raise RuntimeError("storage layout")
if not zone.try_store(7):
    raise RuntimeError("storage load")

camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(-2100, -2300, 1500))
camera.tags = [TAG]
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(0, 0, 90)), False)
camera.camera_component.set_field_of_view(48)
OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists(): OUT.unlink()
unreal.EditorLevelLibrary.editor_play_simulate()
started = time.monotonic()
capture_started = None
handle = None

def finish(ok, detail):
    global handle
    (unreal.log if ok else unreal.log_error)(f"LINE_BOSS_PLAYER_COIL_STORAGE_V917_{'PASS' if ok else 'FAIL'} {detail}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.EditorLevelLibrary.editor_end_play()
    unreal.SystemLibrary.quit_editor()

def tick(_delta):
    global capture_started
    now = time.monotonic()
    world = unreal.EditorLevelLibrary.get_game_world()
    if not world: return
    cameras = unreal.GameplayStatics.get_all_actors_with_tag(world, TAG)
    zones = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.LBPressShopStorageZone)
    if capture_started is None and now - started >= 5 and cameras and zones:
        proof = next((z for z in zones if z.get_zone_id() == "SZ-COIL-PROOF-001"), None)
        if not proof: return
        unreal.log(f"LINE_BOSS_PLAYER_COIL_STORAGE_V917_RUNTIME stands={proof.get_generated_stand_count()} units={proof.get_visible_stored_unit_count()} stand_bottom={proof.get_first_stand_bottom_world_z():.3f} coil_bottom={proof.get_first_stored_unit_bottom_world_z():.3f}")
        task = unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, str(OUT), camera=cameras[0], force_game_view=True)
        if not task.is_valid_task():
            finish(False, "invalid screenshot task")
            return
        capture_started = now
    elif capture_started is not None and OUT.exists() and OUT.stat().st_size > 1024:
        finish(True, str(OUT))
    elif now - started > 75:
        finish(False, "timeout")

handle = unreal.register_slate_post_tick_callback(tick)
