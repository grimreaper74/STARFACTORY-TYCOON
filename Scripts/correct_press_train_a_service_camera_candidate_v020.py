"""Create v020 with a fixed die-change-side camera and separated S04/S05 detail."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAServiceReadabilityCandidate_v019"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAServiceCameraCandidate_v020"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_service_camera_v020.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v020 from v019: {TARGET}")


def actor(label):
    matches = [value for value in actors_api.get_all_level_actors() if value.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one {label}, found {len(matches)}")
    return matches[0]


# Keep each variant within its 7.5 m pitch while preventing the repeated bank
# from sitting directly over the S04/S05 process-specific presentation.
offsets = {
    "CA_MW_PTA_S04_InstalledServiceBank": 2130.0,
    "CA_MW_PTA_S04_LocalTaskFixture": 2130.0,
    "CA_MW_PTA_S04_InstalledTaskLight": 2130.0,
    "CA_MW_PTA_S04_TrimScrapService": 2370.0,
    "CA_MW_PTA_S05_InstalledServiceBank": 2880.0,
    "CA_MW_PTA_S05_LocalTaskFixture": 2880.0,
    "CA_MW_PTA_S05_InstalledTaskLight": 2880.0,
    "CA_MW_PTA_S05_PierceSlugService": 3120.0,
}
for label, y_cm in offsets.items():
    value = actor(label)
    location = value.get_actor_location()
    value.set_actor_location(unreal.Vector(location.x, y_cm, location.z), False, False)

location = unreal.Vector(700.0, 2250.0, 760.0)
target = unreal.Vector(0.0, 2250.0, 260.0)
camera = actors_api.spawn_actor_from_class(
    unreal.CameraActor, location, unreal.MathLibrary.find_look_at_rotation(location, target))
camera.set_actor_label("CA_MW_PTA_CAM_DieChangeService")
camera.tags = [unreal.Name(value) for value in (
    "LB.PressTrain.TrainA.Isolated", "LB.Camera.Fixed", "LB.Camera.Fixed.DieChangeService",
    "LB.Asset.Candidate.v020", "LB.Asset.CandidateNotPromoted",
    "LB.Authority.WorldPlacement.TBCNotInvented",
)]
camera.camera_component.set_editor_property("field_of_view", 68.0)
settings = camera.camera_component.get_editor_property("post_process_settings")
settings.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 0.45,
})
camera.camera_component.set_editor_property("post_process_settings", settings)
camera.camera_component.set_editor_property("post_process_blend_weight", 1.0)

scope_count = 0
for value in actors_api.get_all_level_actors():
    actor_tags = [str(tag) for tag in value.tags]
    if "LB.PressTrain.TrainA.Isolated" in actor_tags:
        scope_count += 1
        if "LB.Asset.Candidate.v020" not in actor_tags:
            actor_tags.append("LB.Asset.Candidate.v020")
            value.set_editor_property("tags", [unreal.Name(tag) for tag in actor_tags])

failures = []
if scope_count != 101:
    failures.append(f"expected 101 scoped actors after service camera, found {scope_count}")
if not levels.save_current_level():
    failures.append("could not save v020 service-camera candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-service-camera-v020/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V020_DIE_CHANGE_SERVICE_CAMERA_AND_SEPARATED_S04_S05_DETAIL__EARLY_SERVICE_CAMERA_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V020_SERVICE_CAMERA__NOT_PROMOTED",
    "source_map": SOURCE, "map": TARGET, "service_camera_location_cm": [700.0, 2250.0, 760.0],
    "service_camera_target_cm": [0.0, 2250.0, 260.0], "service_camera_fov_deg": 68.0,
    "stage_variant_actor_y_cm": offsets, "scope_actor_count": scope_count,
    "world_placement": "TBC_NOT_INVENTED", "production_map_changed": False,
    "accepted_pr010_map_changed": False, "failures": failures,
    "promotion_authorized": False, "press_shop_complete": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
