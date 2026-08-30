"""build_station_materials_v004.py - COLD STEEL grade (owner picked
variant B, 2026-08-25). Upgrades the master material's plain scalar
boost into the chosen grade: BaseColor * tint(0.94, 0.99, 1.08) * 1.5.
One shared change; every station and drone instance inherits it.

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> -Unattended ... -ExecutePythonScript="<this>"
"""

import unreal

MASTER = ("/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001"
          "/Materials/M_LB_MeshyPBR_v002")

mel = unreal.MaterialEditingLibrary
lib = unreal.EditorAssetLibrary
master = unreal.load_asset(MASTER)
if master is None:
    raise RuntimeError("FAIL CLOSED: master material missing")

boost = None
for expr in mel.get_material_expressions(master):
    if isinstance(expr, unreal.MaterialExpressionScalarParameter) \
            and expr.get_editor_property("parameter_name") \
            == "BaseColorBoost":
        boost = expr
        break
if boost is None:
    raise RuntimeError("FAIL CLOSED: BaseColorBoost missing - run v003")

# Cold Steel: the boost keeps the lift; a tint vector joins the chain.
boost.set_editor_property("default_value", 1.5)
for expr in mel.get_material_expressions(master):
    if isinstance(expr, unreal.MaterialExpressionVectorParameter) \
            and expr.get_editor_property("parameter_name") == "SteelTint":
        unreal.log("COLD STEEL already wired - kept")
        raise SystemExit(0)

# Find the multiply that BaseColorBoost feeds and retarget through the
# tint: (BaseColor * Boost) * Tint -> BaseColor property.
mul_old = None
for expr in mel.get_material_expressions(master):
    if isinstance(expr, unreal.MaterialExpressionMultiply):
        mul_old = expr
if mul_old is None:
    raise RuntimeError("FAIL CLOSED: boost multiply missing")

tint = mel.create_material_expression(
    master, unreal.MaterialExpressionVectorParameter, -140, -420)
tint.set_editor_property("parameter_name", "SteelTint")
tint.set_editor_property("default_value",
                         unreal.LinearColor(0.94, 0.99, 1.08, 1.0))
mul2 = mel.create_material_expression(
    master, unreal.MaterialExpressionMultiply, -60, -300)
mel.connect_material_expressions(mul_old, "", mul2, "A")
mel.connect_material_expressions(tint, "", mul2, "B")
mel.connect_material_property(mul2, "",
                              unreal.MaterialProperty.MP_BASE_COLOR)
mel.recompile_material(master)
lib.save_asset(MASTER)
unreal.log("COLD STEEL GRADE DONE: tint wired over the boost")
