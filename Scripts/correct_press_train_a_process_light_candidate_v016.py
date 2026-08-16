"""Create v016 by moving illumination from roof glare into process bays."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAInstalledReadabilityCandidate_v015"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAProcessLightCandidate_v016"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_process_light_v016.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v016 from preserved v015: {TARGET}")

counts = {"bay": 0, "fill": 0, "bounce": 0, "sky": 0, "key": 0, "scope": 0}
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("CA_MW_PTA_ProcessBayLight_"):
        component = actor.get_editor_property("point_light_component")
        component.set_editor_property("intensity", 180.0)
        component.set_editor_property("attenuation_radius", 560.0)
        component.set_editor_property("source_radius", 75.0)
        counts["bay"] += 1
    elif label.startswith("CA_MW_PTA_IsolatedFill_"):
        actor.get_editor_property("rect_light_component").set_editor_property("intensity", 900.0)
        counts["fill"] += 1
    elif label.startswith("CA_MW_PTA_InstalledHallBounce_"):
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 80.0)
        counts["bounce"] += 1
    elif label == "CA_MW_PTA_IsolatedSky":
        actor.get_editor_property("light_component").set_editor_property("intensity", 0.65)
        counts["sky"] += 1
    elif label == "CA_MW_PTA_IsolatedKey":
        actor.get_editor_property("directional_light_component").set_editor_property("intensity", 1.20)
        counts["key"] += 1
    actor_tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        counts["scope"] += 1
        if "LB.Asset.Candidate.v016" not in actor_tags:
            actor_tags.append("LB.Asset.Candidate.v016")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])

failures = []
if tuple(counts[name] for name in ("bay", "fill", "bounce", "sky", "key")) != (7, 7, 4, 1, 1):
    failures.append(f"lighting cardinality mismatch: {counts}")
if not levels.save_current_level():
    failures.append("could not save v016 process-light candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-process-light-v016/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V016_REDUCED_ROOF_KEY_AND_INCREASED_LOCAL_PROCESS_LIGHT__EARLY_DRAW_CAMERA_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V016_PROCESS_LIGHT__NOT_PROMOTED",
    "source_map": SOURCE, "map": TARGET, "counts": counts,
    "intensities": {"process_bay": 180.0, "external_fill": 900.0, "hall_bounce": 80.0, "sky": 0.65, "directional_key": 1.20},
    "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
    "accepted_pr010_map_changed": False, "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
