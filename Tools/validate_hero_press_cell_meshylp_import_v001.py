"""Independent asset-only verification for the native low-poly hero press import.

This never loads or writes a level.  It verifies the persisted UAssets, not the
importer's own in-memory variables.
"""
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
ROOT = "/Game/LineBoss/Candidates/PressShop/HeroPressCell_MeshyLowPoly_v001"
MESH_PATH = ROOT + "/SM_LB_PS_HeroPressCell_MeshyLP_v001"
MASTER_PATH = ROOT + "/Materials/M_LB_PS_HeroPressCell_MeshyLP_v001"
INSTANCE_PATH = ROOT + "/Materials/MI_LB_PS_HeroPressCell_MeshyLP_v001"
TEXTURE_PATHS = {
    "BaseColorMap": ROOT + "/Textures/T_LB_PS_HeroPressCell_MeshyLP_BaseColor_v001",
    "MetallicRoughnessMap": ROOT + "/Textures/T_LB_PS_HeroPressCell_MeshyLP_MetallicRoughness_v001",
    "NormalMap": ROOT + "/Textures/T_LB_PS_HeroPressCell_MeshyLP_Normal_v001",
}
REPORT_PATH = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "hero_press_cell_meshylp_unreal_validation_v001.json"
EXPECTED_BOUNDS_CM = (1914.018, 618.691, 800.0)


def fail(message):
    raise RuntimeError("HERO_PRESS_CELL_VALIDATION_FAIL: " + message)


mesh = unreal.load_asset(MESH_PATH)
master = unreal.load_asset(MASTER_PATH)
instance = unreal.load_asset(INSTANCE_PATH)
if not isinstance(mesh, unreal.StaticMesh):
    fail("candidate mesh is missing or wrong class")
if not isinstance(master, unreal.Material):
    fail("native master material is missing or wrong class")
if not isinstance(instance, unreal.MaterialInstanceConstant):
    fail("native material instance is missing or wrong class")

bounds = mesh.get_bounding_box()
dimensions = (bounds.max.x - bounds.min.x, bounds.max.y - bounds.min.y, bounds.max.z - bounds.min.z)
if any(abs(actual - expected) > 3.0 for actual, expected in zip(dimensions, EXPECTED_BOUNDS_CM)):
    fail("mesh bounds {} do not match {} cm".format(dimensions, EXPECTED_BOUNDS_CM))
try:
    triangles = int(mesh.get_num_triangles(0))
except Exception as error:
    fail("could not query persisted LOD0 triangle count: {}".format(error))
if triangles != 3917:
    fail("persisted LOD0 triangle count {} is not 3,917".format(triangles))
if len(mesh.static_materials) != 1:
    fail("expected one mesh material slot, found {}".format(len(mesh.static_materials)))
assigned = mesh.static_materials[0].material_interface
if assigned.get_path_name().split(".")[0] != INSTANCE_PATH:
    fail("mesh material slot is not the native instance: {}".format(assigned.get_path_name()))
parent = instance.get_editor_property("parent")
if parent.get_path_name().split(".")[0] != MASTER_PATH:
    fail("instance parent is not the native master: {}".format(parent.get_path_name()))

textures = {}
for parameter, asset_path in TEXTURE_PATHS.items():
    texture = unreal.load_asset(asset_path)
    if not isinstance(texture, unreal.Texture):
        fail("{} source texture is missing".format(parameter))
    assigned_texture = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(instance, parameter)
    if assigned_texture is None or assigned_texture.get_path_name().split(".")[0] != asset_path:
        fail("{} is not assigned to the material instance".format(parameter))
    textures[parameter] = {
        "path": texture.get_path_name(),
        "srgb": bool(texture.get_editor_property("srgb")),
        "compression": str(texture.get_editor_property("compression_settings")),
        "flip_green": bool(texture.get_editor_property("flip_green_channel")),
    }
if not textures["BaseColorMap"]["srgb"]:
    fail("base colour must be sRGB")
if textures["MetallicRoughnessMap"]["srgb"]:
    fail("metallic/roughness map must be linear")
if textures["NormalMap"]["srgb"] or not textures["NormalMap"]["flip_green"]:
    fail("normal map must be linear and have its OpenGL green channel flipped")

roughness = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(
    instance, "RoughnessMultiplier")
if abs(float(roughness) - 1.30) > 0.001:
    fail("unexpected roughness multiplier {}".format(roughness))

report = {
    "status": "PASS__PERSISTED_UNREAL_CANDIDATE_ASSET_ONLY",
    "map_loaded": False,
    "map_saved": False,
    "mesh": {"path": mesh.get_path_name(), "triangles_lod0": triangles,
             "bounds_cm": [round(value, 3) for value in dimensions],
             "material_slot": assigned.get_path_name()},
    "material": {"master": master.get_path_name(), "instance": instance.get_path_name(),
                 "roughness_multiplier": float(roughness)},
    "textures": textures,
    "collision": "not yet authored",
    "lods": "LOD0 only; appropriate for this 3,917-triangle candidate until the in-map review proves a need for more",
    "next_gate": "new map only: dedicated visual placement, lighting and performance capture",
}
REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
REPORT_PATH.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("LINE_BOSS_HERO_PRESS_CELL_VALIDATION=" + json.dumps(report, sort_keys=True))
