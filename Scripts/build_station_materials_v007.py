"""build_station_materials_v007.py - master material rebuilt clean.

Diagnosis trail (polish night, owner asleep): pixel-identical captures
before/after both the v005 master-default bump and the v006 per-MI
boost writes proved the BaseColorBoost never reaches the shader. The
saved graph LOOKS right (probe v001: BASECOLOR fed by a Multiply) but
expression inputs are unreadable from Python in 5.8, so rather than
guess which link or cached shader map is stale, this supersedes the
master: a fresh M_LB_MeshyPBR_v003 with the whole correct chain built
in one pass - BaseColor x Boost x SteelTint -> BASE_COLOR, Normal ->
NORMAL, glTF MR B -> METALLIC / G -> ROUGHNESS - and every MI
reparented to it, textures carried over, measured per-model boosts
(v006 table, target 0.22 linear) re-asserted. A fresh asset means a
fresh shader map: no stale-DDC ambiguity survives this.
"""

import unreal

MAT_DIR = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials"
OLD = MAT_DIR + "/M_LB_MeshyPBR_v002"
NEW_NAME = "M_LB_MeshyPBR_v003"
NEW = MAT_DIR + "/" + NEW_NAME

BOOSTS = {
    "CircuitFab": 1.01, "DroneAssembly": 3.55, "DroneCargoLift": 3.67,
    "DroneSpray": 4.00, "DroneWinch": 3.73, "PowerCellPlant": 1.47,
    "PowerPlant": 1.00, "PropulsionStation": 1.23, "RollingMill": 1.50,
    "StorageRack": 4.49, "SubAssemblyRobot": 1.54,
}

mel = unreal.MaterialEditingLibrary
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

if lib.does_asset_exist(NEW):
    raise RuntimeError("FAIL CLOSED: %s already exists" % NEW)

mat = tools.create_asset(NEW_NAME, MAT_DIR, unreal.Material,
                         unreal.MaterialFactoryNew())

base = mel.create_material_expression(
    mat, unreal.MaterialExpressionTextureSampleParameter2D, -900, -300)
base.set_editor_property("parameter_name", "BaseColor")
boost = mel.create_material_expression(
    mat, unreal.MaterialExpressionScalarParameter, -900, -80)
boost.set_editor_property("parameter_name", "BaseColorBoost")
boost.set_editor_property("default_value", 1.5)
mul1 = mel.create_material_expression(
    mat, unreal.MaterialExpressionMultiply, -620, -220)
mel.connect_material_expressions(base, "RGB", mul1, "A")
mel.connect_material_expressions(boost, "", mul1, "B")
tint = mel.create_material_expression(
    mat, unreal.MaterialExpressionVectorParameter, -620, -20)
tint.set_editor_property("parameter_name", "SteelTint")
tint.set_editor_property("default_value",
                         unreal.LinearColor(0.94, 0.99, 1.08, 1.0))
mul2 = mel.create_material_expression(
    mat, unreal.MaterialExpressionMultiply, -380, -160)
mel.connect_material_expressions(mul1, "", mul2, "A")
mel.connect_material_expressions(tint, "", mul2, "B")
mel.connect_material_property(mul2, "",
                              unreal.MaterialProperty.MP_BASE_COLOR)

norm = mel.create_material_expression(
    mat, unreal.MaterialExpressionTextureSampleParameter2D, -900, 260)
norm.set_editor_property("parameter_name", "Normal")
norm.set_editor_property("sampler_type",
                         unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
mel.connect_material_property(norm, "RGB",
                              unreal.MaterialProperty.MP_NORMAL)

mr = mel.create_material_expression(
    mat, unreal.MaterialExpressionTextureSampleParameter2D, -900, 520)
mr.set_editor_property("parameter_name", "MetallicRoughness")
mr.set_editor_property("sampler_type",
                       unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
mel.connect_material_property(mr, "B", unreal.MaterialProperty.MP_METALLIC)
mel.connect_material_property(mr, "G", unreal.MaterialProperty.MP_ROUGHNESS)

# The samplers need real default textures or the compile fails closed:
# borrow the current defaults from the old master's expressions.
old = unreal.load_asset(OLD)
defaults = {}
for e in mel.get_material_expressions(old):
    if isinstance(e, unreal.MaterialExpressionTextureSampleParameter2D):
        defaults[str(e.get_editor_property("parameter_name"))] = \
            e.get_editor_property("texture")
for expr, key in ((base, "BaseColor"), (norm, "Normal"),
                  (mr, "MetallicRoughness")):
    if defaults.get(key) is not None:
        expr.set_editor_property("texture", defaults[key])

mel.recompile_material(mat)
lib.save_asset(NEW)
unreal.log("MASTER v003 built")

for key, val in BOOSTS.items():
    path = "%s/MI_LB_%s" % (MAT_DIR, key)
    mi = unreal.load_asset(path)
    if mi is None:
        raise RuntimeError("FAIL CLOSED: %s missing" % path)
    mel.set_material_instance_parent(mi, mat)
    mel.set_material_instance_scalar_parameter_value(
        mi, "BaseColorBoost", val)
    mel.update_material_instance(mi)
    lib.save_asset(path)
    unreal.log("REPARENTED %s boost=%.2f" % (key, val))
unreal.log("REBUILD v007 DONE: 11 instances on fresh master")
