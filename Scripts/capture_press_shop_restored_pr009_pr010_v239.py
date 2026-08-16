"""Capture restored PR009/PR010 and their installed handoff in v239."""

import os
import time
from pathlib import Path

import unreal


candidate = os.environ.get("LB_RESTORED_MACHINE_CANDIDATE", "v239").lower()
MAP = f"/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_{candidate}"
CAPTURES = {
    "pr009": {
        "location": (-620.0, -1190.0, 525.0),
        "target": (450.0, -2000.0, 170.0),
        "fov": 52.0,
        "filename": "v239_pr009_restored_process.png",
    },
    "pr010": {
        "location": (2800.0, -4200.0, 950.0),
        "target": (1250.0, -2000.0, 160.0),
        "fov": 58.0,
        "filename": "v239_pr010_restored_overview.png",
    },
    "chain": {
        "location": (-1500.0, -3500.0, 760.0),
        "target": (650.0, -1950.0, 170.0),
        "fov": 62.0,
        "filename": "v239_pr008_to_trains_restored_chain.png",
    },
    "interface": {
        "location": (-300.0, -4700.0, 1250.0),
        "target": (1350.0, -2000.0, 120.0),
        "fov": 60.0,
        "filename": "v239_pr010_train_bc_interface.png",
    },
}
capture_id = os.environ.get("LB_V239_CAPTURE", "chain").lower()
if capture_id not in CAPTURES:
    raise RuntimeError(capture_id)
spec = CAPTURES[capture_id]
filename = spec["filename"].replace("v239", candidate)
output = Path(unreal.Paths.project_saved_dir()) / f"ValidationScreenshots/PressShopIntegration/{candidate}_restored_pr009_pr010" / filename
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*spec["location"]), unreal.Rotator())
if camera is None:
    raise RuntimeError("could not create transient v239 evidence camera")
camera.set_actor_label(f"LB_V239_TRANSIENT_CAM_{capture_id.upper()}")
if "target" in spec:
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(
        camera.get_actor_location(), unreal.Vector(*spec["target"])), False)
else:
    camera.set_actor_rotation(unreal.Rotator(*spec["rotation"]), False)
camera.camera_component.set_editor_properties({
    "field_of_view": spec["fov"], "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True})
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 24")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(output), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Cairnwell Moorcross {candidate} restored accepted PR009 PR010 {capture_id}",
    delay=0.0, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError(f"invalid screenshot task for {capture_id}")
started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LB_V239_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 65.0:
        return
    else:
        unreal.log_error(f"LB_V239_CAPTURE_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(finish)
