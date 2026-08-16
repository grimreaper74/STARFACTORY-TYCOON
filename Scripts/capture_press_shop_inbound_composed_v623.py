"""Transient wide evidence camera for v616; never saves or mutates the map."""
from pathlib import Path
import time
import unreal


MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundWrappedTrailerCandidate_v616"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/inbound_wrapped_trailer_v623/01_inbound_wide.png"

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)

camera = actors.spawn_actor_from_class(
    unreal.CameraActor, unreal.Vector(-18000.0, 4200.0, 2450.0), unreal.Rotator())
camera.set_actor_label("LB_CAM_TRANSIENT_InboundWide_v623")
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
    camera.get_actor_location(), unreal.Vector(-13300.0, -2000.0, 250.0)), False)
camera.camera_component.set_editor_properties({
    "field_of_view": 67.0,
    "aspect_ratio": 16.0 / 9.0,
    "constrain_aspect_ratio": True,
})

OUT.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(OUT), camera=camera, mask_enabled=False, capture_hdr=False,
    delay=8, force_game_view=True)
started = time.monotonic()
handle = None


def tick(_dt):
    global handle
    elapsed = time.monotonic() - started
    if elapsed < 9.0 or (not task.is_task_done() and elapsed < 60.0):
        return
    ok = OUT.exists() and OUT.stat().st_size > 1024
    unreal.log(("LINE_BOSS_INBOUND_V623_CAPTURE_PASS " if ok else
                "LINE_BOSS_INBOUND_V623_CAPTURE_FAIL ") + str(OUT))
    unreal.unregister_slate_post_tick_callback(handle)
    handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(tick)
