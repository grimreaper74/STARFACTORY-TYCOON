"""Create v012 with the overview camera inside the validation hall envelope."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAHallBounceCandidate_v011"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAManagementCameraCandidate_v012"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_management_camera_v012.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v012 from preserved v011: {TARGET}")
matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == "CA_MW_PTA_CAM_Overview"]
if len(matches) != 1:
    raise RuntimeError(f"Expected one overview camera, found {len(matches)}")
camera = matches[0]
location = unreal.Vector(-5200.0, 2250.0, 1080.0)
target = unreal.Vector(0.0, 2250.0, 360.0)
camera.set_actor_location(location, False, False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
camera.camera_component.set_editor_property("field_of_view", 65.0)
tags = [str(tag) for tag in camera.tags]
if "LB.Asset.Candidate.v012" not in tags:
    tags.append("LB.Asset.Candidate.v012")
    camera.set_editor_property("tags", [unreal.Name(tag) for tag in tags])
failures = []
if not levels.save_current_level():
    failures.append("could not save v012 management-camera candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-management-camera-v012/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V012_OVERVIEW_CAMERA_INSIDE_HALL_WIDE_CCTV_COMPOSITION__FRESH_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V012_MANAGEMENT_CAMERA__NOT_PROMOTED",
    "source_map": SOURCE,
    "map": TARGET,
    "overview_camera_location_cm": [location.x, location.y, location.z],
    "overview_camera_target_cm": [target.x, target.y, target.z],
    "overview_camera_fov_deg": 65.0,
    "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False,
    "accepted_pr010_map_changed": False,
    "failures": failures,
    "promotion_authorized": False,
    "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
