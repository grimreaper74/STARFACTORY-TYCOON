"""The project's OWN surface material, authored in Unreal.

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
out = root / "Saved/Audits/Spacecraft/surface_master_v002.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v003.")

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
mel.connect_material_property(normal, "RGB",
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
worn = mel.create_material_expression(
    master, unreal.MaterialExpressionLinearInterpolate, -350, -400)
mel.connect_material_expressions(tint, "", worn, "A")
mel.connect_material_expressions(detail, "RGB", worn, "B")
mel.connect_material_expressions(wear, "", worn, "Alpha")
mel.connect_material_property(worn, "",
                              unreal.MaterialProperty.MP_BASE_COLOR)

# ---- roughness and metallic: parameters, modulated by the ORD map ----
rough_param = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -700, 620)
rough_param.set_editor_property("parameter_name", "Roughness")
rough_param.set_editor_property("default_value", 0.45)
rough_mul = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -350, 640)
mel.connect_material_expressions(surface, "G", rough_mul, "A")
mel.connect_material_expressions(rough_param, "", rough_mul, "B")
mel.connect_material_property(rough_mul, "",
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
INSTANCES = {
    "MI_LB_Surface_PalePanel": {
        "tint": unreal.LinearColor(0.84, 0.86, 0.89, 1.0),
        "wear": 0.30, "rough": 0.45, "metal": 0.10, "tiling": 256.0},
    "MI_LB_Surface_Graphite": {
        "tint": unreal.LinearColor(0.20, 0.21, 0.23, 1.0),
        "wear": 0.45, "rough": 0.55, "metal": 0.25, "tiling": 220.0},
    "MI_LB_Surface_WarningOrange": {
        "tint": unreal.LinearColor(0.85, 0.42, 0.10, 1.0),
        "wear": 0.40, "rough": 0.50, "metal": 0.08, "tiling": 180.0},
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
    library.save_loaded_asset(instance, only_if_is_dirty=False)
    reloaded = library.load_asset(path)
    parent = reloaded.get_editor_property("parent")
    ok = parent is not None and parent.get_name() == "M_LB_Surface_Master"
    if not ok:
        failures.append("%s did not keep the master as its parent" % name)
    made.append({"instance": path, "parented": ok})

report = {
    "$schema": "lineboss/audit/surface-master-v002/v1",
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
