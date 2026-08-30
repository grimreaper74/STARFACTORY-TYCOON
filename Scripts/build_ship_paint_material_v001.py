"""build_ship_paint_material_v001.py - the live-painting material
(owner 2026-08-25: "make it look like they're actually painting it
live"). One material with a world-space paint front: surfaces behind
PaintFrontX wear the finish colour, surfaces ahead of it are still
primer, with a 50 cm soft edge. The presenter slides PaintFrontX with
the REAL Assembly-stage progress, so the ship is exactly as painted as
the stage is complete.

Run headless (editor closed):
  UnrealEditor-Cmd.exe <proj> -Unattended ... -ExecutePythonScript="<this>"
"""

import unreal

MAT_DIR = "/Game/LineBoss/Candidates/Spacecraft/StationMeshes_v001/Materials"
NAME = "M_LB_ShipPaint_v001"

lib = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
if lib.does_asset_exist("%s/%s" % (MAT_DIR, NAME)):
    unreal.log("PAINT MATERIAL already exists - kept")
else:
    mat = tools.create_asset(NAME, MAT_DIR, unreal.Material,
                             unreal.MaterialFactoryNew())
    wp = mel.create_material_expression(
        mat, unreal.MaterialExpressionWorldPosition, -1100, 0)
    wx = mel.create_material_expression(
        mat, unreal.MaterialExpressionComponentMask, -950, 0)
    wx.set_editor_property("r", True)
    wx.set_editor_property("g", False)
    wx.set_editor_property("b", False)
    mel.connect_material_expressions(wp, "", wx, "")
    front = mel.create_material_expression(
        mat, unreal.MaterialExpressionScalarParameter, -950, 140)
    front.set_editor_property("parameter_name", "PaintFrontX")
    front.set_editor_property("default_value", -1000000.0)
    diff = mel.create_material_expression(
        mat, unreal.MaterialExpressionSubtract, -800, 40)
    mel.connect_material_expressions(wx, "", diff, "A")
    mel.connect_material_expressions(front, "", diff, "B")
    soft = mel.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -800, 180)
    soft.set_editor_property("r", 50.0)
    div = mel.create_material_expression(
        mat, unreal.MaterialExpressionDivide, -650, 60)
    mel.connect_material_expressions(diff, "", div, "A")
    mel.connect_material_expressions(soft, "", div, "B")
    sat = mel.create_material_expression(
        mat, unreal.MaterialExpressionSaturate, -520, 60)
    mel.connect_material_expressions(div, "", sat, "")
    paint = mel.create_material_expression(
        mat, unreal.MaterialExpressionVectorParameter, -520, -160)
    paint.set_editor_property("parameter_name", "PaintColor")
    paint.set_editor_property("default_value",
                              unreal.LinearColor(0.75, 0.78, 0.82, 1.0))
    primer = mel.create_material_expression(
        mat, unreal.MaterialExpressionVectorParameter, -520, 220)
    primer.set_editor_property("parameter_name", "PrimerColor")
    primer.set_editor_property("default_value",
                               unreal.LinearColor(0.34, 0.32, 0.30, 1.0))
    lerp = mel.create_material_expression(
        mat, unreal.MaterialExpressionLinearInterpolate, -300, 0)
    mel.connect_material_expressions(paint, "", lerp, "A")
    mel.connect_material_expressions(primer, "", lerp, "B")
    mel.connect_material_expressions(sat, "", lerp, "Alpha")
    mel.connect_material_property(lerp, "",
                                  unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -300, 200)
    rough.set_editor_property("r", 0.42)
    mel.connect_material_property(rough, "",
                                  unreal.MaterialProperty.MP_ROUGHNESS)
    mel.recompile_material(mat)
    lib.save_asset("%s/%s" % (MAT_DIR, NAME))
    unreal.log("PAINT MATERIAL created")
unreal.log("SHIP PAINT MATERIAL DONE")
