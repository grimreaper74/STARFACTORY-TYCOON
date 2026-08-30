"""build_bay_paint_decals_v001.py - the project's own bay-paint decal
materials.

HONEST PROVENANCE: this lane was written on a WRONG diagnosis. I
believed the Fab materials the paint lane used (MI_DangerLine_01,
MI_Decal_FloorTraces1) were surface materials that
UDecalComponent::SetDecalMaterial would refuse. Both beliefs were
false - the Fab materials are decal-domain, and the engine does not
refuse a wrong-domain material anyway (it keeps it and substitutes the
engine default decal at render time). The bad verdict came from a
string-vs-enum comparison bug in inspect_decal_materials_v001.py,
since fixed.

The two materials are kept anyway, on their own merits:

  M_LB_BayHazard_Decal_v001 - procedural diagonal hazard banding with
      no texture and NO BAKED WORDS (the game ships translated), tinted
      by two vector parameters so the colours stay tunable while the
      owner has not picked a palette. The Fab alternative needs atlas
      cell maths and carries a fixed rust-orange tint.
  M_LB_BayWear_Decal_v001 - the Fab floor-scuff texture, with opacity
      driven by the image's own darkness so the patch fades out at its
      edges instead of ending on a hard rectangle.

Fails closed if an expected source texture is missing.
"""

import unreal

ROOT = "/Game/LineBoss/Materials/Decals"
WEAR_TEX = ("/Game/Textures/T_Floor_Scratches_and_traces_BCO"
            ".T_Floor_Scratches_and_traces_BCO")

lib = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
assets = unreal.EditorAssetLibrary


def make_material(name):
    path = "%s/%s" % (ROOT, name)
    if assets.does_asset_exist(path):
        assets.delete_asset(path)
    mat = tools.create_asset(name, ROOT, unreal.Material,
                             unreal.MaterialFactoryNew())
    if mat is None:
        raise RuntimeError("FAIL CLOSED: could not create " + path)
    mat.set_editor_property("material_domain",
                            unreal.MaterialDomain.MD_DEFERRED_DECAL)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    # DecalBlendMode is a PROTECTED property and Python refuses to set
    # it, so these keep the factory default (DBM_TRANSLUCENT). That is
    # the standard deferred-decal path; if the Nanite floor turns out
    # to reject it, the fix is one dropdown in the material editor
    # (DBuffer Translucent Color,Roughness) - recorded rather than
    # worked around silently.
    return mat


def custom(mat, x, y, code, out_type, input_names, desc):
    node = lib.create_material_expression(
        mat, unreal.MaterialExpressionCustom, x, y)
    node.set_editor_property("code", code)
    node.set_editor_property("output_type", out_type)
    node.set_editor_property("description", desc)
    pins = []
    for pin_name in input_names:
        pin = unreal.CustomInput()
        pin.set_editor_property("input_name", pin_name)
        pins.append(pin)
    node.set_editor_property("inputs", pins)
    return node


# ---------------------------------------------------------------- hazard
haz = make_material("M_LB_BayHazard_Decal_v001")

uv = lib.create_material_expression(
    haz, unreal.MaterialExpressionTextureCoordinate, -900, 0)

col_a = lib.create_material_expression(
    haz, unreal.MaterialExpressionVectorParameter, -900, 200)
col_a.set_editor_property("parameter_name", "BandColorA")
col_a.set_editor_property("default_value",
                          unreal.LinearColor(0.62, 0.24, 0.02, 1.0))

col_b = lib.create_material_expression(
    haz, unreal.MaterialExpressionVectorParameter, -900, 380)
col_b.set_editor_property("parameter_name", "BandColorB")
col_b.set_editor_property("default_value",
                          unreal.LinearColor(0.05, 0.05, 0.055, 1.0))

freq = lib.create_material_expression(
    haz, unreal.MaterialExpressionScalarParameter, -900, 560)
freq.set_editor_property("parameter_name", "BandCount")
freq.set_editor_property("default_value", 6.0)

opacity = lib.create_material_expression(
    haz, unreal.MaterialExpressionScalarParameter, -900, 700)
opacity.set_editor_property("parameter_name", "PaintOpacity")
opacity.set_editor_property("default_value", 0.85)

rough = lib.create_material_expression(
    haz, unreal.MaterialExpressionScalarParameter, -900, 840)
rough.set_editor_property("parameter_name", "PaintRoughness")
rough.set_editor_property("default_value", 0.55)

# Diagonal banding straight from the decal's own UVs: no atlas, no
# cell maths, nothing baked that would need translating.
haz_code = ("float t = frac((UV.x + UV.y) * max(BandCount, 0.001));\n"
            "float band = step(0.5, t);\n"
            "return lerp(ColorA, ColorB, band);")
