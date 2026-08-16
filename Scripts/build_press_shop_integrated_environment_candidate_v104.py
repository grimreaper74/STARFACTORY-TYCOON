"""Create an isolated whole-shop environment correction from accepted v103.

The accepted PR-009/PR-010 map is immutable.  This candidate fixes the exact
lighting warnings and the pillar-texture floor failure found in the user's
free-camera walkthrough, then adds fixed whole-shop evidence cameras.  It does
not claim station or whole-shop promotion.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PR010Accepted_v103"
MAP = "/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v104"
DEST = "/Game/LineBoss/Candidates/PressShop/IntegratedEnvironment_v104"
MAT = DEST + "/Materials"
OUT = ROOT / "Saved/Audits/PressShopIntegration/integrated_environment_build_v104.json"

library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("could not create isolated v104 from accepted v103")


def expression(material, klass, x, y):
    return mel.create_material_expression(material, klass, x, y)


def sealed_material(name, dark, light, rough_dark=0.82, rough_light=0.72, noise_scale=1.35):
    material = asset_tools.create_asset(name, MAT, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"could not create {MAT}/{name}")
    material.set_editor_properties({"two_sided": False})

    uv = expression(material, unreal.MaterialExpressionTextureCoordinate, -980, 0)
    scale = expression(material, unreal.MaterialExpressionConstant, -980, 120)
    scale.set_editor_property("r", noise_scale)
    scaled = expression(material, unreal.MaterialExpressionMultiply, -760, 20)
    mel.connect_material_expressions(uv, "", scaled, "A")
    mel.connect_material_expressions(scale, "", scaled, "B")
    noise = expression(material, unreal.MaterialExpressionNoise, -540, 20)
    noise.set_editor_properties({
        "quality": 1,
        "levels": 2,
        "output_min": 0.28,
        "output_max": 0.72,
    })
    mel.connect_material_expressions(scaled, "", noise, "Position")

    colour_a = expression(material, unreal.MaterialExpressionConstant3Vector, -520, -180)
    colour_a.set_editor_property("constant", unreal.LinearColor(*dark, 1.0))
    colour_b = expression(material, unreal.MaterialExpressionConstant3Vector, -520, -95)
    colour_b.set_editor_property("constant", unreal.LinearColor(*light, 1.0))
    colour = expression(material, unreal.MaterialExpressionLinearInterpolate, -260, -110)
    mel.connect_material_expressions(colour_a, "", colour, "A")
    mel.connect_material_expressions(colour_b, "", colour, "B")
    mel.connect_material_expressions(noise, "", colour, "Alpha")

    rough_a = expression(material, unreal.MaterialExpressionConstant, -260, 90)
    rough_a.set_editor_property("r", rough_dark)
    rough_b = expression(material, unreal.MaterialExpressionConstant, -260, 165)
    rough_b.set_editor_property("r", rough_light)
    rough = expression(material, unreal.MaterialExpressionLinearInterpolate, 0, 120)
    mel.connect_material_expressions(rough_a, "", rough, "A")
    mel.connect_material_expressions(rough_b, "", rough, "B")
    mel.connect_material_expressions(noise, "", rough, "Alpha")
    metal = expression(material, unreal.MaterialExpressionConstant, 0, 220)
    metal.set_editor_property("r", 0.015)

    mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(material)
    library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


materials = {
    "neutral": sealed_material(
        "M_CA_MW_SealedFactoryConcrete_v104",
        (0.115, 0.128, 0.132), (0.155, 0.168, 0.172), 0.84, 0.74, 1.25),
    "receiving": sealed_material(
        "M_CA_MW_ReceivingConcrete_v104",
        (0.125, 0.135, 0.145), (0.175, 0.188, 0.198), 0.84, 0.75, 1.30),
    "inspection": sealed_material(
        "M_CA_MW_InspectionConcrete_v104",
        (0.145, 0.130, 0.105), (0.195, 0.178, 0.145), 0.84, 0.74, 1.28),
    "store": sealed_material(
        "M_CA_MW_CoilStoreConcrete_v104",
        (0.105, 0.140, 0.145), (0.142, 0.185, 0.188), 0.85, 0.76, 1.24),
    "hold": sealed_material(
        "M_CA_MW_HoldConcrete_v104",
        (0.165, 0.105, 0.095), (0.215, 0.135, 0.120), 0.86, 0.76, 1.22),
    "walkway": sealed_material(
        "M_CA_MW_ProtectedWalkway_v104",
        (0.070, 0.145, 0.112), (0.095, 0.190, 0.148), 0.82, 0.72, 1.35),
}


def actor_tags(actor):
    return [str(value) for value in actor.tags]


actors = actors_api.get_all_level_actors()
changed_floors = []
front_floor_map = {
    "LB_INT_FRONT_Floor_PR001": "receiving",
    "LB_INT_FRONT_Floor_PR002": "inspection",
    "LB_INT_FRONT_Floor_PR003": "store",
    "LB_INT_FRONT_Floor_HOLD": "hold",
    "LB_INT_FRONT_PedestrianRoute": "walkway",
}
zone_labels = {
    "LB_ZONE_PRESS_COIL_STORE", "LB_ZONE_PRESS_FRONT_END", "LB_ZONE_PRESS_LOGISTICS",
    "LB_ZONE_PRESS_RECEIVING", "LB_ZONE_PRESS_SUPPORT", "LB_ZONE_PRESS_TOOLING",
    "LB_ZONE_PRESS_TRAINS",
}
for actor in actors:
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    label = actor.get_actor_label()
    role = front_floor_map.get(label)
    if label in zone_labels:
        role = "neutral"
    if role is None:
        continue
    component = actor.static_mesh_component
    for index in range(max(1, component.get_num_materials())):
        component.set_material(index, materials[role])
    tags = actor_tags(actor)
    tags.extend(["LB.Asset.Candidate.v104", "LB.Environment.Floor.SealedConcrete", f"LB.Environment.Floor.Role.{role}"])
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(tags)]
    changed_floors.append({"actor": label, "role": role, "material": materials[role].get_path_name()})

# Resolve the exact runtime warnings found by the read-only v103 inspection.
lighting_changes = []
for actor in actors:
    label = actor.get_actor_label()
    if isinstance(actor, unreal.SkyLight) and label == "LB_PRESS_V023_FrontEndSkyLight":
        component = actor.get_component_by_class(unreal.SkyLightComponent)
        component.set_editor_property("real_time_capture", False)
        tags = actor_tags(actor) + ["LB.Asset.Candidate.v104", "LB.Lighting.SkyCapture.Baked"]
        actor.tags = [unreal.Name(value) for value in dict.fromkeys(tags)]
        lighting_changes.append({"actor": label, "change": "real_time_capture=false"})
    if isinstance(actor, unreal.DirectionalLight):
        component = actor.get_component_by_class(unreal.DirectionalLightComponent)
        if label == "LB_PRESS_DirectionalFill":
            component.set_editor_property("forward_shading_priority", 1)
            lighting_changes.append({"actor": label, "change": "forward_shading_priority=1"})
        elif label == "LB_INT_FRONT_FrontEndAmbientBounce":
            component.set_editor_property("affects_world", False)
            component.set_editor_property("intensity", 0.0)
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

    # Earlier candidate generations remain inherited in v103. Disable only the
    # superseded sources that overlap later installed/calibrated lighting.
    disable_prefixes = (
        "LB_PR008_V058_", "LB_PR008_V062_", "LB_MOTH_V004_EmergencyPool_",
        "LB_PR004_V028_CraneServiceFill", "LB_PR004_V031_CHookCameraFill",
        "LB_PR004_V034_", "LB_PR004_V037_", "LB_PR004_V040_",
    )
    if label.startswith(disable_prefixes):
        component.set_editor_property("affects_world", False)
        component.set_editor_property("intensity", 0.0)
        lighting_changes.append({"actor": label, "change": "disabled superseded/exception-state light"})
    elif label.startswith("LB_PR004_V041_Downlight_"):
        old = float(component.get_editor_property("intensity"))
        new = round(old * 0.56, 3)
        component.set_editor_property("intensity", new)
        lighting_changes.append({"actor": label, "change": f"calibrated {old}->{new}"})


def add_camera(label, location, target, fov):
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*location), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    camera.tags = [
        unreal.Name("LB.Camera.Validation"), unreal.Name("LB.Camera.Fixed.IntegratedEnvironment.v104"),
        unreal.Name("LB.Asset.Candidate.v104"), unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    return camera


cameras = [
    add_camera("LB_ENV_V104_CAM_WholeShop", (10400, 6100, 5200), (-1200, -1700, 650), 70.0),
    add_camera("LB_ENV_V104_CAM_FrontEnd", (-2800, 4100, 3100), (-6900, -2100, 550), 66.0),
    add_camera("LB_ENV_V104_CAM_CraneCoil", (-2600, 2600, 3700), (-6500, -2100, 900), 64.0),
    add_camera("LB_ENV_V104_CAM_ConnectedLine", (5200, 3200, 3000), (-900, -2050, 750), 62.0),
]

failures = []
if len(changed_floors) != 12:
    failures.append(f"expected 12 corrected floor/zone actors, found {len(changed_floors)}")
if len(cameras) != 4:
    failures.append(f"expected four fixed environment cameras, found {len(cameras)}")
if not levels.save_current_level():
    failures.append("could not save isolated v104")
library.save_directory(DEST, only_if_is_dirty=False, recursive=True)

report = {
    "$schema": "cairnwell/audit/press-shop-integrated-environment-build-v104/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": (
        "PASS__ISOLATED_V104_LIGHT_WARNING_AND_PILLAR_TEXTURE_FLOOR_CORRECTION_BUILT__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED"
        if not failures else "FAIL__INTEGRATED_ENVIRONMENT_V104_BUILD__NOT_PROMOTED"
    ),
    "source_map": BASE,
    "map": MAP,
    "materials": {key: value.get_path_name() for key, value in materials.items()},
    "changed_floor_actors": changed_floors,
    "lighting_changes": lighting_changes,
    "fixed_cameras": [camera.get_actor_label() for camera in cameras],
    "accepted_v103_changed": False,
    "station_authority_changed": False,
    "promotion_authorized": False,
    "press_shop_complete": False,
    "failures": failures,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
