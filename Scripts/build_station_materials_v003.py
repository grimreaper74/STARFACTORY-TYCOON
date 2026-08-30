"""build_station_materials_v003.py - albedo lift. The Meshy textures
are darker than their preview images; rather than repaint (a palette
decision the owner has not made), the master material gains a
BaseColorBoost multiply (default 1.45) so all eleven models rise toward
the clean-industrial read in one reversible parameter.

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> -Unattended ... -ExecutePythonScript="<this>"
"""

import unreal

MAT_DIR = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials"
MASTER = MAT_DIR + "/M_LB_MeshyPBR_v002"

mel = unreal.MaterialEditingLibrary
lib = unreal.EditorAssetLibrary
master = unreal.load_asset(MASTER)
if master is None:
    raise RuntimeError("FAIL CLOSED: master material missing")

exprs = mel.get_material_expressions(master)
for expr in exprs:
    if isinstance(expr, unreal.MaterialExpressionScalarParameter) \
            and expr.get_editor_property("parameter_name") \
            == "BaseColorBoost":
        unreal.log("BOOST already wired - kept")
        raise SystemExit(0)

base = None
for expr in exprs:
    if isinstance(expr,
                  unreal.MaterialExpressionTextureSampleParameter2D) \
            and expr.get_editor_property("parameter_name") == "BaseColor":
        base = expr
        break
if base is None:
    raise RuntimeError("FAIL CLOSED: BaseColor sampler not found")

boost = mel.create_material_expression(
    master, unreal.MaterialExpressionScalarParameter, -420, -420)
boost.set_editor_property("parameter_name", "BaseColorBoost")
boost.set_editor_property("default_value", 1.45)
mul = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -260, -300)
mel.connect_material_expressions(base, "RGB", mul, "A")
mel.connect_material_expressions(boost, "", mul, "B")
mel.connect_material_property(mul, "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
mel.recompile_material(master)
lib.save_asset(MASTER)
unreal.log("ALBEDO LIFT DONE: BaseColorBoost 1.45 wired")
