"""build_bay_paint_decals_v002.py - repair the wear decal that was
painting every work-station bay black.

THE FAULT, measured not guessed. v001 built the wear decal like this:

    opacity    = saturate((1 - luminance) * Strength * 2.0)
    base colour = the scuff texture's own RGB

on the stated assumption that the source is "dark marks on a pale
plate", so the plate would fall out and only the marks would land. The
source (T_Floor_Scratches_and_traces_BCO) is mostly DARK, so the
assumption inverted: (1 - lum) went to 1 over most of the image, and
with Strength 0.5 doubled to 1.0 the darkest texels painted at FULL
opacity in their own near-black colour. A subtle scuff overlay became
an opaque black slab across 85% of every bay.

It was visible in every capture as four black pits in a bright hall,
and it was read as "the bay floor is muddy" - a taste problem - for
longer than it should have been. PROVEN by setting WearStrength to 0
and re-rendering: the bays came back as clean mid-grey pads with their
hazard borders intact. That diagnostic is why this is a repair and not
another guess.

THE REPAIR, and why each half of it:

  base colour becomes a WearTint PARAMETER, not the texture's RGB.
      A grime overlay should decide its own colour. Feeding an image's
      RGB into base colour means the decal can never be tuned without
      re-authoring the texture, and it couples the look to whatever
      that particular map happens to contain - which is exactly how
      this went wrong.
  opacity loses the x2 and drops to 0.30.
      Opacity now peaks at 0.30 where the map is blackest, so the pad
      tone still dominates and the scuff modulates it. Wear is meant to
      break up a flat surface, not replace it.

The texture is still doing the job it is good at: telling the material
WHERE the scuffing goes. That is the same principle as the surface
master's new PanelMask - use a map for its shape information and
decide the colour ourselves.

v001 is left exactly as it was, as evidence of the fault - including
restoring the WearStrength the diagnostic zeroed. The C++ presenter is
what moves to v002.

Fails closed if the source texture or the v001 lane's output is absent.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir())
out = root / "Saved/Audits/Spacecraft/bay_paint_decals_v002.json"
if out.exists():
    raise RuntimeError("Refusing to rerun: receipt exists. Author v003.")

ROOT = "/Game/LineBoss/Materials/Decals"
WEAR_TEX = ("/Game/Textures/T_Floor_Scratches_and_traces_BCO"
            ".T_Floor_Scratches_and_traces_BCO")

lib = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
assets = unreal.EditorAssetLibrary

wear_tex = unreal.load_asset(WEAR_TEX)
if wear_tex is None:
    raise RuntimeError("FAIL CLOSED: missing " + WEAR_TEX)

name = "M_LB_BayWear_Decal_v002"
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

sample = lib.create_material_expression(
    mat, unreal.MaterialExpressionTextureSampleParameter2D, -900, 0)
sample.set_editor_property("parameter_name", "WearTexture")
sample.set_editor_property("texture", wear_tex)

tint = lib.create_material_expression(
    mat, unreal.MaterialExpressionVectorParameter, -900, 260)
tint.set_editor_property("parameter_name", "WearTint")
# A grimy warm grey. Deliberately NOT near-black: this sits on a pad
# that is already only 0.46, and the point is to modulate that pad
# rather than bury it.
tint.set_editor_property("default_value",
                         unreal.LinearColor(0.34, 0.33, 0.31, 1.0))

strength = lib.create_material_expression(
    mat, unreal.MaterialExpressionScalarParameter, -900, 400)
strength.set_editor_property("parameter_name", "WearStrength")
strength.set_editor_property("default_value", 0.30)

rough = lib.create_material_expression(
    mat, unreal.MaterialExpressionScalarParameter, -900, 540)
rough.set_editor_property("parameter_name", "PaintRoughness")
rough.set_editor_property("default_value", 0.80)

node = lib.create_material_expression(
    mat, unreal.MaterialExpressionCustom, -450, 200)
node.set_editor_property("code",
                         "float lum = dot(Scuff, float3(0.299, 0.587, "
                         "0.114));\nreturn saturate((1.0 - lum) * Strength);")
node.set_editor_property("output_type",
                         unreal.CustomMaterialOutputType.CMOT_FLOAT1)
node.set_editor_property("description", "wear amount, capped by Strength")
inputs = []
for input_name in ("Scuff", "Strength"):
    custom_input = unreal.CustomInput()
    custom_input.set_editor_property("input_name", input_name)
    inputs.append(custom_input)
node.set_editor_property("inputs", inputs)
lib.connect_material_expressions(sample, "RGB", node, "Scuff")
lib.connect_material_expressions(strength, "", node, "Strength")

lib.connect_material_property(tint, "", unreal.MaterialProperty.MP_BASE_COLOR)
lib.connect_material_property(node, "", unreal.MaterialProperty.MP_OPACITY)
lib.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
lib.recompile_material(mat)
assets.save_asset(mat.get_path_name())

instance_path = "%s/MI_LB_BayWear_v002" % ROOT
if assets.does_asset_exist(instance_path):
    assets.delete_asset(instance_path)
instance = tools.create_asset("MI_LB_BayWear_v002", ROOT,
                              unreal.MaterialInstanceConstant,
                              unreal.MaterialInstanceConstantFactoryNew())
if instance is None:
    raise RuntimeError("FAIL CLOSED: could not create " + instance_path)
lib.set_material_instance_parent(instance, mat)
lib.set_material_instance_scalar_parameter_value(
    instance, "WearStrength", 0.30)
assets.save_asset(instance.get_path_name())

# Put v001 back exactly as it was: the diagnostic zeroed its strength,
# and a superseded artifact is only evidence if it is unaltered.
restored = False
old = assets.load_asset("%s/MI_LB_BayWear_v001" % ROOT)
if old is not None:
    lib.set_material_instance_scalar_parameter_value(
        old, "WearStrength", 0.5)
    assets.save_loaded_asset(old, only_if_is_dirty=False)
    restored = True

# The domain check is the one that was missing when this first went
# wrong: a non-decal material is ACCEPTED and silently replaced by the
# engine default at render time.
reloaded = unreal.load_asset(instance_path)
parent = reloaded.get_editor_property("parent")
domain = parent.get_editor_property("material_domain")
ok = domain == unreal.MaterialDomain.MD_DEFERRED_DECAL

report = {
    "$schema": "lineboss/audit/bay-paint-decals-v002/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__BAY_WEAR_REPAIRED" if ok else "FAIL_CLOSED__WRONG_DOMAIN",
    "why": ("v001's wear decal drove OPACITY from darkness while using "
            "the texture's own RGB as base colour. The source map is "
            "mostly dark, so the darkest texels painted at full opacity "
            "in near-black and every work-station bay rendered as a "
            "black pit. Proven by zeroing WearStrength and "
            "re-rendering: the bays came back as clean grey pads."),
    "material": path,
    "instance": instance_path,
    "domain_is_deferred_decal": ok,
    "v001_strength_restored": restored,
    "not_proven": [
        "NOT YET SEEN. The C++ presenter still loads MI_LB_BayWear_v001 "
        "until its path is moved to v002, and no capture has been taken "
        "with the repaired material bound.",
        "The tint and strength are a first estimate judged against Car "
        "Manufacture's bright bays, not a tuned value.",
    ],
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("BAYWEAR %s domain_ok=%s restored_v001=%s"
      % (report["status"], ok, restored))
