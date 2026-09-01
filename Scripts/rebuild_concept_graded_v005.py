"""v005: recreate M_LB_ConceptGraded_v001 as a FRESH asset (cook fix).

Every packaged cook dies with "Array index out of bounds: 2 into an
array of size 1" the moment this material compiles for PCD3D_SM5 —
the one shader platform the editor itself never compiles, which is why
PIE has always been fine. The asset has been rebuilt in place four
times (v001..v004 all call delete_all_material_expressions on the same
object), so before blaming the graph, this lane deletes the asset and
recreates it at the same path with the identical v004 graph. Same-path
recreation is reference-safe: uasset imports resolve by package/object
name, and the C++ presenter loads it by path.
"""
import unreal

PATH = "/Game/Spacecraft/Props/M_LB_ConceptGraded_v001"

if unreal.EditorAssetLibrary.does_asset_exist(PATH):
    assert unreal.EditorAssetLibrary.delete_asset(PATH), "delete failed"
    unreal.log("GRADE V005: deleted stale asset")

tools = unreal.AssetToolsHelpers.get_asset_tools()
mat = tools.create_asset(
    asset_name="M_LB_ConceptGraded_v001",
    package_path="/Game/Spacecraft/Props",
    asset_class=unreal.Material,
    factory=unreal.MaterialFactoryNew())
assert mat is not None, "create failed"

lib = unreal.MaterialEditingLibrary
default_tex = unreal.load_asset("/Engine/EngineResources/DefaultTexture")
lib.delete_all_material_expressions(mat)

def node(cls, x, y):
    n = lib.create_material_expression(mat, cls, x, y)
    assert n is not None, cls.get_name()
    return n

def conn(a, ap, b, bp):
    assert lib.connect_material_expressions(a, ap, b, bp), (ap, bp)

tex = node(unreal.MaterialExpressionTextureSampleParameter2D, -1300, 0)
tex.set_editor_property("parameter_name", "BaseTex")
tex.set_editor_property("texture", default_tex)

desat = node(unreal.MaterialExpressionDesaturation, -1000, -60)
conn(tex, "RGB", desat, "")

lift = node(unreal.MaterialExpressionMultiply, -840, -60)
lift.set_editor_property("const_b", 1.7)
conn(desat, "", lift, "A")
clamp = node(unreal.MaterialExpressionClamp, -700, -60)
conn(lift, "", clamp, "")

graphite = node(unreal.MaterialExpressionConstant3Vector, -840, 120)
graphite.set_editor_property("constant", unreal.LinearColor(0.069, 0.077, 0.084, 1.0))
pale = node(unreal.MaterialExpressionConstant3Vector, -840, 260)
pale.set_editor_property("constant", unreal.LinearColor(0.68, 0.65, 0.60, 1.0))
two = node(unreal.MaterialExpressionLinearInterpolate, -560, 40)
conn(graphite, "", two, "A")
conn(pale, "", two, "B")
conn(clamp, "", two, "Alpha")

detail_scale = node(unreal.MaterialExpressionMultiply, -840, -200)
detail_scale.set_editor_property("const_b", 0.5)
conn(desat, "", detail_scale, "A")
detail_bias = node(unreal.MaterialExpressionAdd, -700, -200)
detail_bias.set_editor_property("const_b", 0.6)
conn(detail_scale, "", detail_bias, "A")
detailed = node(unreal.MaterialExpressionMultiply, -400, -40)
conn(two, "", detailed, "A")
conn(detail_bias, "", detailed, "B")

dist = node(unreal.MaterialExpressionDistance, -840, 420)
conn(tex, "RGB", dist, "A")
conn(desat, "", dist, "B")
sat_wide = node(unreal.MaterialExpressionMultiply, -700, 420)
sat_wide.set_editor_property("const_b", 5.0)
conn(dist, "", sat_wide, "A")
sat_mask = node(unreal.MaterialExpressionClamp, -560, 420)
conn(sat_wide, "", sat_mask, "")

accent = node(unreal.MaterialExpressionMultiply, -560, 300)
accent.set_editor_property("const_b", 1.5)
conn(tex, "RGB", accent, "A")

final = node(unreal.MaterialExpressionLinearInterpolate, -200, 80)
conn(detailed, "", final, "A")
conn(accent, "", final, "B")
conn(sat_mask, "", final, "Alpha")
assert lib.connect_material_property(final, "", unreal.MaterialProperty.MP_BASE_COLOR)

rough = node(unreal.MaterialExpressionScalarParameter, -200, 320)
rough.set_editor_property("parameter_name", "Roughness")
rough.set_editor_property("default_value", 0.5)
assert lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)

lib.recompile_material(mat)
assert unreal.EditorAssetLibrary.save_loaded_asset(mat), "save failed"
unreal.log("GRADE V005 OK: fresh asset, v004 graph")
