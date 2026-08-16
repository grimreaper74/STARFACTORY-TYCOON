"""Capture current PR-005 viewport path without replacing prior evidence."""

from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation"
CAMERA = "LB_CAM_PR005_Overview"
OUT = Path(unreal.Paths.project_saved_dir()) / "ValidationScreenshots/PR005/Diagnostic/pr005_overview_highres_diagnostic.png"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == CAMERA), None)
if camera is None:
    raise RuntimeError(f"Missing {CAMERA}")
OUT.parent.mkdir(parents=True, exist_ok=True)
if OUT.exists():
    OUT.unlink()
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "viewmode lit")
unreal.EditorLevelLibrary.editor_set_game_view(True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.AutomationLibrary.finish_loading_before_screenshot()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, str(OUT), camera=camera, mask_enabled=False, capture_hdr=False,
    comparison_tolerance=unreal.ComparisonTolerance.LOW,
    comparison_notes="PR005 current high-res A/B diagnostic", delay=0.0, force_game_view=True,
)
if not task.is_valid_task():
    raise RuntimeError("No high-res task")
unreal.log(f"LINE_BOSS_PR005_HIGHRES_DIAGNOSTIC={OUT}")
