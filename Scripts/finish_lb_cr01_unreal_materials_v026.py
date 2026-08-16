"""Replace pale FBX placeholders with native Unreal CR01 candidate materials."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MESH_DIR = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v026/LOD0"
MAT_DIR = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v026/Materials"
MAP = "/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v026"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v026_materials.json"

factory = unreal.MaterialFactoryNew()
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

specs = {
    "Oxide": ((0.16, 0.055, 0.018), 0.0, 0.82),
    "Bristle": ((0.012, 0.014, 0.015), 0.0, 0.92),
    "BrushedSteel": ((0.115, 0.125, 0.135), 0.76, 0.52),
    "RecessBlack": ((0.006, 0.008, 0.010), 0.0, 0.78),
    "SensorGlass": ((0.008, 0.055, 0.075), 0.12, 0.14),
    "BodyCharcoal": ((0.035, 0.045, 0.052), 0.55, 0.43),
    "FrameAnthracite": ((0.020, 0.025, 0.030), 0.68, 0.40),
    "RubberBlack": ((0.005, 0.006, 0.007), 0.0, 0.94),
    "SafetyYellow": ((0.58, 0.245, 0.006), 0.36, 0.46),
    "Floor": ((0.055, 0.052, 0.047), 0.0, 0.91),
}

def constant_material(name, colour, metallic, roughness):
    path = f"{MAT_DIR}/M_LB_CR01_{name}_v026"
    material = unreal.load_asset(path)
    if not material:
        material = tools.create_asset(f"M_LB_CR01_{name}_v026", MAT_DIR, unreal.Material, factory)
    mel.delete_all_material_expressions(material)
    base = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -420, -30)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 130)
    metal.set_editor_property("r", metallic)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -420, 220)
    rough.set_editor_property("r", roughness)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material

materials = {key: constant_material(key, *value) for key, value in specs.items()}

lens_path = f"{MAT_DIR}/M_LB_CR01_LensVertexTint_v026"
lens = unreal.load_asset(lens_path)
if not lens:
    lens = tools.create_asset("M_LB_CR01_LensVertexTint_v026", MAT_DIR, unreal.Material, factory)
mel.delete_all_material_expressions(lens)
vertex = mel.create_material_expression(lens, unreal.MaterialExpressionVertexColor, -460, -40)
rough = mel.create_material_expression(lens, unreal.MaterialExpressionConstant, -460, 190)
rough.set_editor_property("r", 0.22)
mel.connect_material_property(vertex, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(vertex, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.recompile_material(lens)
unreal.EditorAssetLibrary.save_loaded_asset(lens, only_if_is_dirty=False)
materials["LensVertexTint"] = lens

def classify(name):
    lower = name.lower()
    for key in ("Oxide", "Bristle", "BrushedSteel", "RecessBlack", "SensorGlass", "BodyCharcoal", "FrameAnthracite", "RubberBlack", "SafetyYellow", "LensVertexTint"):
        if key.lower() in lower:
            return key
    return None

mesh_count = slot_count = 0
unmatched = []
bindings = {}
for path in unreal.EditorAssetLibrary.list_assets(MESH_DIR, recursive=False, include_folder=False):
    mesh = unreal.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        continue
    mesh_count += 1
    for index in range(mesh.get_num_sections(0)):
        current = mesh.get_material(index)
        source_name = current.get_name() if current else "None"
        key = classify(source_name)
        if not key:
            unmatched.append({"mesh": path, "slot": index, "source": source_name})
            continue
        mesh.set_material(index, materials[key])
        slot_count += 1
        bindings[source_name] = key
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label == "LB_CR01_V026_ValidationFloor":
        actor.get_editor_property("static_mesh_component").set_material(0, materials["Floor"])
    elif label == "LB_CR01_V026_KeyLight":
        actor.get_editor_property("directional_light_component").set_editor_property("intensity", 0.58)
    elif label == "LB_CR01_V026_FillFront":
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 55.0)
    elif label == "LB_CR01_V026_FillRear":
        actor.get_editor_property("point_light_component").set_editor_property("intensity", 32.0)
    elif label == "LB_CR01_V026_SkyLight":
        actor.get_editor_property("light_component").set_editor_property("intensity", 0.10)

# Replace painted-only indications with restrained, functional runtime lights.
# Each light is attached to its matching travelling mesh actor so the six-second
# evidence sequence moves the lighting package with the vehicle.
existing_runtime_lights = [
    actor for actor in actors.get_all_level_actors()
    if actor.get_actor_label().startswith("LB_CR01_V026_RuntimeLight_")
]
if existing_runtime_lights:
    actors.destroy_actors(existing_runtime_lights)

def find_anchor(token):
    matches = [actor for actor in actors.get_all_level_actors() if token in actor.get_actor_label()]
    if len(matches) != 1:
        raise RuntimeError(f"Expected one light anchor for {token}; found {len(matches)}")
    return matches[0]

def attach_keep_world(child, parent):
    child.attach_to_actor(
        parent, "",
        unreal.AttachmentRule.KEEP_WORLD,
        unreal.AttachmentRule.KEEP_WORLD,
        unreal.AttachmentRule.KEEP_WORLD,
        False,
    )

runtime_lights = []
for suffix in ("L", "R"):
    anchor = find_anchor(f"SM_LB_CR01_WorkLight_{suffix}")
    light = actors.spawn_actor_from_class(
        unreal.SpotLight, anchor.get_actor_location(), unreal.Rotator(-7.0, 180.0, 0.0)
    )
    light.set_actor_label(f"LB_CR01_V026_RuntimeLight_Work_{suffix}")
    component = light.get_editor_property("spot_light_component")
    component.set_editor_property("intensity", 430.0)
    component.set_editor_property("light_color", unreal.Color(255, 224, 184, 255))
    component.set_editor_property("attenuation_radius", 520.0)
    component.set_editor_property("inner_cone_angle", 19.0)
    component.set_editor_property("outer_cone_angle", 34.0)
    attach_keep_world(light, anchor)
    runtime_lights.append(light.get_actor_label())

for suffix in ("L", "R"):
    anchor = find_anchor(f"SM_LB_CR01_RearLight_{suffix}")
    light = actors.spawn_actor_from_class(unreal.PointLight, anchor.get_actor_location(), unreal.Rotator())
    light.set_actor_label(f"LB_CR01_V026_RuntimeLight_Rear_{suffix}")
    component = light.get_editor_property("point_light_component")
    component.set_editor_property("intensity", 38.0)
    component.set_editor_property("light_color", unreal.Color(255, 16, 5, 255))
    component.set_editor_property("attenuation_radius", 105.0)
    attach_keep_world(light, anchor)
    runtime_lights.append(light.get_actor_label())

anchor = find_anchor("SM_LB_RP01_StackLens_Amber")
light = actors.spawn_actor_from_class(unreal.PointLight, anchor.get_actor_location(), unreal.Rotator())
light.set_actor_label("LB_CR01_V026_RuntimeLight_StackAmber")
component = light.get_editor_property("point_light_component")
component.set_editor_property("intensity", 24.0)
component.set_editor_property("light_color", unreal.Color(255, 112, 0, 255))
component.set_editor_property("attenuation_radius", 82.0)
attach_keep_world(light, anchor)
runtime_lights.append(light.get_actor_label())

# Blue projected route/safety patch: physically attached to the left work-light
# datum and aimed down/ahead. It is deliberately subtle in the bright test bay.
anchor = find_anchor("SM_LB_CR01_WorkLight_L")
route = actors.spawn_actor_from_class(
    unreal.SpotLight, anchor.get_actor_location(), unreal.Rotator(-56.0, 180.0, 0.0)
)
route.set_actor_label("LB_CR01_V026_RuntimeLight_BlueRouteProjector")
component = route.get_editor_property("spot_light_component")
component.set_editor_property("intensity", 155.0)
component.set_editor_property("light_color", unreal.Color(0, 72, 255, 255))
component.set_editor_property("attenuation_radius", 260.0)
component.set_editor_property("inner_cone_angle", 8.0)
component.set_editor_property("outer_cone_angle", 15.0)
attach_keep_world(route, anchor)
runtime_lights.append(route.get_actor_label())
if not levels.save_current_level():
    raise RuntimeError("Failed saving corrected CR01 material evidence map")

result = {
    "status": "CANDIDATE_MATERIAL_BINDINGS_PASS__RUNTIME_VISUAL_GATE_REQUIRED",
    "mesh_count": mesh_count, "bound_slots": slot_count,
    "unmatched": unmatched, "unmatched_count": len(unmatched), "bindings": bindings,
    "native_materials": {key: value.get_path_name() for key, value in materials.items()},
    "runtime_lights": runtime_lights,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
if unmatched:
    raise RuntimeError(f"Unmatched CR01 material slots: {len(unmatched)}")
unreal.log(f"LINE_BOSS_LB_CR01_V026_MATERIAL_PASS meshes={mesh_count} slots={slot_count}")
