"""Create v015 with installed-hall readability and a usable hero camera."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainACCTVMaterialCandidate_v014"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAInstalledReadabilityCandidate_v015"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_installed_readability_v015.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v015 from preserved v014: {TARGET}")

bay_count = 0
fill_count = 0
bounce_count = 0
sky_count = 0
scope_count = 0
hero_count = 0
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("CA_MW_PTA_ProcessBayLight_"):
        component = actor.get_editor_property("point_light_component")
        component.set_editor_property("intensity", 72.0)
        component.set_editor_property("attenuation_radius", 520.0)
        component.set_editor_property("source_radius", 55.0)
        bay_count += 1
    elif label.startswith("CA_MW_PTA_IsolatedFill_"):
        actor.get_editor_property("rect_light_component").set_editor_property("intensity", 650.0)
        fill_count += 1
    elif label.startswith("CA_MW_PTA_InstalledHallBounce_"):
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 105.0)
        bounce_count += 1
    elif label == "CA_MW_PTA_IsolatedSky":
        actor.get_editor_property("light_component").set_editor_property("intensity", 0.50)
        sky_count += 1
    elif label == "CA_MW_PTA_CAM_Hero":
        location = unreal.Vector(-2850.0, -2050.0, 850.0)
        target = unreal.Vector(0.0, 2200.0, 350.0)
        actor.set_actor_location(location, False, False)
        actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
        actor.camera_component.set_editor_property("field_of_view", 55.0)
        hero_count += 1
    actor_tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        scope_count += 1
        if "LB.Asset.Candidate.v015" not in actor_tags:
            actor_tags.append("LB.Asset.Candidate.v015")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])

failures = []
if (bay_count, fill_count, bounce_count, sky_count, hero_count) != (7, 7, 4, 1, 1):
    failures.append(
        f"cardinality mismatch bay={bay_count} fill={fill_count} bounce={bounce_count} sky={sky_count} hero={hero_count}")
if not levels.save_current_level():
    failures.append("could not save v015 installed-readability candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-installed-readability-v015/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V015_RESTRAINED_MATERIALS_BALANCED_BAY_FILL_AND_LOWER_HERO_CAMERA__STATIC_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V015_INSTALLED_READABILITY__NOT_PROMOTED",
    "source_map": SOURCE, "map": TARGET, "scope_actor_count": scope_count,
    "process_bay_light_count": bay_count, "process_bay_light_intensity": 72.0,
    "external_fill_count": fill_count, "external_fill_intensity": 650.0,
    "hall_bounce_count": bounce_count, "hall_bounce_intensity": 105.0,
    "sky_intensity": 0.50, "hero_camera_location_cm": [-2850.0, -2050.0, 850.0],
    "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
    "accepted_pr010_map_changed": False, "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
