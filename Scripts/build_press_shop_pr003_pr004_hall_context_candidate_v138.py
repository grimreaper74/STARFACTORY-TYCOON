"""Build isolated v138 by applying the retained v107 hall policy to v136.

The v117 sealed-concrete floor, v135 AGV authority and v136 powered C-hook are
preserved.  Only the independently retained v104/v107 shared-hall correction
is transferred: warning-safe light calibration, saw-cut joints, a logistics
spine, continuous luminaires and fixed operational cameras.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v136"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR003PR004HallContextCandidate_v138"
DEST = "/Game/LineBoss/Candidates/PressShop/PR003PR004HallContext_v138"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr003_pr004_hall_context_build_v138.json"
BASE_PACKAGE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v136.umap"

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
    raise RuntimeError(f"could not create isolated v138 from {BASE}")

cube = library.load_asset("/Engine/BasicShapes/Cube.Cube")
materials = {
    "joint": library.load_asset(
        "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_SlabJoint_v105"),
    "route": library.load_asset(
        "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_LogisticsRoute_v105"),
    "yellow": library.load_asset(
        "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_RouteYellow_v105"),
    "lens": library.load_asset(
        "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v107/Materials/M_CA_MW_LuminaireLens_v105"),
}
if cube is None or any(value is None for value in materials.values()):
    raise RuntimeError("missing retained v107 environment source asset")


def tags(actor):
    return [str(value) for value in actor.tags]


def merge_tags(actor, values):
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(tags(actor) + values)]


common_tags = [
    "LB.Asset.Candidate.v138", "LB.Asset.CandidateNotPromoted",
    "LB.Environment.SharedHall.v138", "LB.Environment.Policy.Source.v107",
]


def add_mesh(label, location, scale, material, role):
    actor = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    component = actor.static_mesh_component
    component.set_static_mesh(cube)
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    component.set_editor_property("cast_shadow", False)
    actor.tags = [unreal.Name(value) for value in common_tags + [role]]
    return actor


lighting_changes = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if isinstance(actor, unreal.SkyLight) and label == "LB_PRESS_V023_FrontEndSkyLight":
        component = actor.get_component_by_class(unreal.SkyLightComponent)
        component.set_editor_property("real_time_capture", False)
        merge_tags(actor, common_tags + ["LB.Lighting.SkyCapture.Baked"])
        lighting_changes.append({"actor": label, "change": "real_time_capture=false"})
    if isinstance(actor, unreal.DirectionalLight):
        component = actor.get_component_by_class(unreal.DirectionalLightComponent)
        if label == "LB_PRESS_DirectionalFill":
            component.set_editor_property("forward_shading_priority", 1)
            merge_tags(actor, common_tags)
            lighting_changes.append({"actor": label, "change": "forward_shading_priority=1"})
        elif label == "LB_INT_FRONT_FrontEndAmbientBounce":
            component.set_editor_property("affects_world", False)
            component.set_editor_property("intensity", 0.0)
            merge_tags(actor, common_tags)
            lighting_changes.append({"actor": label, "change": "disabled superseded ambient directional"})

    component = None
    if isinstance(actor, unreal.PointLight):
        component = actor.get_component_by_class(unreal.PointLightComponent)
    elif isinstance(actor, unreal.SpotLight):
        component = actor.get_component_by_class(unreal.SpotLightComponent)
    elif isinstance(actor, unreal.RectLight):
        component = actor.get_component_by_class(unreal.RectLightComponent)
    if component is None:
        continue
    disable_prefixes = (
        "LB_PR008_V058_", "LB_PR008_V062_", "LB_MOTH_V004_EmergencyPool_",
        "LB_PR004_V028_CraneServiceFill", "LB_PR004_V031_CHookCameraFill",
        "LB_PR004_V034_", "LB_PR004_V037_", "LB_PR004_V040_",
    )
    if label.startswith(disable_prefixes):
        component.set_editor_property("affects_world", False)
        component.set_editor_property("intensity", 0.0)
        merge_tags(actor, common_tags)
        lighting_changes.append({"actor": label, "change": "disabled superseded/exception-state light"})
    elif label.startswith("LB_PR004_V041_Downlight_"):
        old = float(component.get_editor_property("intensity"))
        new = round(old * 0.56, 3)
        component.set_editor_property("intensity", new)
        merge_tags(actor, common_tags)
        lighting_changes.append({"actor": label, "change": f"calibrated {old}->{new}"})

slab_joints = []
for x in range(-12600, 4201, 600):
    slab_joints.append(add_mesh(
        f"LB_ENV_V138_SlabJoint_X_{x:+06d}", (x, -2000, 1.2), (0.18, 120.0, 0.04),
        materials["joint"], "LB.Environment.Floor.SawCutJoint"))
for y in range(-5600, 1601, 600):
    slab_joints.append(add_mesh(
        f"LB_ENV_V138_SlabJoint_Y_{y:+06d}", (-4200, y, 1.25), (168.0, 0.18, 0.04),
        materials["joint"], "LB.Environment.Floor.SawCutJoint"))

route_parts = [add_mesh(
    "LB_ENV_V138_MainLogisticsSpine", (-4200, 600, 1.4), (168.0, 18.0, 0.045),
    materials["route"], "LB.Environment.Route.MainLogisticsSpine")]
for x in range(-12000, 3601, 800):
    route_parts.append(add_mesh(
        f"LB_ENV_V138_RouteDash_{x:+06d}", (x, 600, 2.0), (3.2, 0.16, 0.03),
        materials["yellow"], "LB.Environment.Route.CentreDash"))

fixtures = []
lights = []
for row_y in (-3600, -400):
    for x in range(-11800, 3001, 1600):
        index = len(lights) + 1
        fixtures.append(add_mesh(
            f"LB_ENV_V138_Luminaire_{index:02d}", (x, row_y, 1760), (7.0, 0.42, 0.10),
            materials["lens"], "LB.Environment.Luminaire"))
        light = actors_api.spawn_actor_from_class(
            unreal.RectLight, unreal.Vector(x, row_y, 1725), unreal.Rotator(-90.0, 0.0, 0.0))
        light.set_actor_label(f"LB_ENV_V138_AmbientRect_{index:02d}")
        component = light.get_component_by_class(unreal.RectLightComponent)
        component.set_editor_properties({
            "intensity": 6.5,
            "source_width": 1250.0,
            "source_height": 110.0,
            "attenuation_radius": 2050.0,
            "cast_shadows": False,
            "light_color": unreal.Color(214, 225, 228, 255),
        })
        light.tags = [unreal.Name(value) for value in common_tags + ["LB.Environment.Light.ContinuousAmbient"]]
        lights.append(light)


def add_camera(label, location, target, fov):
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov, "aspect_ratio": 16.0 / 9.0, "constrain_aspect_ratio": True,
    })
    camera.tags = [unreal.Name(value) for value in common_tags + [
        "LB.Camera.Validation", "LB.Camera.Fixed.PR003PR004HallContext.v138"]]
    return camera


cameras = [
    add_camera("LB_ENV_V138_CAM_FrontEndFlow", (-10600, 900, 980), (-7200, -2100, 520), 59.0),
    add_camera("LB_ENV_V138_CAM_CraneCoil", (-10100, -5000, 1180), (-7000, -2100, 780), 57.0),
    add_camera("LB_ENV_V138_CAM_PR003AGV", (-9000, 900, 510), (-5700, -2200, 170), 58.0),
    add_camera("LB_ENV_V138_CAM_PR004Cell", (-3600, -4700, 640), (-5050, -2050, 260), 54.0),
    add_camera("LB_ENV_V138_CAM_LogisticsSpine", (-9000, 1200, 340), (-3000, 500, 120), 62.0),
]

failures = []
if len(lighting_changes) < 20:
    failures.append(f"expected at least 20 retained lighting calibrations, found {len(lighting_changes)}")
if len(slab_joints) != 42:
    failures.append(f"expected 42 slab joints, found {len(slab_joints)}")
if len(route_parts) != 21:
    failures.append(f"expected 21 route parts, found {len(route_parts)}")
if len(fixtures) != 20 or len(lights) != 20:
    failures.append(f"expected 20 fixtures/lights, found {len(fixtures)}/{len(lights)}")
if len(cameras) != 5:
    failures.append(f"expected five cameras, found {len(cameras)}")
if not levels.save_current_level():
    failures.append("could not save v138")

base_hash_after = sha256(BASE_PACKAGE)
if base_hash_after != base_hash_before:
    failures.append("immutable v136 package changed")

report = {
    "$schema": "cairnwell/audit/press-shop-pr003-pr004-hall-context-build-v138/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__RETAINED_V107_HALL_POLICY_APPLIED_TO_V136_CHILD__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V138_HALL_CONTEXT_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "source_policy": "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107",
    "v117_floor_rebound": False,
    "station_authority_changed": False,
    "agv_authority_changed": False,
    "powered_hook_authority_changed": False,
    "lighting_changes": lighting_changes,
    "slab_joint_count": len(slab_joints),
    "route_part_count": len(route_parts),
    "luminaire_count": len(fixtures),
    "ambient_light_count": len(lights),
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "protected_v136_sha256_before": base_hash_before,
    "protected_v136_sha256_after": base_hash_after,
    "promotion_authorized": False,
    "press_shop_complete": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
