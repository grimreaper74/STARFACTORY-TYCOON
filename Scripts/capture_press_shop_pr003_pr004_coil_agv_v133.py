"""Capture one fixed coil-AGV v133 view per clean editor process."""

import os
import time
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilAGVCandidate_v133"
CAPTURES = {
    "loaded": ("LB_PR003_PR004_V133_CAM_LoadedApproach", "press_shop_v133_coil_agv_loaded_approach.png"),
    "dock": ("LB_PR003_PR004_V133_CAM_DockAndPR004", "press_shop_v133_coil_agv_dock_pr004.png"),
    "route": ("LB_PR003_PR004_V133_CAM_RouteOverview", "press_shop_v133_coil_agv_route_overview.png"),
}
capture_id = os.environ.get("LB_COIL_AGV_V133_CAPTURE", "loaded").lower()
if capture_id not in CAPTURES:
    raise RuntimeError(capture_id)
camera_label, filename = CAPTURES[capture_id]
output = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PressShopIntegration/v133_coil_agv" / filename
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == camera_label), None)
if camera is None:
    raise RuntimeError(camera_label)
output.parent.mkdir(parents=True, exist_ok=True)
if output.exists():
    output.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.Streaming.FullyLoadUsedTextures 1")
unreal.SystemLibrary.execute_console_command(world, "r.HighResScreenshotDelay 20")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(1920,1080,str(output),camera=camera,mask_enabled=False,capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"Cairnwell owner-directed PR003-PR004 coil AGV v133: {capture_id}",delay=0.0,force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError(f"invalid screenshot task for {capture_id}")
started = time.monotonic()
handle = None
def finish(_delta):
    global handle
    elapsed = time.monotonic()-started
    if elapsed >= 3.0 and output.exists() and output.stat().st_size >= 1024:
        unreal.log(f"LB_COIL_AGV_V133_CAPTURE_PASS id={capture_id} path={output}")
    elif elapsed < 55.0:
        return
    else:
        unreal.log_error(f"LB_COIL_AGV_V133_CAPTURE_FAIL id={capture_id} path={output}")
    if handle is not None:
        unreal.unregister_slate_post_tick_callback(handle); handle=None
    unreal.SystemLibrary.quit_editor()
handle = unreal.register_slate_post_tick_callback(finish)
