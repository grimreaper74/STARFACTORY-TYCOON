"""Capture one PR-005 HMI screen evidence view selected by environment."""

import os
from pathlib import Path
import unreal


capture_id = os.environ.get("LB_PR005_HMI_CAPTURE", "operator").lower()
cameras = {
    "operator": "LB_HMI_SCREEN_CAM_Operator",
    "close": "LB_HMI_SCREEN_CAM_Close",
}
if capture_id not in cameras:
    raise RuntimeError(f"Unknown LB_PR005_HMI_CAPTURE={capture_id}")
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == cameras[capture_id]), None)
if camera is None:
    raise RuntimeError(f"Missing camera {cameras[capture_id]}")
output = Path(unreal.Paths.project_saved_dir()) / f"ValidationScreenshots/PR005/HMI/Candidate_v001/pr005_hmi_{capture_id}.png"
output.parent.mkdir(parents=True, exist_ok=True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(output), camera=camera, mask_enabled=False,
    capture_hdr=False, comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes=f"PR-005 HMI commissioning screen v001 {capture_id}",
    delay=0.25, force_game_view=True)
if not task.is_valid_task():
    raise RuntimeError("Unreal rejected HMI screenshot task")
unreal.log(f"LINE_BOSS_PR005_HMI_CAPTURE_REQUESTED id={capture_id} path={output}")
