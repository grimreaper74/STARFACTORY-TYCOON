"""Add the matching north-side coil task lights to retained-direction v140."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v140"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v141"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr003_pr004_coil_readability_build_v141.json"
BASE_PACKAGE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v140.umap"
library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


base_hash_before = sha256(BASE_PACKAGE)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not create {MAP}")
cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
lens = library.load_asset(
    "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_LuminaireLens_v105")
if cube is None or lens is None:
    raise RuntimeError("missing retained luminaire assets")
common_tags = [
    "LB.Asset.Candidate.v141", "LB.Asset.CandidateNotPromoted",
    "LB.Environment.CoilReadability.v141", "LB.VisualCorrection.NorthFaceFill",
]


def add_task_light(index, location, target):
    rotation = unreal.MathLibrary.find_look_at_rotation(unreal.Vector(*location), unreal.Vector(*target))
    fixture = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), rotation)
    fixture.set_actor_label(f"LB_ENV_V141_CoilNorthTaskLuminaire_{index:02d}")
    fixture.set_actor_scale3d(unreal.Vector(1.20, 0.35, 0.12))
    component = fixture.static_mesh_component
    component.set_static_mesh(cube)
    component.set_material(0, lens)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    component.set_editor_property("cast_shadow", False)
    fixture.tags = [unreal.Name(value) for value in common_tags + ["LB.Environment.Luminaire.CoilTask"]]
    light = actors_api.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*location), rotation)
    light.set_actor_label(f"LB_ENV_V141_CoilNorthTaskRect_{index:02d}")
    light_component = light.get_component_by_class(unreal.RectLightComponent)
    light_component.set_editor_properties({
        "intensity": 62.0, "source_width": 560.0, "source_height": 180.0,
        "attenuation_radius": 3000.0, "cast_shadows": False,
        "light_color": unreal.Color(220, 229, 232, 255),
    })
    light.tags = [unreal.Name(value) for value in common_tags + ["LB.Environment.Light.CoilTaskFill"]]
    return fixture, light


north_lights = [
    add_task_light(1, (-6750.0, -450.0, 1120.0), (-6750.0, -1950.0, 150.0)),
    add_task_light(2, (-6150.0, -450.0, 1120.0), (-6150.0, -1950.0, 150.0)),
]


def add_camera(label, location, target, fov):
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True,
    })
    camera.tags = [unreal.Name(value) for value in common_tags + [
        "LB.Camera.Validation", "LB.Camera.Fixed.CoilReadability.v141"]]
    return camera


cameras = [
    add_camera("LB_ENV_V141_CAM_CoilStoreNorth", (-7900.0, 50.0, 650.0), (-6450.0, -1900.0, 160.0), 52.0),
    add_camera("LB_ENV_V141_CAM_FrontEndFlow", (-10600.0, 900.0, 980.0), (-7200.0, -2100.0, 520.0), 59.0),
]
failures = []
if len(north_lights) != 2 or len(cameras) != 2:
    failures.append("unexpected north task-light or camera count")
if not levels.save_current_level():
    failures.append("could not save v141")
base_hash_after = sha256(BASE_PACKAGE)
if base_hash_after != base_hash_before:
    failures.append("preserved v140 package changed")
report = {
    "$schema": "cairnwell/audit/press-shop-pr003-pr004-coil-readability-build-v141/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__SYMMETRIC_NORTH_SOUTH_COIL_TASK_LIGHTING_BUILT__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V141_BUILD__NOT_PROMOTED",
    "source_map": BASE, "map": MAP,
    "inherited_south_task_light_count": 2, "new_north_task_light_count": len(north_lights),
    "coil_materials_changed": False, "coil_transforms_changed": False,
    "agv_or_crane_authority_changed": False,
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "protected_v140_sha256_before": base_hash_before,
    "protected_v140_sha256_after": base_hash_after,
    "promotion_authorized": False, "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
