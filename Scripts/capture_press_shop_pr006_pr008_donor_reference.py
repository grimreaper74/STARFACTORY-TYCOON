"""Capture the retained donor release view for one PR006-PR008 station."""
import os
import time
from pathlib import Path

import unreal


REFERENCES = {
    "pr006": (
        "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208",
        "LB_PR006_V208_CAM_ConnectedRelease",
        "donor_v208_pr006_connected_release.png",
    ),
    "pr007": (
        "/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209",
        "LB_PR007_V209_CAM_ConnectedRelease",
        "donor_v209_pr007_connected_release.png",
    ),
    "pr008": (
        "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210",
        "LB_PR008_V210_CAM_AuthoredAnchorProcess",
        "donor_v210_pr008_authored_anchor.png",
    ),
}

capture_id = os.environ.get("LB_DONOR_CAPTURE", "pr006").lower()
map_path, camera_label, filename = REFERENCES[capture_id]
output = (
    Path(unreal.Paths.project_saved_dir())
    / "ValidationScreenshots/PressShopIntegration/pr006_pr008_donor_reference"
    / filename
)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(map_path):
    raise RuntimeError(map_path)
camera = next(
    (actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == camera_label),
    None,
)
if camera is None:
    raise RuntimeError(camera_label)
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
    1920,
    1080,
    str(output),
    camera=camera,
    mask_enabled=False,
    capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Retained donor reference {capture_id}",
    delay=0.0,
    force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError(capture_id)
started = time.monotonic()
handle = None


def finish(_delta):
    global handle
    elapsed = time.monotonic() - started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LB_DONOR_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 65.0:
        return
    else:
        unreal.log_error(f"LB_DONOR_CAPTURE_FAIL id={capture_id}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle)
        handle = None
    unreal.SystemLibrary.quit_editor()


handle = unreal.register_slate_post_tick_callback(finish)
