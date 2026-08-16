"""Build an isolated visual successor of exact Train A assembly v005.

Only validation lighting, exposure and fixed-camera composition are changed.
The 163-object assembly, transforms, materials, collision authoring and local
TBC placement remain inherited from v005.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v005"
TARGET = "/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyVisualCandidate_v006"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_assembly_visual_build_v006.json"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if library.does_asset_exist(TARGET):
    raise RuntimeError(f"Refusing to overwrite preserved candidate: {TARGET}")
if not levels.new_level_from_template(TARGET, SOURCE):
    raise RuntimeError(f"Could not create v006 from v005: {TARGET}")


def all_actors():
    return list(actors_api.get_all_level_actors())


def one(label):
    matches = [actor for actor in all_actors() if actor.get_actor_label() == label]
    if len(matches) != 1:
        raise RuntimeError(f"expected one {label}, found {len(matches)}")
    return matches[0]


def add_tags(actor, *values):
    tags = [str(value) for value in actor.tags]
    for value in values:
        if value not in tags:
            tags.append(value)
    actor.set_editor_property("tags", [unreal.Name(value) for value in tags])


def camera_exposure(camera, bias=1.65):
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


def set_camera(old_label, new_label, location, target, fov, roll=0.0):
    actor = one(old_label)
    rotation = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*location), unreal.Vector(*target))
    rotation.roll = roll
    actor.set_actor_location(unreal.Vector(*location), False, False)
    actor.set_actor_rotation(rotation, False)
    actor.set_actor_label(new_label)
    actor.camera_component.set_editor_property("field_of_view", fov)
    camera_exposure(actor)
    add_tags(actor, "LB.Asset.Candidate.v006", "LB.PressTrain.VisualSuccessor.v006")
    return actor


# Raise the existing non-production study lighting into a restrained, readable
# neutral evidence rig. No light is presented as installed production hardware.
sky = one("CA_MW_PTA_IsolationSky_v005")
sky.set_actor_label("CA_MW_PTA_IsolationSky_v006")
sky.get_editor_property("light_component").set_editor_property("intensity", 1.4)
add_tags(sky, "LB.Asset.Candidate.v006", "LB.Validation.Lighting.v006")

key = one("CA_MW_PTA_IsolationKey_v005")
key.set_actor_label("CA_MW_PTA_IsolationKey_v006")
key.set_actor_rotation(unreal.Rotator(pitch=-52.0, yaw=-38.0), False)
key.get_editor_property("directional_light_component").set_editor_property("intensity", 7.0)
add_tags(key, "LB.Asset.Candidate.v006", "LB.Validation.Lighting.v006")

existing_fill_count = 0
for index, y in enumerate((-250.0, 750.0, 1750.0, 2750.0, 3750.0, 4750.0), 1):
    light = one(f"CA_MW_PTA_IsolationFill_{index:02d}_v005")
    light.set_actor_label(f"CA_MW_PTA_IsolationFill_East_{index:02d}_v006")
    light.set_actor_location(unreal.Vector(1700.0, y, 1750.0), False, False)
    light.set_actor_rotation(unreal.Rotator(pitch=-38.0, yaw=180.0), False)
    comp = light.get_editor_property("rect_light_component")
    comp.set_editor_properties({
        "intensity": 7600.0,
        "source_width": 850.0,
        "source_height": 260.0,
        "attenuation_radius": 4200.0,
    })
    comp.set_light_color(unreal.LinearColor(0.92, 0.96, 1.0, 1.0))
    add_tags(light, "LB.Asset.Candidate.v006", "LB.Validation.Lighting.v006")
    existing_fill_count += 1

west_fill_count = 0
for index, y in enumerate((-250.0, 750.0, 1750.0, 2750.0, 3750.0, 4750.0), 1):
    light = actors_api.spawn_actor_from_class(
        unreal.RectLight, unreal.Vector(-1700.0, y, 1550.0), unreal.Rotator(pitch=-32.0, yaw=0.0)
    )
    light.set_actor_label(f"CA_MW_PTA_IsolationFill_West_{index:02d}_v006")
    comp = light.get_editor_property("rect_light_component")
    comp.set_editor_properties({
        "intensity": 5200.0,
        "source_width": 850.0,
        "source_height": 260.0,
        "attenuation_radius": 4200.0,
    })
    comp.set_light_color(unreal.LinearColor(1.0, 0.92, 0.82, 1.0))
    add_tags(
        light,
        "LB.PressTrain.TrainA.AssemblyIntegration.v005",
        "LB.Asset.Candidate.v006",
        "LB.Authority.WorldPlacement.TBCNotInvented",
        "LB.Validation.Lighting",
        "LB.Validation.Lighting.v006",
        "LB.PressTrain.VisualSuccessor.v006",
    )
    west_fill_count += 1

post = one("CA_MW_PTA_IsolationExposure_v005")
post.set_actor_label("CA_MW_PTA_IsolationExposure_v006")
pps = post.get_editor_property("settings")
pps.set_editor_properties({
    "override_auto_exposure_method": True,
    "auto_exposure_method": unreal.AutoExposureMethod.AEM_BASIC,
    "override_auto_exposure_min_brightness": True,
    "override_auto_exposure_max_brightness": True,
    "auto_exposure_min_brightness": 1.0,
    "auto_exposure_max_brightness": 1.0,
    "override_auto_exposure_bias": True,
    "auto_exposure_bias": 1.25,
})
post.set_editor_property("settings", pps)
add_tags(post, "LB.Asset.Candidate.v006", "LB.Validation.Lighting.v006")

cameras = [
    set_camera("CA_MW_PTA_CAM_Hero_v005", "CA_MW_PTA_CAM_Hero_v006", (-3800.0, -2500.0, 2200.0), (0.0, 2250.0, 450.0), 42.0),
    set_camera("CA_MW_PTA_CAM_OperatorSide_v005", "CA_MW_PTA_CAM_OperatorSide_v006", (3900.0, 2250.0, 1450.0), (0.0, 2250.0, 480.0), 42.0),
    set_camera("CA_MW_PTA_CAM_Overhead_v005", "CA_MW_PTA_CAM_Overhead_v006", (0.0, 2250.0, 7200.0), (0.0, 2250.0, 0.0), 44.0, 90.0),
    set_camera("CA_MW_PTA_CAM_S01_v005", "CA_MW_PTA_CAM_S01_v006", (3200.0, -1750.0, 1450.0), (0.0, -100.0, 420.0), 46.0),
    set_camera("CA_MW_PTA_CAM_S07_v005", "CA_MW_PTA_CAM_S07_v006", (3200.0, 6250.0, 1450.0), (0.0, 4650.0, 420.0), 46.0),
    set_camera("CA_MW_PTA_CAM_LoadedCart_v005", "CA_MW_PTA_CAM_LoadedCart_v006", (-2850.0, 1700.0, 1150.0), (-400.0, 2200.0, 260.0), 44.0),
    set_camera("CA_MW_PTA_CAM_Mechanics_v005", "CA_MW_PTA_CAM_Mechanics_v006", (3300.0, 2550.0, 1650.0), (250.0, 2550.0, 430.0), 40.0),
]

scope = []
for actor in all_actors():
    tags = {str(value) for value in actor.tags}
    if "LB.PressTrain.TrainA.AssemblyIntegration.v005" in tags:
        add_tags(actor, "LB.PressTrain.VisualSuccessor.v006")
        scope.append(actor)

failures = []
if existing_fill_count != 6 or west_fill_count != 6:
    failures.append(f"fill cardinality mismatch east={existing_fill_count} west={west_fill_count}")
if len(cameras) != 7:
    failures.append(f"camera cardinality mismatch {len(cameras)}")
if len(scope) < 180:
    failures.append(f"unexpected inherited scope count {len(scope)}")
if not levels.save_current_level():
    failures.append("could not save v006 map")

report = {
    "$schema": "cairnwell/audit/press-train-a-assembly-visual-build-v006/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__DIRECT_V005_VISUAL_SUCCESSOR__EXACT_STATIC_AND_FRESH_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__TRAIN_A_ASSEMBLY_VISUAL_V006__NOT_PROMOTED",
    "source_map": SOURCE,
    "map": TARGET,
    "inherited_assembly_actor_count": len(scope),
    "machine_geometry_modified": False,
    "machine_materials_modified": False,
    "machine_transforms_modified": False,
    "collision_authority_modified": False,
    "world_placement": "TBC_NOT_INVENTED",
    "validation_environment_only": True,
    "camera_count": len(cameras),
    "east_fill_count": existing_fill_count,
    "west_fill_count": west_fill_count,
    "production_map_changed": False,
    "failures": failures,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))

