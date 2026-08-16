"""Create v009 with deterministic camera exposure and neutral installed backdrop."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAMechanicalBayCandidate_v008"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAExposureEnvironmentCandidate_v009"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_exposure_environment_v009.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
library = unreal.EditorAssetLibrary
if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v009 from preserved v008: {TARGET}")

# Establish deterministic evidence exposure on all three fixed cameras.  This
# prevents the black isolated void from driving auto exposure and bleaching the
# layered charcoal/green materials.
camera_count = 0
for actor in actors_api.get_all_level_actors():
    if isinstance(actor, unreal.CameraActor) and "LB.Camera.Fixed" in {str(tag) for tag in actor.tags}:
        settings = actor.camera_component.get_editor_property("post_process_settings")
        settings.set_editor_properties({
            "override_auto_exposure_method": True,
            "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
            "override_auto_exposure_min_brightness": True,
            "override_auto_exposure_max_brightness": True,
            "auto_exposure_min_brightness": 1.0,
            "auto_exposure_max_brightness": 1.0,
            "override_auto_exposure_bias": True,
            "auto_exposure_bias": -0.35,
        })
        actor.camera_component.set_editor_property("post_process_settings", settings)
        actor.camera_component.set_editor_property("post_process_blend_weight", 1.0)
        camera_count += 1

# Neutral evidence wall and ceiling provide a finite installed-space read and
# diffuse bounce reference; they are validation-only and have no production datum.
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
backdrop_material_path = "/Game/LineBoss/Stations/Press/PR009/Presentation_v085/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v085"
backdrop_material = library.load_asset(backdrop_material_path)
if not isinstance(cube, unreal.StaticMesh) or backdrop_material is None:
    raise RuntimeError("neutral evidence environment assets missing")


def evidence_mesh(label, location, scale):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator())
    actor.set_actor_label(label)
    actor.tags = [
        unreal.Name("LB.Validation.Environment"),
        unreal.Name("LB.Validation.Environment.InstalledNeutral"),
        unreal.Name("LB.Asset.Candidate.v009"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    actor.static_mesh_component.set_static_mesh(cube)
    actor.set_actor_scale3d(scale)
    actor.static_mesh_component.set_material(0, backdrop_material)
    actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
    return actor


evidence_mesh("CA_MW_PTA_InstalledEvidenceBackWall", unreal.Vector(900.0, 2250.0, 620.0), unreal.Vector(0.6, 65.0, 12.5))
evidence_mesh("CA_MW_PTA_InstalledEvidenceCeiling", unreal.Vector(0.0, 2250.0, 1260.0), unreal.Vector(18.0, 65.0, 0.35))

bay_lights = 0
fill_lights = 0
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("CA_MW_PTA_ProcessBayLight_"):
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 38.0)
        bay_lights += 1
    elif label.startswith("CA_MW_PTA_IsolatedFill_"):
        actor.get_editor_property("rect_light_component").set_editor_property("intensity", 760.0)
        fill_lights += 1
    elif label == "CA_MW_PTA_IsolatedSky":
        actor.get_editor_property("light_component").set_editor_property("intensity", 0.42)
    tags = [str(tag) for tag in actor.tags]
    if "LB.PressTrain.TrainA.Isolated" in tags and "LB.Asset.Candidate.v009" not in tags:
        tags.append("LB.Asset.Candidate.v009")
        actor.set_editor_property("tags", [unreal.Name(tag) for tag in tags])

failures = []
if camera_count != 3:
    failures.append(f"expected three fixed cameras, found {camera_count}")
if bay_lights != 7 or fill_lights != 7:
    failures.append(f"light cardinality mismatch bay={bay_lights} fill={fill_lights}")
if not levels.save_current_level():
    failures.append("could not save v009 exposure/environment candidate")
report = {
    "$schema": "cairnwell/audit/press-train-a-exposure-environment-v009/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__PRESS_TRAIN_A_V009_FIXED_EXPOSURE_NEUTRAL_INSTALLED_EVIDENCE_ENVIRONMENT__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__PRESS_TRAIN_A_V009_EXPOSURE_ENVIRONMENT__NOT_PROMOTED",
    "source_map": SOURCE,
    "map": TARGET,
    "fixed_camera_count": camera_count,
    "auto_exposure_bias": -0.35,
    "process_bay_light_intensity": 38.0,
    "external_rect_light_intensity": 760.0,
    "sky_intensity": 0.42,
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
