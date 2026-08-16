"""Capture the fixed close-control Cairnwell PR-005 branding candidate."""

from pathlib import Path
import unreal

CAMERA = "LB_BRAND_PR005_CAM_HMI"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/Brand/Candidate_v001/cairnwell_pr005_asset_plate_hmi.png"

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
camera = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(f"Missing camera {CAMERA}")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.ForceDebugViewModes 0")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(OUTPUT), camera=camera, mask_enabled=False,
    capture_hdr=False, comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes="Cairnwell PR-005 asset plate v001", delay=0.25,
    force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("Unreal rejected the PR-005 screenshot task")
unreal.log(f"LINE_BOSS_CAIRNWELL_PR005_CAPTURE_REQUESTED path={OUTPUT}")
