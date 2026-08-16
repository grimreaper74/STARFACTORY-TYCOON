"""Create v034 with balanced facade fill and highlight-safe fixed cameras."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAEnclosedFacadeCandidate_v033"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAFacadeLightingCandidate_v034"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_facade_lighting_v034.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v034 from v033: {TARGET}")


def set_exposure(camera, bias):
    settings = camera.camera_component.get_editor_property("post_process_settings")
    settings.set_editor_properties({
        "override_auto_exposure_method": True,
        "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
        "override_auto_exposure_min_brightness": True,
        "override_auto_exposure_max_brightness": True,
        "auto_exposure_min_brightness": 1.0, "auto_exposure_max_brightness": 1.0,
        "override_auto_exposure_bias": True, "auto_exposure_bias": bias,
    })
    camera.camera_component.set_editor_property("post_process_settings", settings)
    camera.camera_component.set_editor_property("post_process_blend_weight", 1.0)


biases = {
    "CA_MW_PTA_CAM_Hero": 0.92, "CA_MW_PTA_CAM_Overview": 0.90,
    "CA_MW_PTA_CAM_DrawStage": 0.82, "CA_MW_PTA_CAM_DieChangeService": 0.82,
    "CA_MW_PTA_CAM_DieCartDetail": 0.74,
}
for actor in actors_api.get_all_level_actors():
    if actor.get_actor_label() in biases:
        set_exposure(actor, biases[actor.get_actor_label()])

facade_lights = []
for index, y_cm in enumerate((0.0, 1125.0, 2250.0, 3375.0, 4500.0), start=1):
    location = unreal.Vector(-1250.0, y_cm, 650.0)
    target = unreal.Vector(-250.0, y_cm, 420.0)
    light = actors_api.spawn_actor_from_class(
        unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, target))
    light.set_actor_label(f"CA_MW_PTA_FacadeFill_{index:02d}")
    light.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.TrainA.Isolated", "LB.Validation.Environment",
        "LB.Validation.FacadeLighting", f"LB.Validation.FacadeLighting.{index:02d}",
        "LB.Asset.Candidate.v034", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    component = light.get_editor_property("rect_light_component")
    component.set_editor_property("intensity", 240.0)
    component.set_editor_property("source_width", 900.0)
    component.set_editor_property("source_height", 230.0)
    component.set_editor_property("attenuation_radius", 1700.0)
    component.set_light_color(unreal.LinearColor(0.48, 0.54, 0.52, 1.0))
    facade_lights.append(light.get_actor_label())

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v034" not in tags:
            tags.append("LB.Asset.Candidate.v034")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if len(facade_lights) != 5 or scope_count != 169:
    failures.append(f"cardinality mismatch facade_lights={len(facade_lights)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v034 facade-lighting candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-facade-lighting-v034/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V034_FIVE_BROAD_CAMERA_SIDE_FILLS_AND_HIGHLIGHT_SAFE_EXPOSURE__EXACT_STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V034_FACADE_LIGHTING__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET, "camera_exposure_bias": biases,
    "facade_lights": facade_lights, "facade_light_intensity": 240.0,
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
