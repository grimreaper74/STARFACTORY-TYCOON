"""Create v028 with balanced release evidence and a close die-cart camera."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAExteriorEnvelopeCandidate_v027"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAReleaseEvidenceCandidate_v028"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_release_evidence_v028.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v028 from v027: {TARGET}")


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


cameras = {}
for actor in actors_api.get_all_level_actors():
    if isinstance(actor, unreal.CameraActor) and "LB.Camera.Fixed" in {str(tag) for tag in actor.tags}:
        cameras[actor.get_actor_label()] = actor
for label, bias in {
    "CA_MW_PTA_CAM_Hero": 0.80,
    "CA_MW_PTA_CAM_Overview": 0.78,
    "CA_MW_PTA_CAM_DrawStage": 0.64,
    "CA_MW_PTA_CAM_DieChangeService": 0.64,
}.items():
    camera_exposure(cameras[label], bias)

service = cameras["CA_MW_PTA_CAM_DieChangeService"]
service_location = unreal.Vector(1600.0, -250.0, 470.0)
service_target = unreal.Vector(500.0, 2350.0, 150.0)
service.set_actor_location(service_location, False, False)
service.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(service_location, service_target), False)
service.camera_component.set_editor_property("field_of_view", 82.0)

cart_camera_location = unreal.Vector(1250.0, 1050.0, 320.0)
cart_camera_target = unreal.Vector(500.0, 1500.0, 95.0)
cart_camera = actors_api.spawn_actor_from_class(
    unreal.CameraActor, cart_camera_location,
    unreal.MathLibrary.find_look_at_rotation(cart_camera_location, cart_camera_target))
cart_camera.set_actor_label("CA_MW_PTA_CAM_DieCartDetail")
cart_camera.tags = [unreal.Name(value) for value in (
    "LB.PressTrain.TrainA.Isolated", "LB.Camera.Fixed", "LB.Camera.Fixed.DieCartDetail",
    "LB.Validation.Environment", "LB.Asset.Candidate.v028", "LB.Asset.CandidateNotPromoted",
    "LB.Authority.WorldPlacement.TBCNotInvented",
)]
cart_camera.camera_component.set_editor_property("field_of_view", 62.0)
camera_exposure(cart_camera, 0.62)

# Existing service lights are aimed higher so they reveal the dock connectors and
# press-side structure, not only the tooling deck.
service_rect_count = 0
for actor in actors_api.get_all_level_actors():
    if actor.get_actor_label().endswith("_DieChangeEvidenceLight"):
        stage_y = actor.get_actor_location().y
        location = unreal.Vector(1180.0, stage_y, 690.0)
        target = unreal.Vector(250.0, stage_y, 410.0)
        actor.set_actor_location(location, False, False)
        actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
        component = actor.get_editor_property("rect_light_component")
        component.set_editor_property("intensity", 235.0)
        component.set_editor_property("source_width", 520.0)
        component.set_editor_property("source_height", 125.0)
        component.set_editor_property("attenuation_radius", 980.0)
        service_rect_count += 1

overhead_lights = []
for index, y_cm in enumerate((500.0, 1750.0, 3000.0, 4250.0), start=1):
    location = unreal.Vector(0.0, y_cm, 1080.0)
    target = unreal.Vector(0.0, y_cm, 500.0)
    light = actors_api.spawn_actor_from_class(
        unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, target))
    light.set_actor_label(f"CA_MW_PTA_ReleaseOverheadWash_{index:02d}")
    light.tags = [unreal.Name(value) for value in (
        "LB.PressTrain.TrainA.Isolated", "LB.Validation.Environment",
        "LB.Validation.ReleaseOverheadLighting", f"LB.Validation.ReleaseOverheadLighting.{index:02d}",
        "LB.Asset.Candidate.v028", "LB.Asset.CandidateNotPromoted",
        "LB.Authority.WorldPlacement.TBCNotInvented",
    )]
    component = light.get_editor_property("rect_light_component")
    component.set_editor_property("intensity", 190.0)
    component.set_editor_property("source_width", 950.0)
    component.set_editor_property("source_height", 210.0)
    component.set_editor_property("attenuation_radius", 1450.0)
    component.set_light_color(unreal.LinearColor(0.56, 0.63, 0.60, 1.0))
    overhead_lights.append(light.get_actor_label())

scope_count = 0
for actor in actors_api.get_all_level_actors():
    actor_tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        scope_count += 1
        if "LB.Asset.Candidate.v028" not in actor_tags:
            actor_tags.append("LB.Asset.Candidate.v028")
            actor.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])

failures = []
if len(cameras) != 4 or service_rect_count != 5 or len(overhead_lights) != 4 or scope_count != 152:
    failures.append(
        f"evidence cardinality mismatch inherited_cameras={len(cameras)} service_rect={service_rect_count} overhead={len(overhead_lights)} scope={scope_count}")
if not levels.save_current_level():
    failures.append("could not save v028 release-evidence candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-release-evidence-v028/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__PRESS_TRAIN_A_V028_FIVE_FIXED_CAMERAS_BALANCED_SERVICE_AND_RESTRAINED_OVERHEAD_EVIDENCE__EXACT_STATIC_AND_FRESH_PRO_VISUAL_GATES_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__PRESS_TRAIN_A_V028_RELEASE_EVIDENCE__NOT_PROMOTED"),
    "source_map": SOURCE, "map": TARGET,
    "camera_exposure_bias": {"hero": 0.80, "overview": 0.78, "draw": 0.64, "service": 0.64, "cart": 0.62},
    "service_camera_location_cm": [1600.0, -250.0, 470.0],
    "service_camera_target_cm": [500.0, 2350.0, 150.0], "service_camera_fov_deg": 82.0,
    "cart_camera_location_cm": [1250.0, 1050.0, 320.0],
    "cart_camera_target_cm": [500.0, 1500.0, 95.0], "cart_camera_fov_deg": 62.0,
    "service_rect_light_count": service_rect_count, "service_rect_intensity": 235.0,
    "overhead_light_count": len(overhead_lights), "overhead_intensity": 190.0,
    "scope_actor_count": scope_count, "world_placement": "TBC_NOT_INVENTED",
    "production_map_changed": False, "accepted_pr010_map_changed": False,
    "failures": failures, "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
