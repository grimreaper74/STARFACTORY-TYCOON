"""Build isolated PR005 v199 material/logistics release-art candidate from v198."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
PARENT = "/Game/LineBoss/Maps/LB_PressShop_PR005AudioRuntimeCandidate_v198"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PR005ReleaseArtCandidate_v199"
PARENT_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PR005AudioRuntimeCandidate_v198.umap"
MESH_PATH = "/Game/LineBoss/Candidates/PressShop/PR005/ServiceLogistics_v007/Meshes/SM_CA_MW_PR005_ServiceLogistics_Static_v007"
MAT_DIR = "/Game/LineBoss/Candidates/PressShop/PR005/ReleaseArt_v199/Materials"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_pr005_release_art_build_v199.json"
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def layered_surface(name, face, edge, metallic, face_roughness, edge_roughness, edge_strength):
    material = tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(f"could not create {name}")
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


def translucent_glass(name):
    material = tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    if material is None:
        raise RuntimeError(name)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property("two_sided", True)
    colour = mel.create_material_expression(material, unreal.MaterialExpressionConstant3Vector, -260, -80)
    colour.set_editor_property("constant", unreal.LinearColor(0.004, 0.018, 0.020, 1.0))
    opacity = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -260, 20)
    opacity.set_editor_property("r", 0.19)
    rough = mel.create_material_expression(material, unreal.MaterialExpressionConstant, -260, 100)
    rough.set_editor_property("r", 0.30)
    mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(material)
    lib.save_loaded_asset(material, only_if_is_dirty=False)
    return material


if lib.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
parent_hash_before = sha256(PARENT_FILE)
if not levels.new_level_from_template(MAP, PARENT):
    raise RuntimeError(f"could not clone {PARENT}")

materials = {
    "roof": layered_surface("M_CA_MW_PR005_RoofCassette_v199", (0.040, 0.047, 0.048), (0.115, 0.125, 0.126), 0.40, 0.68, 0.44, 0.10),
    "charcoal": layered_surface("M_CA_MW_PR005_FoundryCharcoal_v199", (0.005, 0.008, 0.009), (0.030, 0.038, 0.040), 0.56, 0.72, 0.46, 0.11),
    "glass": translucent_glass("M_CA_MW_PR005_InspectionGlass_v199"),
    "CA_MW_ReturnBlue": layered_surface("M_CA_MW_PR005_ReturnBlue_v199", (0.008, 0.028, 0.068), (0.025, 0.085, 0.18), 0.38, 0.62, 0.42, 0.12),
    "CA_MW_ServiceOrange": layered_surface("M_CA_MW_PR005_ServiceOrange_v199", (0.15, 0.035, 0.003), (0.40, 0.12, 0.008), 0.18, 0.65, 0.44, 0.10),
    "CA_MW_LogisticsCharcoal": layered_surface("M_CA_MW_PR005_LogisticsCharcoal_v199", (0.006, 0.009, 0.010), (0.035, 0.042, 0.044), 0.54, 0.70, 0.46, 0.10),
    "CA_MW_SafetyYellow": layered_surface("M_CA_MW_PR005_LogisticsYellow_v199", (0.24, 0.10, 0.001), (0.58, 0.28, 0.005), 0.22, 0.60, 0.40, 0.09),
    "CA_MW_HardwareSteel": layered_surface("M_CA_MW_PR005_LogisticsHardware_v199", (0.12, 0.14, 0.15), (0.34, 0.37, 0.38), 0.90, 0.34, 0.22, 0.16),
    "CA_MW_LabelWhite": layered_surface("M_CA_MW_PR005_LogisticsLabel_v199", (0.42, 0.44, 0.42), (0.72, 0.74, 0.70), 0.03, 0.76, 0.58, 0.08),
    "CA_MW_RubberBlack": layered_surface("M_CA_MW_PR005_LogisticsRubber_v199", (0.002, 0.003, 0.003), (0.010, 0.012, 0.012), 0.01, 0.90, 0.78, 0.04),
}

all_actors = actors_api.get_all_level_actors()
infill_rows = [actor for actor in all_actors if actor.get_actor_label() == "LB_PR005_V197_RuntimeCageInfill_Static_v005"]
if len(infill_rows) != 1:
    raise RuntimeError(f"expected one v197 infill, got {len(infill_rows)}")
infill = infill_rows[0]
infill_slots = []
mesh = infill.static_mesh_component.get_editor_property("static_mesh")
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    name = str(slot.material_slot_name)
    if name == "CA_MW_ServiceGrey":
        infill.static_mesh_component.set_material(index, materials["roof"])
    elif name == "CA_MW_LaminatedInspectionGlass":
        infill.static_mesh_component.set_material(index, materials["glass"])
    elif name == "CA_MW_FoundryCharcoal":
        infill.static_mesh_component.set_material(index, materials["charcoal"])
    infill_slots.append({"slot": name, "override": infill.static_mesh_component.get_material(index).get_path_name()})
infill.tags = list(infill.tags) + [unreal.Name("LB.Asset.Candidate.v199"), unreal.Name("LB.PR005.ReleaseMaterialOverride")]

old_labels = {
    "LB_PR005_V053_ReturnStillage_Base", "LB_PR005_V053_ReturnStillage_Open",
    "LB_PR005_V053_ServicePallet", "LB_PR005_V053_ServiceCrate_01",
    "LB_PR005_V053_ServiceCrate_02", "LB_PR005_V053_ServiceCrate_03",
}
old_rows = [actor for actor in all_actors if actor.get_actor_label() in old_labels]
if {actor.get_actor_label() for actor in old_rows} != old_labels:
    raise RuntimeError("v053 logistics replacement scope is incomplete")
old_bounds = []
for actor in old_rows:
    origin, extent = actor.get_actor_bounds(False)
    old_bounds.append({"label": actor.get_actor_label(), "min": [origin.x-extent.x, origin.y-extent.y, origin.z-extent.z], "max": [origin.x+extent.x, origin.y+extent.y, origin.z+extent.z]})
    actors_api.destroy_actor(actor)

logistics_mesh = lib.load_asset(MESH_PATH)
if not isinstance(logistics_mesh, unreal.StaticMesh):
    raise RuntimeError(MESH_PATH)
body = logistics_mesh.get_editor_property("body_setup")
aggregate = unreal.KAggregateGeom()
boxes = []
for center, dimensions in (
    ((-102.0, 0.0, 75.0), (145.0, 112.0, 150.0)),
    ((65.0, 0.0, 32.0), (135.0, 112.0, 64.0)),
    ((162.0, 0.0, 60.0), (70.0, 94.0, 120.0)),
):
    elem = unreal.KBoxElem()
    elem.set_editor_properties({"center": unreal.Vector(*center), "rotation": unreal.Rotator(), "x": dimensions[0], "y": dimensions[1], "z": dimensions[2]})
    boxes.append(elem)
aggregate.set_editor_property("box_elems", boxes)
body.set_editor_property("agg_geom", aggregate)
body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_DEFAULT)
body.modify(); logistics_mesh.modify()
lib.save_loaded_asset(logistics_mesh, only_if_is_dirty=False)

rotation = unreal.Rotator()
rotation.set_editor_properties({"pitch": 0.0, "yaw": 0.0, "roll": 0.0})
logistics = actors_api.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-2950.0, -3340.0, 2.5), rotation)
logistics.set_actor_label("LB_PR005_V199_ServiceLogistics_Static_v007")
component = logistics.static_mesh_component
component.set_static_mesh(logistics_mesh)
component.set_mobility(unreal.ComponentMobility.STATIC)
component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
component.set_collision_profile_name(unreal.Name("BlockAll"))
component.set_editor_property("can_ever_affect_navigation", True)
for index, slot in enumerate(logistics_mesh.get_editor_property("static_materials")):
    role = str(slot.material_slot_name)
    if role not in materials:
        raise RuntimeError(f"unmapped logistics slot {role}")
    component.set_material(index, materials[role])
logistics.tags = [unreal.Name(value) for value in (
    "LB.Asset.Candidate.v199", "LB.Asset.CandidateNotPromoted", "LB.Station.PR-005",
    "LB.Logistics.StaticDressing", "LB.PR005.ReleaseArt", "LB.Authority.ProductionFlowUnchanged")]
new_origin, new_extent = logistics.get_actor_bounds(False)
new_bounds = {"min": [new_origin.x-new_extent.x, new_origin.y-new_extent.y, new_origin.z-new_extent.z], "max": [new_origin.x+new_extent.x, new_origin.y+new_extent.y, new_origin.z+new_extent.z]}

# Restrained local bay fill; no new global hall lighting policy.
for index, (x, y) in enumerate(((-3850.0, -1900.0), (-3000.0, -3320.0)), 1):
    light = actors_api.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, y, 560.0), unreal.Rotator(-90.0, 0.0, 0.0))
    light.set_actor_label(f"LB_PR005_V199_LocalBayLED_{index:02d}")
    light.get_component_by_class(unreal.RectLightComponent).set_editor_properties({
        "intensity": 3.0 if index == 1 else 2.2, "source_width": 260.0, "source_height": 55.0,
        "attenuation_radius": 720.0, "cast_shadows": True, "light_color": unreal.Color(190, 204, 207, 255),
    })
    light.tags = [unreal.Name("LB.Asset.Candidate.v199"), unreal.Name("LB.Lighting.PR005.LocalBay")]

if not levels.save_current_level():
    raise RuntimeError(MAP)
parent_hash_after = sha256(PARENT_FILE)
failures = []
if parent_hash_before != parent_hash_after:
    failures.append("protected v198 changed")
if new_bounds["min"][2] < -0.2:
    failures.append(f"logistics below floor {new_bounds}")
report = {
    "$schema": "cairnwell/audit/press-shop-pr005-release-art-build-v199/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_PR005_RELEASE_ART_BUILD__FIXED_CAMERA_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "parent": PARENT, "map": MAP,
    "protected_v198_sha256_before": parent_hash_before, "protected_v198_sha256_after": parent_hash_after,
    "infill_material_overrides": infill_slots,
    "removed_v053_logistics": old_bounds,
    "new_service_logistics": {"actor": logistics.get_actor_label(), "asset": MESH_PATH, "world_bounds_cm": new_bounds, "collision_boxes": 3, "profile": "BlockAll", "navigation": True},
    "local_bay_lights": 2,
    "production_equipment_modified": False,
    "runtime_authority_modified": False,
    "physical_gate_motion": "UNCHANGED_TBC_NOT_INVENTED",
    "promotion_authorized": False, "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
unreal.log("LINE_BOSS_PR005_RELEASE_ART_V199_BUILD_PASS")
unreal.SystemLibrary.quit_editor()
