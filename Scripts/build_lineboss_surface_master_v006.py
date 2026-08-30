"""The surface master, now able to paint TWO tones per mesh.

Owner 2026-08-28: "what's easiest way for you to paint the models ?"

The measured answer is why this exists. Of 73 imported meshes, 63 carry
exactly ONE material slot, so "paint a model" could only ever mean "give
the whole thing one flat colour" - which is why the drones and the booth
read as solid lumps while the bay, built from separate blocks, has
colour in it.

The master is WORLD-SPACE TRIPLANAR by design, because generated meshes
have whatever UVs the generator felt like. That is also exactly why it
cannot tell a panel from a rib: a triplanar projection knows where a
point is in the WORLD, never which PART of the model it belongs to.

So v005 adds the missing channel - a UV-mapped MASK selecting between
two tints:

  BaseTint ----\
                >--- lerp by mask ---> the paint
  AccentTint --/

with two mask sources, either or both:

  PanelMask   a UV-mapped texture, its luminance used as the selector.
              The obvious supply is MESHY'S OWN BASE COLOUR MAP - 46 are
              still in the project. Their COLOURS stay rejected (owner's
              standing direction: geometry from Meshy, materials ours),
              but the same map also records where every panel line,
              vent, recess and seam is, and that shape information was
              being thrown away along with the colour. As a mask it
              gives back the detail and none of the palette.
  HeightBlend an object-space vertical gradient, for meshes with no map
              at all: darker toward the feet, paler toward the top, the
              way real machinery is built and weathers.

EVERY NEW PARAMETER DEFAULTS TO INERT (MaskStrength 0, HeightBlend 0),
so this recompiles to exactly the v004 look until an instance opts in.
That is deliberate: the palette was retuned against the owner's "covered
in snow" note, and a new global default would silently undo it.

--- v004's reasoning, still true, below ---

The project's OWN surface material, authored in Unreal.

Owner 2026-08-28: "don't bother with meshy's textures, think better if
we do them in unreal." Meshy is a geometry source; the look is ours.

Why this is the better call, concretely:

  - ONE ART LANGUAGE IN ONE PLACE. Meshy bakes a different colour and
    lighting response into every asset, so a site dressed with its maps
    drifts even when every prompt asked for the same style. Eleven
    assets currently wear eleven unrelated map sets.
  - RETUNING IS GLOBAL. The settled look - pale panels, graphite
    framing, blue-white indicators, sparing warning orange - moves with
    a parameter instead of a regeneration.
  - IT IS FREE. Refinement costs credits per asset; a material costs
    nothing per asset and applies to all of them.
  - CHEAPER AT RUNTIME. Tiling detail beats a unique 1-2k map set per
    prop, in memory and in cook time.

The library's Metal Paint Chips set is VIRTUAL TEXTURE, which v001
missed: it wired ordinary Normal/LinearColor samplers and the master
would not compile - "Sampler type is Normal, should be Virtual Normal",
in the compiler's own words. Sampler types are picked to match here,
defensively, because the Python enum names for the virtual variants
differ between engine versions and a wrong guess fails the same way.

The master is WORLD-SPACE TRIPLANAR, deliberately: generated meshes
have whatever UVs the generator felt like, and a triplanar projection
does not care - the same material lands correctly on a fence panel, a
storage tank and a gantry crane without anyone unwrapping anything.

Surfaces come from the project's own library (owner's standing
direction to use what is already downloaded): the Metal Paint Chips
set under /Game/Surface_Forge.

Parameters, and what each is for:
  BaseTint        the panel colour - the pale/graphite decision
  DetailTiling    world centimetres per texture repeat
  Roughness/Metallic  the surface response
  WearAmount      how much of the paint-chip detail shows through
  EmissiveTint / EmissiveStrength  the blue-white indicator strips
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/surface_master_v006.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v007.")

MAT_DIR = "/Game/LineBoss/Materials/Surfaces"
MASTER = "%s/M_LB_Surface_Master" % MAT_DIR
SRC = "/Game/Surface_Forge/Textures/Metal_Paint_Chips"

library = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
failures = []


def sampler(*candidates):
    """First sampler enum that exists in this engine's bindings.

    The virtual-texture sampler names have moved between versions;
    naming one and hoping is how v001 failed."""
    for candidate in candidates:
        value = getattr(unreal.MaterialSamplerType, candidate, None)
        if value is not None:
            return value
    raise RuntimeError("no sampler type among %s" % (candidates,))


def is_virtual(texture):
    try:
        return bool(texture.get_editor_property("virtual_texture_streaming"))
    except Exception:  # noqa: BLE001
        return False

base_tex = library.load_asset("%s/T_Base_Color_Metal_Paint_Chips" % SRC)
normal_tex = library.load_asset("%s/T_Normal_Metal_Paint_Chips" % SRC)
ord_tex = library.load_asset("%s/T_ORD_Metal_Paint_Chips" % SRC)
for name, tex in (("base", base_tex), ("normal", normal_tex), ("ord", ord_tex)):
    if tex is None:
        failures.append("library texture missing: %s" % name)
if failures:
    raise RuntimeError("; ".join(failures))

if not library.does_asset_exist(MASTER):
    master = tools.create_asset("M_LB_Surface_Master", MAT_DIR,
                                unreal.Material, unreal.MaterialFactoryNew())
else:
    master = library.load_asset(MASTER)
mel.delete_all_material_expressions(master)

# ---- world-space triplanar UVs: position / tiling ----
pos = mel.create_material_expression(
    master, unreal.MaterialExpressionWorldPosition, -1400, 0)
tiling = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -1400, 200)
tiling.set_editor_property("parameter_name", "DetailTilingCm")
tiling.set_editor_property("default_value", 256.0)
uv_div = mel.create_material_expression(
    master, unreal.MaterialExpressionDivide, -1150, 60)
mel.connect_material_expressions(pos, "", uv_div, "A")
mel.connect_material_expressions(tiling, "", uv_div, "B")
# XY of the world position is enough for props standing on a floor;
# the vertical faces take the same grain, which reads as painted panel.
uv_mask = mel.create_material_expression(
    master, unreal.MaterialExpressionComponentMask, -950, 60)
uv_mask.set_editor_property("r", True)
uv_mask.set_editor_property("g", True)
uv_mask.set_editor_property("b", False)
uv_mask.set_editor_property("a", False)
mel.connect_material_expressions(uv_div, "", uv_mask, "")

detail = mel.create_material_expression(
    master, unreal.MaterialExpressionTextureSample, -700, -200)
detail.set_editor_property("texture", base_tex)
if is_virtual(base_tex):
    detail.set_editor_property("sampler_type", sampler(
        "SAMPLERTYPE_VIRTUAL_COLOR", "SAMPLERTYPE_VIRTUALCOLOR"))
mel.connect_material_expressions(uv_mask, "", detail, "UVs")

normal = mel.create_material_expression(
    master, unreal.MaterialExpressionTextureSample, -700, 400)
normal.set_editor_property("texture", normal_tex)
normal.set_editor_property("sampler_type", sampler(
    "SAMPLERTYPE_VIRTUAL_NORMAL", "SAMPLERTYPE_VIRTUALNORMAL")
    if is_virtual(normal_tex)
    else unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
mel.connect_material_expressions(uv_mask, "", normal, "UVs")
# NORMAL STRENGTH (owner 2026-08-28: "the building looks like its
# coverd in snow"). With WearAmount at 0 the base colour is a flat tint,
# so the paint-chip NORMAL is the only thing left with any variation in
# it - and on a near-white surface under a bright lamp it reads as
# crystalline crust. Snow, exactly as described.
#
# The normal had no knob at all: it went straight to the output at full
# strength. Lerping from a FLAT normal (0,0,1) toward the sampled one
# gives a dial from "smooth painted panel" to "full paint-chip relief".
flat_normal = mel.create_material_expression(
    master, unreal.MaterialExpressionConstant3Vector, -700, 560)
flat_normal.set_editor_property("constant",
                                unreal.LinearColor(0.0, 0.0, 1.0, 1.0))
normal_strength = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -700, 700)
normal_strength.set_editor_property("parameter_name", "NormalStrength")
normal_strength.set_editor_property("default_value", 0.25)
normal_mix = mel.create_material_expression(
    master, unreal.MaterialExpressionLinearInterpolate, -350, 480)
mel.connect_material_expressions(flat_normal, "", normal_mix, "A")
mel.connect_material_expressions(normal, "RGB", normal_mix, "B")
mel.connect_material_expressions(normal_strength, "", normal_mix, "Alpha")
mel.connect_material_property(normal_mix, "",
                              unreal.MaterialProperty.MP_NORMAL)

surface = mel.create_material_expression(
    master, unreal.MaterialExpressionTextureSample, -700, 900)
surface.set_editor_property("texture", ord_tex)
surface.set_editor_property("sampler_type", sampler(
    "SAMPLERTYPE_VIRTUAL_LINEAR_COLOR", "SAMPLERTYPE_VIRTUALLINEARCOLOR")
    if is_virtual(ord_tex)
    else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
mel.connect_material_expressions(uv_mask, "", surface, "UVs")

# ---- base colour: tint, with the paint-chip detail worn into it ----
tint = mel.create_material_expression(
    master, unreal.MaterialExpressionVectorParameter, -700, -520)
tint.set_editor_property("parameter_name", "BaseTint")
tint.set_editor_property("default_value",
                         unreal.LinearColor(0.82, 0.84, 0.87, 1.0))
wear = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -700, -380)
wear.set_editor_property("parameter_name", "WearAmount")
wear.set_editor_property("default_value", 0.35)
# The TINT always dominates and the detail only modulates its
# brightness. Lerping straight to the map (v002) meant that if the
# map ever resolved dark - a virtual texture not yet streamed, a
# missing asset - the surface went dark with it. A material should
# degrade to "flat painted panel", never to black.
detail_gain = mel.create_material_expression(
    master, unreal.MaterialExpressionLinearInterpolate, -500, -300)
one = mel.create_material_expression(
    master, unreal.MaterialExpressionConstant, -700, -300)
one.set_editor_property("r", 1.0)
bright = mel.create_material_expression(
    master, unreal.MaterialExpressionAdd, -560, -180)
half = mel.create_material_expression(
    master, unreal.MaterialExpressionConstant, -700, -140)
half.set_editor_property("r", 0.55)
scaled_detail = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -680, -230)
gain = mel.create_material_expression(
    master, unreal.MaterialExpressionConstant, -820, -215)
gain.set_editor_property("r", 0.9)
mel.connect_material_expressions(detail, "R", scaled_detail, "A")
mel.connect_material_expressions(gain, "", scaled_detail, "B")
mel.connect_material_expressions(scaled_detail, "", bright, "A")
mel.connect_material_expressions(half, "", bright, "B")
mel.connect_material_expressions(one, "", detail_gain, "A")
mel.connect_material_expressions(bright, "", detail_gain, "B")
mel.connect_material_expressions(wear, "", detail_gain, "Alpha")
# ---- THE MASK: what lets one material paint two tones ----
accent = mel.create_material_expression(
    master, unreal.MaterialExpressionVectorParameter, -1400, -900)
accent.set_editor_property("parameter_name", "AccentTint")
accent.set_editor_property("default_value",
                          unreal.LinearColor(0.26, 0.25, 0.24, 1.0))
# The mask needs a true midpoint. v004's `half` is 0.55 - a detail-gain
# constant that only looks like one - and borrowing it would bias every
# mask 5% toward the accent for no stated reason.
mid = mel.create_material_expression(
    master, unreal.MaterialExpressionConstant, -1400, -1480)
mid.set_editor_property("r", 0.5)


def clamp01(expression, x, y):
    """Clamp rather than Saturate, deliberately: Saturate is not exposed
    under a stable Python name across engine versions, and a wrong guess
    fails the same silent way the v001 samplers did."""
    node = mel.create_material_expression(
        master, unreal.MaterialExpressionClamp, x, y)
    node.set_editor_property("min_default", 0.0)
    node.set_editor_property("max_default", 1.0)
    mel.connect_material_expressions(expression, "", node, "")
    return node


# -- source A: a UV-mapped texture's luminance (Meshy's map, as a mask) --
# NOTE THE UVs: this samples the MESH'S OWN UV0, not the triplanar
# projection above. That is the whole point - a mask has to live in the
# model's own space to know anything about the model.
panel_mask = mel.create_material_expression(
    master, unreal.MaterialExpressionTextureSampleParameter2D, -1400, -1150)
panel_mask.set_editor_property("parameter_name", "PanelMask")
white = library.load_asset("/Engine/EngineResources/WhiteSquareTexture")
if white is not None:
    panel_mask.set_editor_property("texture", white)
else:
    failures.append("engine white texture missing - PanelMask has no default")
luminance = mel.create_material_expression(
    master, unreal.MaterialExpressionDesaturation, -1120, -1150)
mel.connect_material_expressions(panel_mask, "RGB", luminance, "")
mask_contrast = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -1400, -1060)
mask_contrast.set_editor_property("parameter_name", "MaskContrast")
mask_contrast.set_editor_property("default_value", 2.5)
mask_pivot = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -1400, -1000)
mask_pivot.set_editor_property("parameter_name", "MaskPivot")
mask_pivot.set_editor_property("default_value", 0.5)
mask_strength = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -1400, -940)
mask_strength.set_editor_property("parameter_name", "MaskStrength")
mask_strength.set_editor_property("default_value", 0.0)
# (luminance - pivot) * contrast + 0.5, clamped: a pivot-and-gain that
# turns a soft photographic map into a decisive two-tone selector.
centred = mel.create_material_expression(
    master, unreal.MaterialExpressionSubtract, -980, -1150)
mel.connect_material_expressions(luminance, "", centred, "A")
mel.connect_material_expressions(mask_pivot, "", centred, "B")
gained = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -890, -1150)
mel.connect_material_expressions(centred, "", gained, "A")
mel.connect_material_expressions(mask_contrast, "", gained, "B")
recentred = mel.create_material_expression(
    master, unreal.MaterialExpressionAdd, -800, -1150)
mel.connect_material_expressions(gained, "", recentred, "A")
mel.connect_material_expressions(mid, "", recentred, "B")
tex_term = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -600, -1150)
mel.connect_material_expressions(clamp01(recentred, -700, -1150), "",
                                 tex_term, "A")
mel.connect_material_expressions(mask_strength, "", tex_term, "B")

# -- source B: an object-space vertical gradient, for meshes with no map --
# World Z minus the object's own centre Z, over its radius. Yaw does not
# affect Z and every prop in this factory stands upright, so this is
# stable without a local-position node that may not be bound.
object_pos = mel.create_material_expression(
    master, unreal.MaterialExpressionObjectPositionWS, -1400, -1400)
object_radius = mel.create_material_expression(
    master, unreal.MaterialExpressionObjectRadius, -1400, -1300)
height_delta = mel.create_material_expression(
    master, unreal.MaterialExpressionSubtract, -1180, -1420)
mel.connect_material_expressions(pos, "", height_delta, "A")
mel.connect_material_expressions(object_pos, "", height_delta, "B")
height_z = mel.create_material_expression(
    master, unreal.MaterialExpressionComponentMask, -1060, -1420)
height_z.set_editor_property("r", False)
height_z.set_editor_property("g", False)
height_z.set_editor_property("b", True)
height_z.set_editor_property("a", False)
mel.connect_material_expressions(height_delta, "", height_z, "")
height_norm = mel.create_material_expression(
    master, unreal.MaterialExpressionDivide, -980, -1420)
mel.connect_material_expressions(height_z, "", height_norm, "A")
mel.connect_material_expressions(object_radius, "", height_norm, "B")
height_scaled = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -890, -1420)
mel.connect_material_expressions(height_norm, "", height_scaled, "A")
mel.connect_material_expressions(mid, "", height_scaled, "B")
# HEIGHT CONTRAST. The term above is normalised by the object's
# BOUNDING SPHERE RADIUS, which on a wide flat mesh is dominated by its
# LENGTH - so the vertical range collapses. Measured on the ground
# drones (320 x 202 x 84 cm and similar), the mask only spanned
# 0.39..0.61 of its 0..1 range, i.e. a gradient confined to the middle
# fifth, which is indistinguishable from no gradient at all.
#
# The gain is applied HERE, while the term is still centred on zero and
# before the 0.5 bias, so it stretches symmetrically about the object's
# middle instead of sliding the whole gradient upward.
height_contrast = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -1400, -1160)
height_contrast.set_editor_property("parameter_name", "HeightContrast")
# 1.0 keeps v005's behaviour exactly; an instance that wants a readable
# top-to-bottom grade on a squat mesh asks for 4 or so.
height_contrast.set_editor_property("default_value", 1.0)
height_gained = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -845, -1420)
mel.connect_material_expressions(height_scaled, "", height_gained, "A")
mel.connect_material_expressions(height_contrast, "", height_gained, "B")
height_biased = mel.create_material_expression(
    master, unreal.MaterialExpressionAdd, -800, -1420)
mel.connect_material_expressions(height_gained, "", height_biased, "A")
mel.connect_material_expressions(mid, "", height_biased, "B")
height_blend = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -1400, -1220)
height_blend.set_editor_property("parameter_name", "HeightBlend")
height_blend.set_editor_property("default_value", 0.0)
height_term = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -600, -1420)
mel.connect_material_expressions(clamp01(height_biased, -700, -1420), "",
                                 height_term, "A")
mel.connect_material_expressions(height_blend, "", height_term, "B")

combined = mel.create_material_expression(
    master, unreal.MaterialExpressionAdd, -520, -1280)
mel.connect_material_expressions(tex_term, "", combined, "A")
mel.connect_material_expressions(height_term, "", combined, "B")
painted = mel.create_material_expression(
    master, unreal.MaterialExpressionLinearInterpolate, -430, -600)
mel.connect_material_expressions(tint, "", painted, "A")
mel.connect_material_expressions(accent, "", painted, "B")
mel.connect_material_expressions(clamp01(combined, -470, -1280), "",
                                 painted, "Alpha")

worn = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -350, -400)
mel.connect_material_expressions(painted, "", worn, "A")
mel.connect_material_expressions(detail_gain, "", worn, "B")
mel.connect_material_property(worn, "",
                              unreal.MaterialProperty.MP_BASE_COLOR)

# ---- roughness and metallic: parameters, modulated by the ORD map ----
rough_param = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -700, 620)
rough_param.set_editor_property("parameter_name", "Roughness")
rough_param.set_editor_property("default_value", 0.45)
# ROUGHNESS IS THE PARAMETER, full stop. v002 multiplied it by the
# ORD map's green channel; when that resolved to zero the surface
# became a perfect mirror, and a mirror in a scene with no reflection
# captures renders BLACK - which is exactly how the props came out.
# The same mistake, in a new place, as the metallic that made the
# buildings look like a mess.
mel.connect_material_property(rough_param, "",
                              unreal.MaterialProperty.MP_ROUGHNESS)

metal_param = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -700, 780)
metal_param.set_editor_property("parameter_name", "Metallic")
# Deliberately LOW by default: painted panel, not bare steel. High
# metal in a scene with no reflection captures renders near-black, and
# that is exactly the fault that made the buildings look like a mess.
metal_param.set_editor_property("default_value", 0.12)
mel.connect_material_property(metal_param, "",
                              unreal.MaterialProperty.MP_METALLIC)

# ---- emissive trim: off by default, for indicator strips ----
emissive_tint = mel.create_material_expression(
    master, unreal.MaterialExpressionVectorParameter, -700, 1050)
emissive_tint.set_editor_property("parameter_name", "EmissiveTint")
emissive_tint.set_editor_property(
    "default_value", unreal.LinearColor(0.45, 0.72, 1.0, 1.0))
emissive_strength = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -700, 1200)
emissive_strength.set_editor_property("parameter_name", "EmissiveStrength")
emissive_strength.set_editor_property("default_value", 0.0)
emissive_mul = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -350, 1100)
mel.connect_material_expressions(emissive_tint, "", emissive_mul, "A")
mel.connect_material_expressions(emissive_strength, "", emissive_mul, "B")
mel.connect_material_property(emissive_mul, "",
                              unreal.MaterialProperty.MP_EMISSIVE_COLOR)

mel.recompile_material(master)
library.save_loaded_asset(master, only_if_is_dirty=False)
# The compile is the deliverable: a master that silently falls back to
# the default material is exactly the fault this project has already
# shipped once.
print("SURFACEMASTER virtual base=%s normal=%s ord=%s"
      % (is_virtual(base_tex), is_virtual(normal_tex), is_virtual(ord_tex)))

# ---- the palette: three instances, the settled language ----
# RETUNED after the owner saw it: "the building looks like its coverd in
# snow". Three faults stacked - albedo 0.88 is near-white, the lamps had
# been tripled to 9k lm, and the normal was at full strength with no
# colour variation to compete with it. All three come down.
#
# 0.72 is the top of what a lit surface should sit at; anything higher
# has nowhere to go under a bright light except white.
INSTANCES = {
    "MI_LB_Surface_PalePanel": {
        "tint": unreal.LinearColor(0.72, 0.70, 0.66, 1.0),
        "wear": 0.0, "rough": 0.58, "metal": 0.02, "tiling": 300.0,
        "normal": 0.22},
    # The TWO-TONE variants: same master, same tints, mask switched on.
    # These are what a mesh gets when it should read as panelled
    # machinery rather than a single moulded lump.
    "MI_LB_Surface_PalePanel_TwoTone": {
        "tint": unreal.LinearColor(0.74, 0.73, 0.70, 1.0),
        "accent": unreal.LinearColor(0.24, 0.24, 0.25, 1.0),
        "wear": 0.0, "rough": 0.55, "metal": 0.03, "tiling": 300.0,
        "normal": 0.22, "MaskStrength": 1.0, "MaskPivot": 0.45,
        "MaskContrast": 3.0},
    "MI_LB_Surface_MachineAmber_TwoTone": {
        "tint": unreal.LinearColor(0.86, 0.47, 0.10, 1.0),
        "accent": unreal.LinearColor(0.22, 0.22, 0.23, 1.0),
        "wear": 0.0, "rough": 0.52, "metal": 0.04, "tiling": 240.0,
        "normal": 0.26, "MaskStrength": 1.0, "MaskPivot": 0.45,
        "MaskContrast": 3.0},
    # No map required: the vertical gradient alone. This is the fallback
    # for the meshes Meshy left no base-colour map for.
    # BaseTint is the BOTTOM and AccentTint is the TOP - the mask runs
    # 0 at the object's underside to 1 at its crown. v005 had these the
    # wrong way round, which would have put the dark tone on the ROOF of
    # every machine and the pale tone on its wheels. Real machinery is
    # the other way about: a dark chassis and running gear under a pale
    # body, which is also what both reference games show.
    "MI_LB_Surface_PalePanel_Graded": {
        "tint": unreal.LinearColor(0.26, 0.26, 0.27, 1.0),
        "accent": unreal.LinearColor(0.80, 0.79, 0.76, 1.0),
        "wear": 0.0, "rough": 0.56, "metal": 0.03, "tiling": 300.0,
        "normal": 0.22, "HeightBlend": 1.0, "HeightContrast": 4.0},
    "MI_LB_Surface_Graphite": {
        "tint": unreal.LinearColor(0.26, 0.25, 0.24, 1.0),
        "wear": 0.0, "rough": 0.62, "metal": 0.04, "tiling": 260.0,
        "normal": 0.30},
    "MI_LB_Surface_WarningOrange": {
        "tint": unreal.LinearColor(0.90, 0.66, 0.05, 1.0),
        "wear": 0.0, "rough": 0.55, "metal": 0.02, "tiling": 200.0,
        "normal": 0.20},
    "MI_LB_Surface_MachineAmber": {
        "tint": unreal.LinearColor(0.74, 0.40, 0.11, 1.0),
        "wear": 0.0, "rough": 0.55, "metal": 0.03, "tiling": 240.0,
        "normal": 0.28},
}
made = []
for name, values in INSTANCES.items():
    path = "%s/%s" % (MAT_DIR, name)
    if library.does_asset_exist(path):
        instance = library.load_asset(path)
    else:
        instance = tools.create_asset(
            name, MAT_DIR, unreal.MaterialInstanceConstant,
            unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(instance, master)
    mel.set_material_instance_vector_parameter_value(
        instance, "BaseTint", values["tint"])
    mel.set_material_instance_scalar_parameter_value(
        instance, "WearAmount", values["wear"])
    mel.set_material_instance_scalar_parameter_value(
        instance, "Roughness", values["rough"])
    mel.set_material_instance_scalar_parameter_value(
        instance, "Metallic", values["metal"])
    mel.set_material_instance_scalar_parameter_value(
        instance, "DetailTilingCm", values["tiling"])
    mel.set_material_instance_scalar_parameter_value(
        instance, "NormalStrength", values["normal"])
    # OPT-IN ONLY. An instance that names no accent keeps the flat v004
    # look exactly, which is why this recompile cannot regress the
    # palette the owner already signed off on.
    if "accent" in values:
        mel.set_material_instance_vector_parameter_value(
            instance, "AccentTint", values["accent"])
    for knob in ("MaskStrength", "MaskPivot", "MaskContrast", "HeightBlend",
                 "HeightContrast"):
        if knob in values:
            mel.set_material_instance_scalar_parameter_value(
                instance, knob, values[knob])
    library.save_loaded_asset(instance, only_if_is_dirty=False)
    reloaded = library.load_asset(path)
    parent = reloaded.get_editor_property("parent")
    ok = parent is not None and parent.get_name() == "M_LB_Surface_Master"
    if not ok:
        failures.append("%s did not keep the master as its parent" % name)
    made.append({"instance": path, "parented": ok})

report = {
    "$schema": "lineboss/audit/surface-master-v006/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": ("PASS__SURFACE_MASTER_AND_PALETTE_BUILT" if not failures
               else "FAIL_CLOSED__SURFACE_MASTER"),
    "why": ("Owner 2026-08-28: materials are authored in Unreal, not "
            "taken from Meshy. One master, one palette, tuned in one "
            "place."),
    "master": MASTER,
    "source_textures": SRC,
    "instances": made,
    "failures": failures,
    "not_proven": [
        "Nobody has looked at it on a mesh yet. The tint and wear "
        "values are a starting point for the owner to move, not a "
        "decision - the factory base tone is COLD STEEL by their "
        "choice and these numbers are aimed at it, not agreed.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "instances": len(made),
                  "failures": failures}, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