haz_node = custom(haz, -450, 0, haz_code,
                  unreal.CustomMaterialOutputType.CMOT_FLOAT3,
                  ["UV", "ColorA", "ColorB", "BandCount"],
                  "diagonal hazard banding")
lib.connect_material_expressions(uv, "", haz_node, "UV")
lib.connect_material_expressions(col_a, "", haz_node, "ColorA")
lib.connect_material_expressions(col_b, "", haz_node, "ColorB")
lib.connect_material_expressions(freq, "", haz_node, "BandCount")
lib.connect_material_property(haz_node, "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
lib.connect_material_property(opacity, "",
                              unreal.MaterialProperty.MP_OPACITY)
lib.connect_material_property(rough, "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
lib.recompile_material(haz)
assets.save_asset(haz.get_path_name())

# ------------------------------------------------------------------ wear
wear_tex = unreal.load_asset(WEAR_TEX)
if wear_tex is None:
    raise RuntimeError("FAIL CLOSED: missing " + WEAR_TEX)

wr = make_material("M_LB_BayWear_Decal_v001")
sample = lib.create_material_expression(
    wr, unreal.MaterialExpressionTextureSampleParameter2D, -900, 0)
sample.set_editor_property("parameter_name", "WearTexture")
sample.set_editor_property("texture", wear_tex)

strength = lib.create_material_expression(
    wr, unreal.MaterialExpressionScalarParameter, -900, 400)
strength.set_editor_property("parameter_name", "WearStrength")
strength.set_editor_property("default_value", 0.55)

wr_rough = lib.create_material_expression(
    wr, unreal.MaterialExpressionScalarParameter, -900, 540)
wr_rough.set_editor_property("parameter_name", "PaintRoughness")
wr_rough.set_editor_property("default_value", 0.80)

# The scuff image is dark marks on a pale plate; drive opacity off how
# DARK a texel is so the pale plate drops out and only the marks land.
wear_code = ("float lum = dot(Scuff, float3(0.299, 0.587, 0.114));\n"
             "return saturate((1.0 - lum) * Strength * 2.0);")
wear_node = custom(wr, -450, 200, wear_code,
                   unreal.CustomMaterialOutputType.CMOT_FLOAT1,
                   ["Scuff", "Strength"], "dark marks only")
lib.connect_material_expressions(sample, "RGB", wear_node, "Scuff")
lib.connect_material_expressions(strength, "", wear_node, "Strength")
lib.connect_material_property(sample, "RGB",
                              unreal.MaterialProperty.MP_BASE_COLOR)
lib.connect_material_property(wear_node, "",
                              unreal.MaterialProperty.MP_OPACITY)
lib.connect_material_property(wr_rough, "",
                              unreal.MaterialProperty.MP_ROUGHNESS)
lib.recompile_material(wr)
assets.save_asset(wr.get_path_name())


# ------------------------------------------------------------ instances
def make_instance(name, parent, vectors=None, scalars=None):
    path = "%s/%s" % (ROOT, name)
    if assets.does_asset_exist(path):
        assets.delete_asset(path)
    mi = tools.create_asset(name, ROOT, unreal.MaterialInstanceConstant,
                            unreal.MaterialInstanceConstantFactoryNew())
    if mi is None:
        raise RuntimeError("FAIL CLOSED: could not create " + path)
    lib.set_material_instance_parent(mi, parent)
    for key, value in (vectors or {}).items():
        lib.set_material_instance_vector_parameter_value(mi, key, value)
    for key, value in (scalars or {}).items():
        lib.set_material_instance_scalar_parameter_value(mi, key, value)
    assets.save_asset(mi.get_path_name())
    return mi


make_instance("MI_LB_BayHazard_v001", haz,
              scalars={"BandCount": 8.0, "PaintOpacity": 0.9})
make_instance("MI_LB_BayWear_v001", wr,
              scalars={"WearStrength": 0.5})

# Prove the domain took - this is the exact check that was missing.
for name in ["M_LB_BayHazard_Decal_v001", "M_LB_BayWear_Decal_v001",
             "MI_LB_BayHazard_v001", "MI_LB_BayWear_v001"]:
    asset = unreal.load_asset("%s/%s" % (ROOT, name))
    base = asset
    if isinstance(asset, unreal.MaterialInstance):
        base = asset.get_editor_property("parent")
    domain = base.get_editor_property("material_domain")
    unreal.log("BAYPAINT %s domain=%s" % (name, domain))
    if domain != unreal.MaterialDomain.MD_DEFERRED_DECAL:
        raise RuntimeError("FAIL CLOSED: %s is not a decal material" % name)
unreal.log("BAYPAINT DONE")
