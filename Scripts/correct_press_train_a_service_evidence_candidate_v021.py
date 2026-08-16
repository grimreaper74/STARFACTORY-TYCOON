"""Create v021 with a clear service-side camera outside the train envelope."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAServiceCameraCandidate_v020"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAServiceEvidenceCandidate_v021"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_service_evidence_v021.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v021 from v020: {TARGET}")


def one(label):
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {label}, found {len(matches)}")
    return matches[0]


# The original validation wall was only 1.5 m beyond the 15 m train envelope.
# Move it out for a legitimate fixed-camera clearance; this is evidence context,
# never a production datum.
wall = one("CA_MW_PTA_InstalledEvidenceBackWall")
wall_location = wall.get_actor_location()
wall.set_actor_location(unreal.Vector(1500.0, wall_location.y, wall_location.z), False, False)
camera = one("CA_MW_PTA_CAM_DieChangeService")
camera_location = unreal.Vector(1250.0, 2250.0, 760.0)
camera_target = unreal.Vector(0.0, 2250.0, 250.0)
camera.set_actor_location(camera_location, False, False)
camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera_location, camera_target), False)
camera.camera_component.set_editor_property("field_of_view", 86.0)

service_lights = []
for stage, y_cm in (("S02", 750.0), ("S03", 1500.0), ("S04", 2250.0), ("S05", 3000.0), ("S06", 3750.0)):
    location = unreal.Vector(1120.0, y_cm, 680.0)
    target = unreal.Vector(0.0, y_cm, 220.0)
    light = actors_api.spawn_actor_from_class(
        unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, target))
    light.set_actor_label(f"CA_MW_PTA_{stage}_DieChangeEvidenceLight")
    light.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.TrainA.Isolated", "LB.Validation.Environment",
        "LB.Validation.DieChangeEvidenceLighting", f"LB.Validation.DieChangeEvidenceLighting.{stage}",
        "LB.Asset.Candidate.v021", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    component = light.get_editor_property("rect_light_component")
    component.set_editor_property("intensity", 240.0)
    component.set_editor_property("source_width", 420.0)
    component.set_editor_property("source_height", 90.0)
    component.set_editor_property("attenuation_radius", 900.0)
    component.set_light_color(unreal.LinearColor(0.58, 0.66, 0.63, 1.0))
    service_lights.append(light.get_actor_label())

scope_count = 0
for value in actors_api.get_all_level_actors():
    actor_tags = [str(tag) for tag in value.tags]
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        scope_count += 1
        if "LB.Asset.Candidate.v021" not in actor_tags:
            actor_tags.append("LB.Asset.Candidate.v021")
            value.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])

failures = []
if len(service_lights) != 5 or scope_count != 106:
    failures.append(f"service evidence cardinality mismatch lights={len(service_lights)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v021 service-evidence candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-service-evidence-v021/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V021_SERVICE_CAMERA_OUTSIDE_ENVELOPE_AND_DIE_CHANGE_EVIDENCE_LIGHTING__EARLY_SERVICE_CAMERA_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V021_SERVICE_EVIDENCE__NOT_PROMOTED",
    "source_map": SOURCE, "map": TARGET, "validation_wall_x_cm": 1500.0,
    "camera_location_cm": [1250.0, 2250.0, 760.0], "camera_target_cm": [0.0, 2250.0, 250.0],
    "camera_fov_deg": 86.0, "service_evidence_light_count": len(service_lights),
    "service_evidence_light_intensity": 240.0, "scope_actor_count": scope_count,
    "validation_environment_only": True, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
