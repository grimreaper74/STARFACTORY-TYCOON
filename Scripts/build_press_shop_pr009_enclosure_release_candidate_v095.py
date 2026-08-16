"""Build isolated PR-009 v095 enclosure refinement with release collision and a bound service door."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
PARENT_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009EnclosurePilotCandidate_v094"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009EnclosureReleaseCandidate_v095"
SOURCE_DIR = "/Game/LineBoss/Candidates/PressShop/PR009/v094/Enclosure"
ASSET_DIR = "/Game/LineBoss/Candidates/PressShop/PR009/v095/Enclosure"
MAT_DIR = "/Game/LineBoss/Candidates/PressShop/PR009/v095/EnclosureMaterials"
OUT = ROOT / "Saved/Audits/PR009_InMap_v095/enclosure_release_build.json"
OLD_PREFIX = "LB_PR009_V094_ENC_"
PREFIX = "LB_PR009_V095_ENC_"

ASSETS = [
    "SM_CA_MW_ENC_PR009_Structure_02",
    "SM_CA_MW_ENC_PR009_PanelsRoof_02",
    "SM_CA_MW_ENC_PR009_Glazing_02",
    "SM_CA_MW_ENC_PR009_ServiceDoor_02",
    "SM_CA_MW_ENC_PR009_ServiceHardware_02",
    "SM_CA_MW_ENC_PR009_Utilities_02",
    "SM_CA_MW_ENC_PR009_RoofEquipment_02",
]

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not lib.does_asset_exist(TARGET_MAP):
    if not lib.duplicate_asset(PARENT_MAP, TARGET_MAP):
        raise RuntimeError(PARENT_MAP)
    if not lib.save_asset(TARGET_MAP, only_if_is_dirty=False):
        raise RuntimeError(TARGET_MAP)
    unreal.log("PR009_V095_MAP_DUPLICATED__RERUN_FOR_REFINEMENT")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit
if not levels.load_level(TARGET_MAP):
    raise RuntimeError(TARGET_MAP)

for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if "V094" in label:
        actor.set_actor_label(label.replace("V094", "V095"))
    actor.tags = [unreal.Name(str(tag).replace("v094", "v095")) for tag in actor.tags]

for name in ASSETS:
    source = f"{SOURCE_DIR}/{name}"
    target = f"{ASSET_DIR}/{name}_v095"
    if not lib.does_asset_exist(target) and not lib.duplicate_asset(source, target):
        raise RuntimeError(f"Could not duplicate {source} to {target}")
    if not lib.save_asset(target, only_if_is_dirty=False):
        raise RuntimeError(target)


def layered_surface(name, face, edge, metallic, face_roughness, edge_roughness, edge_strength):
    path = f"{MAT_DIR}/{name}"
    material = lib.load_asset(path) if lib.does_asset_exist(path) else tools.create_asset(
        name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(path)
    mel.delete_all_material_expressions(material)
    face_node = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -520, -150)
    face_node.set_editor_property("constant", unreal.LinearColor(*face, 1.0))
    edge_node = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -520, -65)
    edge_node.set_editor_property("constant", unreal.LinearColor(*edge, 1.0))
    fresnel = mel.create_material_expression(material, unreal.MaterialExpressionFresnel, -520, 55)
    strength = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -520, 165)
    strength.set_editor_property("r", edge_strength)
    alpha = mel.create_material_expression(material, unreal.MaterialExpressionMultiply, -305, 75)
    mel.connect_material_expressions(fresnel, "", alpha, "A")
    mel.connect_material_expressions(strength, "", alpha, "B")
    colour = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, -90, -85)
    mel.connect_material_expressions(face_node, "", colour, "A")
    mel.connect_material_expressions(edge_node, "", colour, "B")
    mel.connect_material_expressions(alpha, "", colour, "Alpha")
    rough_face = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -305, 205)
    rough_face.set_editor_property("r", face_roughness)
    rough_edge = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -305, 280)
    rough_edge.set_editor_property("r", edge_roughness)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionLinearInterpolate, -90, 240)
    mel.connect_material_expressions(rough_face, "", rough, "A")
    mel.connect_material_expressions(rough_edge, "", rough, "B")
    mel.connect_material_expressions(fresnel, "", rough, "Alpha")
    metal = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -90, 345)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(material)
    lib.save_loaded_asset(material, only_if_is_dirty=False)
    return material


materials = {
    "frame": layered_surface("M_CA_MW_ENC_FoundryCharcoal_v095",
        (0.006, 0.010, 0.011), (0.030, 0.040, 0.041), 0.62, 0.58, 0.39, 0.12),
    "green": layered_surface("M_CA_MW_ENC_CairnwellGreen_v095",
        (0.008, 0.052, 0.039), (0.026, 0.125, 0.088), 0.48, 0.52, 0.34, 0.11),
    "yellow": layered_surface("M_CA_MW_ENC_SafetyYellow_v095",
        (0.34, 0.145, 0.001), (0.62, 0.30, 0.004), 0.34, 0.55, 0.36, 0.09),
    "grey": layered_surface("M_CA_MW_ENC_ServiceGrey_v095",
        (0.050, 0.058, 0.056), (0.115, 0.125, 0.119), 0.38, 0.62, 0.43, 0.08),
    "machined": layered_surface("M_CA_MW_ENC_BrushedHardware_v095",
        (0.17, 0.19, 0.20), (0.37, 0.40, 0.41), 0.94, 0.31, 0.18, 0.20),
    "rubber": layered_surface("M_CA_MW_ENC_VentBlack_v095",
        (0.003, 0.004, 0.004), (0.012, 0.014, 0.014), 0.02, 0.86, 0.72, 0.03),
}

glass_path = MAT_DIR + "/M_CA_MW_ENC_InspectionGlass_v095"
glass = lib.load_asset(glass_path) if lib.does_asset_exist(glass_path) else tools.create_asset(
    "M_CA_MW_ENC_InspectionGlass_v095", MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
mel.delete_all_material_expressions(glass)
glass.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
glass.set_editor_property("two_sided", True)
colour = mel.create_material_expression(glass, unreal.MaterialExpressionConstant3Vector, -260, -80)
colour.set_editor_property("constant", unreal.LinearColor(0.004, 0.030, 0.032, 1.0))
opacity = mel.create_material_expression(glass, unreal.MaterialExpressionConstant, -260, 20)
opacity.set_editor_property("r", 0.27)
rough = mel.create_material_expression(glass, unreal.MaterialExpressionConstant, -260, 100)
rough.set_editor_property("r", 0.22)
mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
mel.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
mel.recompile_material(glass)
lib.save_loaded_asset(glass, only_if_is_dirty=False)
materials["glass"] = glass


def role_for(slot_name):
    value = slot_name.upper()
    if "GLASS" in value: return "glass"
    if "GREEN" in value: return "green"
    if "YELLOW" in value: return "yellow"
    if "BRUSHED" in value: return "machined"
    if "GASKET" in value or "VENTBLACK" in value: return "rubber"
    if "SERVICEPANEL" in value: return "grey"
    return "frame"


def apply_boxes(mesh, specs):
    body = mesh.get_editor_property("body_setup")
    aggregate = unreal.KAggregateGeom()
    boxes = []
    for center, dimensions in specs:
        box = unreal.KBoxElem()
        box.set_editor_property("center", unreal.Vector(*center))
        box.set_editor_property("rotation", unreal.Rotator())
        box.set_editor_property("x", dimensions[0])
        box.set_editor_property("y", dimensions[1])
        box.set_editor_property("z", dimensions[2])
        boxes.append(box)
    aggregate.set_editor_property("box_elems", boxes)
    body.set_editor_property("agg_geom", aggregate)
    body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
    body.modify()
    mesh.modify()
    lib.save_loaded_asset(mesh, only_if_is_dirty=False)
    persisted = mesh.get_editor_property("body_setup").get_editor_property("agg_geom")
    if len(persisted.get_editor_property("box_elems")) != len(specs):
        raise RuntimeError(f"Collision did not persist on {mesh.get_path_name()}")


# Local-space shell collision leaves both 2.9 m material portals clear and reserves the service-door aperture.
structure_boxes = [
    ((-240.0, 0.0, 177.5), (10.0, 550.0, 355.0)),
    ((240.0, -220.0, 177.5), (10.0, 110.0, 355.0)),
    ((240.0, 101.0, 177.5), (10.0, 348.0, 355.0)),
    ((0.0, 0.0, 350.0), (490.0, 550.0, 10.0)),
    ((0.0, -270.0, 285.0), (490.0, 10.0, 140.0)),
    ((0.0, 270.0, 285.0), (490.0, 10.0, 140.0)),
    ((-195.0, -270.0, 100.0), (100.0, 10.0, 200.0)),
    ((195.0, -270.0, 100.0), (100.0, 10.0, 200.0)),
    ((-195.0, 270.0, 100.0), (100.0, 10.0, 200.0)),
    ((195.0, 270.0, 100.0), (100.0, 10.0, 200.0)),
]
door_boxes = [((231.5, -119.0, 170.0), (11.0, 92.0, 246.0))]
apply_boxes(lib.load_asset(f"{ASSET_DIR}/SM_CA_MW_ENC_PR009_Structure_02_v095"), structure_boxes)
apply_boxes(lib.load_asset(f"{ASSET_DIR}/SM_CA_MW_ENC_PR009_ServiceDoor_02_v095"), door_boxes)

module_rows = []
door_actor = None
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if not label.startswith(PREFIX + "SM_CA_MW_ENC_PR009_") or not isinstance(actor, unreal.StaticMeshActor):
        continue
    source_name = next((name for name in ASSETS if name in label), None)
    if source_name is None:
        continue
    mesh = lib.load_asset(f"{ASSET_DIR}/{source_name}_v095")
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        slot_name = str(slot.get_editor_property("imported_material_slot_name") or slot.get_editor_property("material_slot_name"))
        component.set_material(index, materials[role_for(slot_name)])
    if "Structure" in source_name or "ServiceDoor" in source_name:
        component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
        component.set_collision_profile_name(unreal.Name("BlockAll"))
        component.set_editor_property("can_ever_affect_navigation", True)
    else:
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_collision_profile_name(unreal.Name("NoCollision"))
        component.set_editor_property("can_ever_affect_navigation", False)
    if "ServiceDoor" in source_name:
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        door_actor = actor
    module_rows.append({"actor": label, "mesh": mesh.get_path_name(), "collision": str(component.get_collision_enabled())})

if len(module_rows) != 7 or door_actor is None:
    raise RuntimeError(f"Expected seven enclosure modules and one door, found {len(module_rows)}")

stations = [a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.LBPR009Station)]
if len(stations) != 1:
    raise RuntimeError(f"Expected one PR-009 station, found {len(stations)}")
station = stations[0]
if not station.bind_presentation_actor("PR009_ENC_ServiceDoor_01", "service_door", "PR009_StationRoot", door_actor):
    raise RuntimeError("Could not bind the enclosure service door to the native hinge")

# Remove v094's small text and replace it with CCTV-legible identity on the existing fascia.
for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX + "TEXT_"):
        actors_api.destroy_actor(actor)


def identity_text(label, value, location, size, colour_value):
    actor = actors_api.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=-90.0))
    actor.set_actor_label(PREFIX + "TEXT_" + label)
    actor.tags = [unreal.Name("LB.Asset.Candidate.v095"), unreal.Name("LB.Asset.CandidateNotPromoted"),
                  unreal.Name("LB.Identity.CairnwellMoorcross"), unreal.Name("LB.Navigation.Neutral")]
    component = actor.text_render
    component.set_text(value)
    component.set_world_size(size)
    component.set_text_render_color(colour_value)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor


identity_text("Corporation", "CAIRNWELL AUTOMOTIVE", (642.0, -2241.5, 304.0), 25.0,
              unreal.Color(r=70, g=220, b=165, a=255))
identity_text("Site", "MOORCROSS WORKS", (642.0, -2241.5, 286.0), 19.0,
              unreal.Color(r=228, g=235, b=230, a=255))
identity_text("Station", "PR-009  AUTOMATED BLANK STACKER", (642.0, -2241.5, 269.0), 12.0,
              unreal.Color(r=242, g=195, b=0, a=255))

# The new shell is now the physical boundary; the superseded perimeter guard no longer owns collision.
old_guards = []
for actor in actors_api.get_all_level_actors():
    if "SM_CA_MW_PR009_GuardSet_01" not in actor.get_actor_label():
        continue
    component = actor.get_component_by_class(unreal.StaticMeshComponent)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_collision_profile_name(unreal.Name("NoCollision"))
    component.set_editor_property("can_ever_affect_navigation", False)
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    old_guards.append(actor.get_actor_label())
if len(old_guards) != 1:
    raise RuntimeError(f"Expected one superseded perimeter guard, found {old_guards}")

flows = [a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.LBPressShopMaterialFlowController)]
pr008 = [a for a in actors_api.get_all_level_actors() if isinstance(a, unreal.LBPR008Station)]
if len(flows) != 1 or len(pr008) != 1:
    raise RuntimeError(f"Authority cardinality changed: flow={len(flows)} PR008={len(pr008)}")
flows[0].bind_blank_stations(pr008[0], station)

if not levels.save_current_level():
    raise RuntimeError(TARGET_MAP)

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "$schema": "cairnwell/audit/pr009-enclosure-release-build-v095/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "V095_REFINED_ENCLOSURE_WITH_RELEASE_COLLISION_AND_BOUND_INTERLOCKED_DOOR__GATES_REQUIRED__NOT_PROMOTED",
    "parent_map": PARENT_MAP,
    "target_map": TARGET_MAP,
    "modules": module_rows,
    "structure_collision_boxes": len(structure_boxes),
    "service_door_collision_boxes": len(door_boxes),
    "material_portal_clear_width_cm": 290.0,
    "service_door_binding_parent": str(door_actor.get_editor_property("root_component").get_attach_parent().get_name()),
    "superseded_guard_collision_disabled": old_guards,
    "identity_cctv_legibility_refined": True,
    "process_geometry_changed": False,
    "production_authority_changed": False,
    "line_boss_in_world": False,
    "pr010_started": False,
    "robots_modified": False,
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log(f"PR009_V095_ENCLOSURE_RELEASE_BUILD_PASS output={OUT}")
