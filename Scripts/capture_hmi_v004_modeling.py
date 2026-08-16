"""Capture the HMI v004 Unreal Modeling candidate without opening the UI."""

from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_HMI04_ModelingValidation"
CAMERA = "LB_CAM_HMI04_Front"
OUTPUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/HMI/shared_hmi_v004_unreal_modeling_front.png"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(f"Missing fixed camera {CAMERA}")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
# Headless editor sessions can inherit a debug/detail-lighting view from the
# last saved viewport.  That view deliberately turns every material white.
# Force the final shaded game view before taking evidence.
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.SystemLibrary.execute_console_command(world, "r.ForceDebugViewModes 0")
unreal.EditorLevelLibrary.editor_set_game_view(True)
# The materials are generated and compiled by the preceding headless Modeling
# pass.  Do not photograph Unreal's white checker/compile fallback.
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(OUTPUT), camera=camera, mask_enabled=False,
    capture_hdr=False, comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes="Line Boss HMI v004 Unreal Modeling validation", delay=0.0,
    force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("Unreal did not create a valid screenshot task")
unreal.log(f"LINE_BOSS_HMI04_SCREENSHOT_REQUESTED path={OUTPUT}")
