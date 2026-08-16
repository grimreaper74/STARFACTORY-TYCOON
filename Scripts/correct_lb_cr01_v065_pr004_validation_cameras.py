"""Correct only cameras in the isolated CR01 v065 PR-004 lighting proof map."""

from datetime import datetime, timezone
import json
from pathlib import Path

import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_Candidate_v065_PR004Lighting"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/lb_cr01_v065_pr004_camera_correction.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

specs = {
    "LB_CR01_v065_PR004_CAM_Mothballed_Oblique": ((-5550.0, -3650.0, 225.0), (-6100.0, -3300.0, 62.0), 48.0),
    "LB_CR01_v065_PR004_CAM_Mothballed_Left": ((-6100.0, -3900.0, 140.0), (-6100.0, -3300.0, 58.0), 44.0),
    "LB_CR01_v065_PR004_CAM_Restored_Oblique": ((-5550.0, -3300.0, 225.0), (-6100.0, -2850.0, 62.0), 48.0),
    "LB_CR01_v065_PR004_CAM_Restored_Front": ((-5500.0, -2850.0, 140.0), (-6100.0, -2850.0, 58.0), 44.0),
}
found = {}
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label not in specs:
        continue
    location, target, fov = specs[label]
    position = unreal.Vector(*location)
    actor.set_actor_location(position, False, False)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(position, unreal.Vector(*target)), False)
    component = actor.get_editor_property("camera_component")
    component.set_editor_property("field_of_view", fov)
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": 1.10,
    })
    found[label] = {"location_cm": list(location), "target_cm": list(target), "fov": fov, "exposure_bias": 1.10}

if set(found) != set(specs):
    raise RuntimeError(f"Camera correction incomplete: missing {sorted(set(specs) - set(found))}")
if not levels.save_current_level():
    raise RuntimeError(f"Could not save corrected validation map {MAP}")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "map": MAP,
    "status": "ISOLATED_VALIDATION_CAMERAS_CORRECTED__ACCEPTED_PR004_V006_UNCHANGED",
    "cameras": found,
}, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LINE_BOSS_CR01_V065_PR004_CAMERA_CORRECTION_PASS cameras={len(found)} audit={OUT}")
