"""v004: detail and accents back into the grade ("unpainted", owner).

v003's flat two-tone read as bare plastic up close - the baked panel
lines and trims are the detail language. v004 keeps the palette
two-tone as the BASE, multiplies the texture's own luminance variation
back over it (panel-line shading), and lerps the texture's saturated
accents (amber trim, blue glows) through by a saturation mask - the
v001 idea, this time with every connection asserted.
"""
import unreal

lib = unreal.MaterialEditingLibrary
mat = unreal.load_asset("/Game/Spacecraft/Props/M_LB_ConceptGraded_v001")
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

# Panel-line detail: texture luminance re-scaled to 0.6..1.1 and
# multiplied over the two-tone, so seams and vents shade the surface.
detail_scale = node(unreal.MaterialExpressionMultiply, -840, -200)
detail_scale.set_editor_property("const_b", 0.5)
conn(desat, "", detail_scale, "A")
detail_bias = node(unreal.MaterialExpressionAdd, -700, -200)
detail_bias.set_editor_property("const_b", 0.6)
conn(detail_scale, "", detail_bias, "A")
detailed = node(unreal.MaterialExpressionMultiply, -400, -40)
conn(two, "", detailed, "A")
conn(detail_bias, "", detailed, "B")

# Saturation mask via Distance(pixel, its own grey) - one node chain,
# no per-channel max/min lattice.
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
unreal.EditorAssetLibrary.save_loaded_asset(mat)
unreal.log("GRADE V004 OK: detail + accents restored")
