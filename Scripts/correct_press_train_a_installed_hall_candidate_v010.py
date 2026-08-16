"""Create v010 with calibrated fixed exposure and installed-hall material context."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAExposureEnvironmentCandidate_v009"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAInstalledHallCandidate_v010"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_installed_hall_v010.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v010 from preserved v009: {TARGET}")

materials = {
    "wall": library.load_asset("/Game/LineBoss/Materials/FrontEnd/MI_LB_Wall_Concrete"),
    "floor": library.load_asset("/Game/LineBoss/Materials/FrontEnd/MI_LB_Floor_Neutral"),
    "ceiling": library.load_asset("/Game/LineBoss/Materials/FrontEnd/MI_LB_Wall_DarkService"),
}
if any(value is None for value in materials.values()):
    raise RuntimeError("installed-hall evidence materials missing")


def actor_by_label(label):
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one actor {label}, found {len(matches)}")
    return matches[0]


actor_by_label("CA_MW_PTA_InstalledEvidenceBackWall").static_mesh_component.set_material(0, materials["wall"])
actor_by_label("CA_MW_PTA_InstalledEvidenceCeiling").static_mesh_component.set_material(0, materials["ceiling"])
actor_by_label("CA_MW_PTA_IsolatedEvidenceFloor").static_mesh_component.set_material(0, materials["floor"])

camera_count = 0
bay_count = 0
fill_count = 0
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if isinstance(actor, unreal.CameraActor) and "LB.Camera.Fixed" in {str(tag) for tag in actor.tags}:
        settings = actor.camera_component.get_editor_property("post_process_settings")
        settings.set_editor_property("auto_exposure_bias", 0.45)
        actor.camera_component.set_editor_property("post_process_settings", settings)
        camera_count += 1
    elif label.startswith("CA_MW_PTA_ProcessBayLight_"):
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 30.0)
        bay_count += 1
    elif label.startswith("CA_MW_PTA_IsolatedFill_"):
        actor.get_editor_property("rect_light_component").set_editor_property("intensity", 600.0)
        fill_count += 1
    elif label == "CA_MW_PTA_IsolatedSky":
        actor.get_editor_property("light_component").set_editor_property("intensity", 0.35)
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags and "LB.Asset.Candidate.v010" not in tags:
        tags.append("LB.Asset.Candidate.v010")
        actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if camera_count != 3 or bay_count != 7 or fill_count != 7:
    failures.append(f"cardinality mismatch cameras={camera_count} bay={bay_count} fill={fill_count}")
if not levels.save_current_level():
    failures.append("could not save v010 installed-hall candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-installed-hall-v010/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V010_FIXED_EXPOSURE_CONCRETE_WALL_NEUTRAL_FLOOR_DARK_SERVICE_CEILING__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V010_INSTALLED_HALL__NOT_PROMOTED",
    "source_map": SOURCE,
    "map": TARGET,
    "fixed_camera_count": camera_count,
    "auto_exposure_bias": 0.45,
    "process_bay_light_intensity": 30.0,
    "external_rect_light_intensity": 600.0,
    "sky_intensity": 0.35,
    "validation_environment_only": True,
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
