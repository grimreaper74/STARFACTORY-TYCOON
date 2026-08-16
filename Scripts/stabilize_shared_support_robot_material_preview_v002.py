"""Stabilize the v002 material preview when it is opened directly.

The initial duplicate-and-load run reproduced UE 5.8's known unattended
old-world leak.  This script intentionally performs no map switch; launch the
editor with the v002 map as its command-line map.
"""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Developer/Validation/LB_SupportRobot_Materials_Candidate_v001"
DEST = "/Game/LineBoss/Developer/Validation/LB_SupportRobot_Materials_Candidate_v002"
AUDIT = ROOT / "Saved/Audits/lb_support_robot_shared_material_preview_v002.json"
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not lib.does_asset_exist(SOURCE) or not lib.does_asset_exist(DEST):
    raise RuntimeError("The preserved v001 source and failed-run v002 clone must both exist")
world = unreal.EditorLevelLibrary.get_editor_world()
current_package = world.get_outermost().get_name() if world is not None else ""
if current_package != DEST:
    raise RuntimeError(f"One-map rule violation: opened {current_package}, expected {DEST}")

camera = next((actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == "LB_CAM_SupportRobot_MaterialPreview_v001"), None)
if camera is None:
    raise RuntimeError("Missing v001 fixed camera")
camera.set_actor_label("LB_CAM_SupportRobot_MaterialPreview_v002")
settings = camera.get_editor_property("camera_component").get_editor_property("post_process_settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": -2.0,
})

# Reduce local fills so the chart reveals hue/roughness instead of clipping.
light_changes = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label == "LB_MAT_V001_FillLeft":
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 180.0)
        light_changes.append({"actor": label, "intensity": 180.0})
    elif label == "LB_MAT_V001_FillRight":
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 140.0)
        light_changes.append({"actor": label, "intensity": 140.0})

if not levels.save_current_level():
    raise RuntimeError(f"Could not save {DEST}")
result = {
    "$schema": "line-boss/audit/lb-support-robot-shared-material-preview-v002",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "FIXED_EXPOSURE_PREVIEW_BUILT__FRESH_SCREENSHOT_REQUIRED__NOT_PROMOTED",
    "source_map": SOURCE,
    "map": DEST,
    "camera": camera.get_actor_label(),
    "exposure": {"method": "AEM_BASIC", "min": 1.0, "max": 1.0, "bias": -2.0},
    "light_changes": light_changes,
    "material_assets_modified": False,
    "initial_failed_run_log": "Saved/Logs/LB_SupportRobot_MaterialPreview_v002_Build.log",
    "initial_failed_run_note": "The duplicate succeeded, then a same-process map switch triggered UE 5.8 old-world leak protection. This direct-map process is authoritative.",
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_SUPPORT_ROBOT_MATERIAL_PREVIEW_V002_BUILT audit={AUDIT}")
unreal.SystemLibrary.quit_editor()
