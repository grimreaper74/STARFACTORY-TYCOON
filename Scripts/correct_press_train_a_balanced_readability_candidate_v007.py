"""Create v007 with balanced internal lighting and restored hero composition."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAInternalReadabilityCandidate_v006"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainABalancedReadabilityCandidate_v007"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_balanced_readability_v007.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary

if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v007 from preserved v006: {TARGET}")


def camera(label, location, target, fov):
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one camera {label}, found {len(matches)}")
    actor = matches[0]
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    actor.camera_component.set_editor_property("field_of_view", fov)


bay_count = 0
fill_count = 0
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("CA_MW_PTA_ProcessBayLight_"):
        component = actor.get_editor_property("point_light_component")
        component.set_editor_property("intensity", 72.0)
        component.set_editor_property("attenuation_radius", 480.0)
        bay_count += 1
    elif label.startswith("CA_MW_PTA_IsolatedFill_"):
        actor.get_editor_property("rect_light_component").set_editor_property("intensity", 600.0)
        fill_count += 1
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags and "LB.Asset.Candidate.v007" not in tags:
        tags.append("LB.Asset.Candidate.v007")
        actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

camera(
    "CA_MW_PTA_CAM_Hero",
    unreal.Vector(-2850.0, -2050.0, 1480.0),
    unreal.Vector(0.0, 2200.0, 420.0),
    55.0,
)
camera(
    "CA_MW_PTA_CAM_DrawStage",
    unreal.Vector(-2400.0, 420.0, 1050.0),
    unreal.Vector(0.0, 850.0, 350.0),
    52.0,
)

failures = []
if bay_count != 7:
    failures.append(f"expected seven process-bay lights, found {bay_count}")
if fill_count != 7:
    failures.append(f"expected seven external fill lights, found {fill_count}")
if not levels.save_current_level():
    failures.append("could not save v007 balanced-readability candidate")

report = {
    "$schema": "cairnwell/audit/press-train-a-balanced-readability-v007/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V007_BALANCED_PROCESS_BAY_LIGHTING_AND_FIXED_CAMERAS__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V007_BALANCED_READABILITY__NOT_PROMOTED",
    "source_map": SOURCE,
    "map": TARGET,
    "process_bay_light_count": bay_count,
    "process_bay_light_intensity": 72.0,
    "external_fill_count": fill_count,
    "external_rect_light_intensity": 600.0,
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
