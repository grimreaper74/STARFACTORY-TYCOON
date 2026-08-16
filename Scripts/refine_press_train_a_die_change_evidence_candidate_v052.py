"""Create v052 with closer three-quarter die-change cameras and restrained service lighting."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainACrownEndpointRefinementCandidate_v051"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainADieChangeCameraEvidenceCandidate_v052"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_die_change_camera_evidence_v052.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v052 from v051: {TARGET}")


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


service = one("CA_MW_PTA_CAM_DieChangeService")
service_location = unreal.Vector(1450.0, 1150.0, 420.0)
service_target = unreal.Vector(450.0, 2250.0, 130.0)
service.set_actor_location(service_location, False, False)
service.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(service_location, service_target), False)
service.camera_component.set_editor_property("field_of_view", 68.0)
camera_exposure(service, 0.86)

cart = one("CA_MW_PTA_CAM_DieCartDetail")
cart_location = unreal.Vector(1300.0, 1850.0, 260.0)
cart_target = unreal.Vector(500.0, 2250.0, 95.0)
cart.set_actor_location(cart_location, False, False)
cart.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(cart_location, cart_target), False)
cart.camera_component.set_editor_property("field_of_view", 58.0)
camera_exposure(cart, 0.80)

rect_count = 0
point_count = 0
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label.endswith("_DieChangeEvidenceLight"):
        y_cm = actor.get_actor_location().y
        location = unreal.Vector(1080.0, y_cm, 560.0)
        target = unreal.Vector(420.0, y_cm, 155.0)
        actor.set_actor_location(location, False, False)
        actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
        component = actor.get_editor_property("rect_light_component")
        component.set_editor_property("intensity", 380.0)
        component.set_editor_property("source_width", 560.0)
        component.set_editor_property("source_height", 160.0)
        component.set_editor_property("attenuation_radius", 1120.0)
        rect_count += 1
    elif label.endswith("_DieChangeDockFill"):
        component = actor.get_editor_property("point_light_component")
        component.set_editor_property("intensity", 220.0)
        component.set_editor_property("attenuation_radius", 850.0)
        component.set_editor_property("source_radius", 75.0)
        point_count += 1

scope_count = 0
for actor in actors_api.get_all_level_actors():
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags:
        scope_count += 1
        if "LB.Asset.Candidate.v052" not in tags:
            tags.append("LB.Asset.Candidate.v052")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if rect_count != 5 or point_count != 5 or scope_count != 180:
    failures.append(f"evidence cardinality mismatch rect={rect_count} point={point_count} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v052 die-change camera evidence candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-die-change-camera-evidence-v052/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V052_THREE_QUARTER_DIE_CHANGE_CAMERAS_AND_RESTRAINED_DOCK_LIGHTING__STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V052_DIE_CHANGE_CAMERA_EVIDENCE__NOT_PROMOTED"
    ),
    "source_map": SOURCE,
    "map": TARGET,
    "service_camera_location_cm": [1450.0, 1150.0, 420.0],
    "service_camera_target_cm": [450.0, 2250.0, 130.0],
    "service_camera_fov_deg": 68.0,
    "service_camera_exposure_bias": 0.86,
    "cart_camera_location_cm": [1300.0, 1850.0, 260.0],
    "cart_camera_target_cm": [500.0, 2250.0, 95.0],
    "cart_camera_fov_deg": 58.0,
    "cart_camera_exposure_bias": 0.80,
    "service_rect_light_count": rect_count,
    "service_rect_intensity": 380.0,
    "dock_point_light_count": point_count,
    "dock_point_intensity": 220.0,
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
