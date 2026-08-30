"""build_station_materials_v005.py - polish pass (owner heading to bed:
"polish so colors are correct"). Two changes:
1. BaseColorBoost 1.5 -> 1.8: the owner's play session showed machines
   still reading near-silhouette against the pale floor; the Meshy
   albedo is genuinely dark and the Cold Steel tint carries the hue.
2. M_LB_Flame_v001: a soft additive flame material (radial falloff from
   UV centre, emissive colour parameter) so the RCS/main cones stop
   reading as flat solid wedges at cinematic distance.

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> -Unattended ... -ExecutePythonScript="<this>"
"""

import unreal

MAT_DIR = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials"
MASTER = MAT_DIR + "/M_LB_MeshyPBR_v002"
FLAME = MAT_DIR + "/M_LB_Flame_v001"

mel = unreal.MaterialEditingLibrary
lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()

master = unreal.load_asset(MASTER)
if master is None:
    raise RuntimeError("FAIL CLOSED: master material missing")
boosted = False
for expr in mel.get_material_expressions(master):
    if isinstance(expr, unreal.MaterialExpressionScalarParameter) \
            and expr.get_editor_property("parameter_name") \
            == "BaseColorBoost":
        expr.set_editor_property("default_value", 1.8)
        boosted = True
if not boosted:
    raise RuntimeError("FAIL CLOSED: BaseColorBoost missing")
mel.recompile_material(master)
lib.save_asset(MASTER)
unreal.log("BOOST raised to 1.8")

if lib.does_asset_exist(FLAME):
    unreal.log("FLAME material already exists - kept")
else:
    mat = tools.create_asset("M_LB_Flame_v001", MAT_DIR, unreal.Material,
                             unreal.MaterialFactoryNew())
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property(
        "shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    colour = mel.create_material_expression(
        mat, unreal.MaterialExpressionVectorParameter, -600, -150)
    colour.set_editor_property("parameter_name", "Color")
    colour.set_editor_property("default_value",
                               unreal.LinearColor(0.45, 0.7, 1.0, 1.0))
    strength = mel.create_material_expression(
        mat, unreal.MaterialExpressionScalarParameter, -600, 60)
    strength.set_editor_property("parameter_name", "Strength")
    strength.set_editor_property("default_value", 6.0)
    # Radial falloff: distance from UV centre -> soft edge.
    uv = mel.create_material_expression(
        mat, unreal.MaterialExpressionTextureCoordinate, -1000, 220)
    centre = mel.create_material_expression(
        mat, unreal.MaterialExpressionConstant2Vector, -1000, 340)
    centre.set_editor_property("r", 0.5)
    centre.set_editor_property("g", 0.5)
    dist = mel.create_material_expression(
        mat, unreal.MaterialExpressionDistance, -840, 260)
    mel.connect_material_expressions(uv, "", dist, "A")
    mel.connect_material_expressions(centre, "", dist, "B")
    scale = mel.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -700, 260)
    two = mel.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -840, 400)
    two.set_editor_property("r", 2.0)
    mel.connect_material_expressions(dist, "", scale, "A")
    mel.connect_material_expressions(two, "", scale, "B")
    inv = mel.create_material_expression(
        mat, unreal.MaterialExpressionOneMinus, -560, 260)
    mel.connect_material_expressions(scale, "", inv, "")
    soft = mel.create_material_expression(
        mat, unreal.MaterialExpressionSaturate, -440, 260)
    mel.connect_material_expressions(inv, "", soft, "")
    glow = mel.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -300, 0)
    mel.connect_material_expressions(colour, "", glow, "A")
    mel.connect_material_expressions(strength, "", glow, "B")
    final = mel.create_material_expression(
        mat, unreal.MaterialExpressionMultiply, -160, 80)
    mel.connect_material_expressions(glow, "", final, "A")
    mel.connect_material_expressions(soft, "", final, "B")
    mel.connect_material_property(final, "",
                                  unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    lib.save_asset(FLAME)
    unreal.log("FLAME material created")
unreal.log("POLISH MATERIALS v005 DONE")
