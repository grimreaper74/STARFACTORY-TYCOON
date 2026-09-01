"""v003: give the master's BaseTex a DEFAULT texture and restore MIs.

v002's graph verified every connection yet still rendered black - the
classic gotcha: a TextureSampleParameter2D with no default texture
fails to compile, and a failed material IS black, instances included.
The default only exists to make the master valid; every MI overrides it.
Also restores line_station_v001's graded MI after the diagnostic swap
to BasicShapeMaterial (which proved the meshes light correctly).
"""
import unreal

lib = unreal.MaterialEditingLibrary
mat = unreal.load_asset("/Game/Spacecraft/Props/M_LB_ConceptGraded_v001")
default_tex = unreal.load_asset("/Engine/EngineResources/DefaultTexture")
fixed = False
for expr in lib.get_material_expressions(mat) if hasattr(lib, "get_material_expressions") else []:
    pass
# get_material_expressions may not exist; rebuild the one node instead:
# find via iterating is unreliable across versions - simplest robust fix:
# delete + rebuild graph again WITH the default texture set.
lib.delete_all_material_expressions(mat)
def node(cls, x, y):
    n = lib.create_material_expression(mat, cls, x, y)
    assert n is not None
    return n
tex = node(unreal.MaterialExpressionTextureSampleParameter2D, -1000, 0)
tex.set_editor_property("parameter_name", "BaseTex")
tex.set_editor_property("texture", default_tex)
desat = node(unreal.MaterialExpressionDesaturation, -700, 0)
assert lib.connect_material_expressions(tex, "RGB", desat, "")
lift = node(unreal.MaterialExpressionMultiply, -520, 0)
lift.set_editor_property("const_b", 1.7)
assert lib.connect_material_expressions(desat, "", lift, "A")
clamp = node(unreal.MaterialExpressionClamp, -380, 0)
assert lib.connect_material_expressions(lift, "", clamp, "")
graphite = node(unreal.MaterialExpressionConstant3Vector, -520, 160)
graphite.set_editor_property("constant", unreal.LinearColor(0.069, 0.077, 0.084, 1.0))
pale = node(unreal.MaterialExpressionConstant3Vector, -520, 300)
pale.set_editor_property("constant", unreal.LinearColor(0.68, 0.65, 0.60, 1.0))
two = node(unreal.MaterialExpressionLinearInterpolate, -180, 40)
assert lib.connect_material_expressions(graphite, "", two, "A")
assert lib.connect_material_expressions(pale, "", two, "B")
assert lib.connect_material_expressions(clamp, "", two, "Alpha")
assert lib.connect_material_property(two, "", unreal.MaterialProperty.MP_BASE_COLOR)
rough = node(unreal.MaterialExpressionScalarParameter, -180, 300)
rough.set_editor_property("parameter_name", "Roughness")
rough.set_editor_property("default_value", 0.55)
assert lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
lib.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)

mesh = unreal.load_asset("/Game/Spacecraft/Props/line_station_v001/line_station_v001")
mi = unreal.load_asset("/Game/Spacecraft/Props/line_station_v001/MI_line_station_v001_Graded")
mats = mesh.get_editor_property("static_materials")
for i in range(len(mats)):
    mesh.set_material(i, mi)
unreal.EditorAssetLibrary.save_loaded_asset(mesh)
unreal.log("V003 MASTER FIXED (default texture set) + station MI restored")
