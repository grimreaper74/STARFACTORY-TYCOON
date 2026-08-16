"""Create v006 with process-bay lighting and corrected close evidence cameras."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainACCTVOpenBayCandidate_v005"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAInternalReadabilityCandidate_v006"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_internal_readability_v006.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary

if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v006 from preserved v005: {TARGET}")


def add_tag(actor, value):
    values = [str(tag) for tag in actor.tags]
    if value not in values:
        values.append(value)
        actor.set_editor_property("tags", [unreal.Name(tag) for tag in values])


stage_y_cm = (0.0, 750.0, 1500.0, 2250.0, 3000.0, 3750.0, 4500.0)
bay_lights = []
for index, y in enumerate(stage_y_cm, start=1):
    light = actors_api.spawn_actor_from_class(
        unreal.PointLight,
        unreal.Vector(-40.0, y, 320.0),
        unreal.Rotator(),
    )
    light.set_actor_label(f"CA_MW_PTA_ProcessBayLight_{index:02d}")
    light.tags = [
        unreal.Name("LB.PressTrain.TrainA.Isolated"),
        unreal.Name("LB.Validation.Environment"),
        unreal.Name("LB.Validation.ProcessBayLighting"),
        unreal.Name("LB.Asset.Candidate.v006"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    component = light.get_editor_property("point_light_component")
    component.set_editor_property("intensity", 850.0)
    component.set_editor_property("attenuation_radius", 620.0)
    component.set_editor_property("source_radius", 18.0)
    component.set_light_color(unreal.LinearColor(0.58, 0.68, 0.64, 1.0))
    bay_lights.append(light.get_actor_label())

# Slightly stronger external fill retains dark foundry values while separating the
# lower slide/die/bolster silhouettes and safety rails from the black background.
for actor in actors_api.get_all_level_actors():
    if actor.get_actor_label().startswith("CA_MW_PTA_IsolatedFill_"):
        actor.get_editor_property("rect_light_component").set_editor_property("intensity", 680.0)
    actor_tags = {str(tag) for tag in actor.tags}
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        add_tag(actor, "LB.Asset.Candidate.v006")


def set_camera(label, location, target, fov):
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one camera {label}, found {len(matches)}")
    actor = matches[0]
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    actor.camera_component.set_editor_property("field_of_view", fov)


set_camera(
    "CA_MW_PTA_CAM_Hero",
    unreal.Vector(-2750.0, -1650.0, 1380.0),
    unreal.Vector(0.0, 2250.0, 390.0),
    55.0,
)
set_camera(
    "CA_MW_PTA_CAM_DrawStage",
    unreal.Vector(-2250.0, 650.0, 980.0),
    unreal.Vector(0.0, 900.0, 340.0),
    50.0,
)

failures = []
if len(bay_lights) != 7:
    failures.append(f"expected seven process-bay lights, found {len(bay_lights)}")
if not levels.save_current_level():
    failures.append("could not save v006 internal-readability candidate")

report = {
    "$schema": "cairnwell/audit/press-train-a-internal-readability-v006/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V006_SEVEN_PROCESS_BAY_LIGHTS_FIXED_CAMERA_READABILITY__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V006_INTERNAL_READABILITY__NOT_PROMOTED",
    "source_map": SOURCE,
    "map": TARGET,
    "process_bay_light_count": len(bay_lights),
    "process_bay_light_intensity": 850.0,
    "external_rect_light_intensity": 680.0,
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
