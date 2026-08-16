"""Create a non-destructive CR01 v028 visual iteration from the v026 runtime map."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE_MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v026"
MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v028"
MAT_DIR = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v028/Materials"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v028_visual.json"

asset_library = unreal.EditorAssetLibrary
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
material_edit = unreal.MaterialEditingLibrary
factory = unreal.MaterialFactoryNew()

if asset_library.does_asset_exist(MAP):
    asset_library.delete_asset(MAP)
if not asset_library.duplicate_asset(SOURCE_MAP, MAP):
    raise RuntimeError("Could not duplicate v026 runtime map for v028 visual iteration")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)

specs = {
    "BrushedSteel": ((0.075, 0.082, 0.090), 0.62, 0.67),
    "BodyCharcoal": ((0.030, 0.042, 0.052), 0.32, 0.58),
    "FrameAnthracite": ((0.017, 0.024, 0.031), 0.48, 0.55),
    "SafetyYellow": ((0.52, 0.205, 0.004), 0.28, 0.52),
    "Floor": ((0.046, 0.044, 0.041), 0.0, 0.92),
}


def constant_material(name, colour, metallic, roughness):
    path = f"{MAT_DIR}/M_LB_CR01_{name}_v028"
    material = unreal.load_asset(path)
    if not material:
        material = asset_tools.create_asset(
            f"M_LB_CR01_{name}_v028", MAT_DIR, unreal.Material, factory
        )
    material_edit.delete_all_material_expressions(material)
    base = material_edit.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -420, -30
    )
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = material_edit.create_material_expression(
        material, unreal.MaterialExpressionConstant, -420, 130
    )
    metal.set_editor_property("r", metallic)
    rough = material_edit.create_material_expression(
        material, unreal.MaterialExpressionConstant, -420, 220
    )
    rough.set_editor_property("r", roughness)
    material_edit.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    material_edit.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    material_edit.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    material_edit.recompile_material(material)
    asset_library.save_loaded_asset(material, only_if_is_dirty=False)
    return material


materials = {name: constant_material(name, *values) for name, values in specs.items()}


def classify(material_name):
    lower = material_name.lower()
    for key in ("BrushedSteel", "BodyCharcoal", "FrameAnthracite", "SafetyYellow"):
        if key.lower() in lower:
            return key
    return None


override_slots = 0
all_actors = actors.get_all_level_actors()
for actor in all_actors:
    label = actor.get_actor_label()
    if label == "LB_CR01_V026_ValidationFloor":
        actor.set_actor_label("LB_CR01_V028_ValidationFloor")
        actor.get_editor_property("static_mesh_component").set_material(0, materials["Floor"])
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if not component:
        continue
    for index in range(component.get_num_materials()):
        current = component.get_material(index)
        key = classify(current.get_name() if current else "")
        if key:
            component.set_material(index, materials[key])
            override_slots += 1

# Rebalance evidence lighting toward readable diffuse industrial illumination.
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label == "LB_CR01_V026_KeyLight":
        actor.set_actor_label("LB_CR01_V028_KeyLight")
        actor.get_editor_property("directional_light_component").set_editor_property("intensity", 0.34)
    elif label == "LB_CR01_V026_FillFront":
        actor.set_actor_label("LB_CR01_V028_FillFront")
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 82.0)
    elif label == "LB_CR01_V026_FillRear":
        actor.set_actor_label("LB_CR01_V028_FillRear")
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 58.0)
    elif label == "LB_CR01_V026_SkyLight":
        actor.set_actor_label("LB_CR01_V028_SkyLight")
        actor.get_editor_property("light_component").set_editor_property("intensity", 0.22)
    elif label.startswith("LB_CR01_V026_RuntimeLight_"):
        actor.set_actor_label(label.replace("V026", "V028"))
        component = actor.get_component_by_class(unreal.LightComponent)
        if component and "BlueRouteProjector" in label:
            component.set_editor_property("intensity", 48.0)
        elif component and "Work_" in label:
            component.set_editor_property("intensity", 260.0)

side_fill = actors.spawn_actor_from_class(
    unreal.PointLight, unreal.Vector(0.0, -270.0, 155.0), unreal.Rotator()
)
side_fill.set_actor_label("LB_CR01_V028_FillSide")
side_component = side_fill.get_editor_property("point_light_component")
side_component.set_editor_property("intensity", 155.0)
side_component.set_editor_property("attenuation_radius", 620.0)
side_component.set_editor_property("light_color", unreal.Color(205, 220, 235, 255))

# Correct fixed cameras without modifying the v026 evidence map.
camera_specs = {
    "LB_CR01_V026_CAM_Oblique": (
        "LB_CR01_V028_CAM_Oblique", unreal.Vector(330, -350, 225), unreal.Vector(0, 0, 48), 48.0
    ),
    "LB_CR01_V026_CAM_Side": (
        "LB_CR01_V028_CAM_Side", unreal.Vector(0, -430, 120), unreal.Vector(0, 0, 48), 43.0
    ),
    "LB_CR01_V026_CAM_Top": (
        "LB_CR01_V028_CAM_Top", unreal.Vector(0, 0, 575), unreal.Vector(0, 0, 25), 47.0
    ),
}
for actor in actors.get_all_level_actors():
    spec = camera_specs.get(actor.get_actor_label())
    if not spec:
        continue
    new_label, location, target, fov = spec
    actor.set_actor_label(new_label)
    actor.set_actor_location(location, False, False)
    actor.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(location, target), False)
    actor.get_editor_property("camera_component").set_editor_property("field_of_view", fov)

if not levels.save_current_level():
    raise RuntimeError("Failed saving LB-CR01 v028 visual candidate map")

result = {
    "status": "VISUAL_CANDIDATE_NOT_PROMOTED__FRESH_SCREENSHOTS_REQUIRED",
    "source_map": SOURCE_MAP,
    "map": MAP,
    "actor_material_override_slots": override_slots,
    "camera_labels": [spec[0] for spec in camera_specs.values()],
    "visual_changes": [
        "darker rougher roof/service metals",
        "less specular charcoal/frame",
        "side diffuse fill",
        "reduced route projector and work lights",
        "wider top and evidence cameras",
    ],
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_LB_CR01_V028_BUILD_PASS overrides={override_slots}")
