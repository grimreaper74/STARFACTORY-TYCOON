"""Create v022 with service-camera distance and low dock-level fill."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAServiceEvidenceCandidate_v021"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainADieChangeEvidenceCandidate_v022"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_die_change_evidence_v022.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v022 from v021: {TARGET}")


def one(label):
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {label}, found {len(matches)}")
    return matches[0]


wall = one("CA_MW_PTA_InstalledEvidenceBackWall")
old = wall.get_actor_location()
wall.set_actor_location(unreal.Vector(2500.0, old.y, old.z), False, False)
camera = one("CA_MW_PTA_CAM_DieChangeService")
location = unreal.Vector(2100.0, 2250.0, 900.0)
target = unreal.Vector(0.0, 2250.0, 260.0)
camera.set_actor_location(location, False, False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
camera.camera_component.set_editor_property("field_of_view", 100.0)

point_lights = []
for stage, y_cm in (("S02", 750.0), ("S03", 1500.0), ("S04", 2250.0), ("S05", 3000.0), ("S06", 3750.0)):
    light = actors_api.spawn_actor_from_class(
        unreal.PointLight, unreal.Vector(850.0, y_cm, 260.0), unreal.Rotator())
    light.set_actor_label(f"CA_MW_PTA_{stage}_DieChangeDockFill")
    light.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.TrainA.Isolated", "LB.Validation.Environment",
        "LB.Validation.DieChangeEvidencePointLighting",
        f"LB.Validation.DieChangeEvidencePointLighting.{stage}",
        "LB.Asset.Candidate.v022", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    component = light.get_editor_property("point_light_component")
    component.set_editor_property("intensity", 280.0)
    component.set_editor_property("attenuation_radius", 760.0)
    component.set_editor_property("source_radius", 90.0)
    component.set_light_color(unreal.LinearColor(0.52, 0.60, 0.58, 1.0))
    point_lights.append(light.get_actor_label())

scope_count = 0
for actor in actors_api.get_all_level_actors():
    actor_tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        scope_count += 1
        if "LB.Asset.Candidate.v022" not in actor_tags:
            actor_tags.append("LB.Asset.Candidate.v022")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])

failures = []
if len(point_lights) != 5 or scope_count != 111:
    failures.append(f"dock evidence cardinality mismatch point_lights={len(point_lights)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v022 die-change-evidence candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-die-change-evidence-v022/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V022_SERVICE_CAMERA_CLEARANCE_AND_DOCK_LEVEL_FILL__EARLY_SERVICE_CAMERA_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V022_DIE_CHANGE_EVIDENCE__NOT_PROMOTED",
    "source_map": SOURCE, "map": TARGET, "validation_wall_x_cm": 2500.0,
    "camera_location_cm": [2100.0, 2250.0, 900.0], "camera_target_cm": [0.0, 2250.0, 260.0],
    "camera_fov_deg": 100.0, "dock_point_light_count": len(point_lights),
    "dock_point_light_intensity": 280.0, "scope_actor_count": scope_count,
    "validation_environment_only": True, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
