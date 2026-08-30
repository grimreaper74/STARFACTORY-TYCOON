"""build_master_v004_v001.py - M_LB_MeshyPBR_v004: the Meshy PBR
master with EXPLICIT glTF channel wiring (owner 2026-08-26 night: the
power plant is fine in Blender but renders glossy black-and-orange in
Unreal). Meshy's metallic_roughness.jpg is glTF-packed - R = ambient
occlusion, G = ROUGHNESS, B = METALLIC. v003 fed the whole sample into
both Metallic and Roughness, so the channels were never pinned; this
master masks them explicitly and clamps roughness to a matte floor so
machine surfaces cannot turn into mirrors that reflect their own
orange cage.

Masters must compile with their OWN defaults (receipt addendum 33
lesson): the MR and Normal parameters default to linear textures.
Re-parents every station/component MI to v004 and reports the count.
"""

import unreal

ROOT = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
MAT_DIR = ROOT + "/Materials"
TEX_DIR = ROOT + "/Textures"
NAME = "M_LB_MeshyPBR_v004"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

default_base = unreal.load_asset(TEX_DIR + "/T_LB_RollingMill_BaseColor")
default_mr = unreal.load_asset(TEX_DIR + "/T_LB_RollingMill_MR")
default_nm = unreal.load_asset(TEX_DIR + "/T_LB_RollingMill_Normal")
if default_base is None or default_mr is None or default_nm is None:
    raise RuntimeError("FAIL CLOSED: default textures missing")

path = "%s/%s" % (MAT_DIR, NAME)
mat = unreal.load_asset(path)
if mat is None:
    mat = tools.create_asset(NAME, MAT_DIR, unreal.Material,
                             unreal.MaterialFactoryNew())

# --- base colour: texture * boost ---
base = mel.create_material_expression(
    mat, unreal.MaterialExpressionTextureSampleParameter2D, -800, -300)
base.set_editor_property("parameter_name", "BaseColor")
base.set_editor_property("texture", default_base)
boost = mel.create_material_expression(
    mat, unreal.MaterialExpressionScalarParameter, -800, -60)
boost.set_editor_property("parameter_name", "BaseColorBoost")
boost.set_editor_property("default_value", 1.0)
mul = mel.create_material_expression(
    mat, unreal.MaterialExpressionMultiply, -500, -200)
mel.connect_material_expressions(base, "RGB", mul, "A")
mel.connect_material_expressions(boost, "", mul, "B")
mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)

# --- metallic (B) and roughness (G), explicitly ---
mr = mel.create_material_expression(
    mat, unreal.MaterialExpressionTextureSampleParameter2D, -800, 200)
mr.set_editor_property("parameter_name", "MetallicRoughness")
mr.set_editor_property("texture", default_mr)
mr.set_editor_property("sampler_type",
                       unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
mel.connect_material_property(mr, "B", unreal.MaterialProperty.MP_METALLIC)

# Roughness floor: machines stay matte industrial, never mirrors.
rough_min = mel.create_material_expression(
    mat, unreal.MaterialExpressionScalarParameter, -800, 430)
rough_min.set_editor_property("parameter_name", "RoughnessFloor")
rough_min.set_editor_property("default_value", 0.35)
rough_max = mel.create_material_expression(
    mat, unreal.MaterialExpressionMax, -500, 300)
mel.connect_material_expressions(mr, "G", rough_max, "A")
mel.connect_material_expressions(rough_min, "", rough_max, "B")
mel.connect_material_property(rough_max, "",
                              unreal.MaterialProperty.MP_ROUGHNESS)

# --- normal ---
nm = mel.create_material_expression(
    mat, unreal.MaterialExpressionTextureSampleParameter2D, -800, 620)
nm.set_editor_property("parameter_name", "Normal")
nm.set_editor_property("texture", default_nm)
nm.set_editor_property("sampler_type",
                       unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
mel.connect_material_property(nm, "RGB", unreal.MaterialProperty.MP_NORMAL)

mel.recompile_material(mat)
lib.save_asset(path)
unreal.log("MASTER v004 BUILT")

# --- re-parent every Meshy-derived MI ---
moved = 0
for asset_path in sorted(lib.list_assets(MAT_DIR, recursive=False)):
    name = asset_path.split("/")[-1].split(".")[0]
    if not name.startswith("MI_LB_"):
        continue
    mi = unreal.load_asset(asset_path)
    if not isinstance(mi, unreal.MaterialInstanceConstant):
        continue
    parent = mi.get_editor_property("parent")
    if parent is None or "MeshyPBR" not in parent.get_name():
        continue
    mel.set_material_instance_parent(mi, mat)
    mel.update_material_instance(mi)
    lib.save_asset(asset_path.split(".")[0])
    moved += 1
    unreal.log("MASTER REPARENTED %s" % name)
unreal.log("MASTER v004 DONE: %d instances on the new master" % moved)
