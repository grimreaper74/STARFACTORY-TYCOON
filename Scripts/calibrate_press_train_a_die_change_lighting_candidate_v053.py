"""Create v053 by retaining v052's useful close cameras and removing clipped service lighting."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainADieChangeCameraEvidenceCandidate_v052"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_die_change_lighting_calibration_v053.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v053 from v052: {TARGET}")


def one(label):
    matches = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label}, found {len(matches)}")
    return matches[0]


def camera_exposure(camera, bias):
    settings = camera.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0,
        "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": bias,
    })
    camera.camera_component.set_editor_property("post_process_settings", settings)
    camera.camera_component.set_editor_property("post_process_blend_weight", 1.0)


# Preserve the v052 compositions: they reveal the cart bogies, clamps and dock
# relationship. Only rebalance exposure and task lights so worked steel retains
# shape and the Cairnwell cart plate remains legible.
camera_exposure(one("CA_MW_PTA_CAM_DieChangeService"), 0.56)
camera_exposure(one("CA_MW_PTA_CAM_DieCartDetail"), 0.52)

rect_count = 0
point_count = 0
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label.endswith("_DieChangeEvidenceLight"):
        component = actor.get_editor_property("rect_light_component")
        component.set_editor_property("intensity", 205.0)
        component.set_editor_property("source_width", 560.0)
        component.set_editor_property("source_height", 160.0)
        component.set_editor_property("attenuation_radius", 1050.0)
        rect_count += 1
    elif label.endswith("_DieChangeDockFill"):
        component = actor.get_editor_property("point_light_component")
        component.set_editor_property("intensity", 105.0)
        component.set_editor_property("attenuation_radius", 780.0)
        component.set_editor_property("source_radius", 75.0)
        point_count += 1

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v053" not in tags:
            tags.append("LB.Asset.Candidate.v053")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if rect_count != 5 or point_count != 5 or scope_count != 180:
    failures.append(f"calibration cardinality mismatch rect={rect_count} point={point_count} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v053 die-change lighting candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-die-change-lighting-calibration-v053/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V053_V052_COMPOSITIONS_RETAINED_WITH_RESTRAINED_DIE_CHANGE_LIGHTING__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V053_DIE_CHANGE_LIGHTING_CALIBRATION__NOT_PROMOTED"
    ),
    "source_map": SOURCE,
    "map": TARGET,
    "service_camera_exposure_bias": 0.56,
    "cart_camera_exposure_bias": 0.52,
    "service_rect_light_count": rect_count,
    "service_rect_intensity": 205.0,
    "dock_point_light_count": point_count,
    "dock_point_intensity": 105.0,
    "scope_actor_count": scope_count,
    "world_placement": "TBC_NOT_INVENTED",
    "validation_environment_only": True,
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
