"""Repair the UE 5.8 Abs input binding in the preserved v023 material."""

import unreal


MATERIAL_PATH = "/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v023/M_LB_BareCoil_WoundSteel_v023"
lib = unreal.EditorAssetLibrary
mel = unreal.MaterialEditingLibrary
material = lib.load_asset(MATERIAL_PATH)
if material is None:
    raise RuntimeError(f"Missing material: {MATERIAL_PATH}")

expressions = mel.get_material_expressions(material)
texture_coordinates = [node for node in expressions if isinstance(node, unreal.MaterialExpressionTextureCoordinate)]
component_masks = [node for node in expressions if isinstance(node, unreal.MaterialExpressionComponentMask)]
sines = [node for node in expressions if isinstance(node, unreal.MaterialExpressionSine)]
absolutes = [node for node in expressions if isinstance(node, unreal.MaterialExpressionAbs)]
scaled_multiply = [
    node for node in expressions
    if isinstance(node, unreal.MaterialExpressionMultiply)
    and int(node.get_editor_property("material_expression_editor_x")) < -500
]
if len(texture_coordinates) != 1 or len(component_masks) != 1 or len(sines) != 1 or len(absolutes) != 1 or len(scaled_multiply) != 1:
    raise RuntimeError(
        "Expected one TextureCoordinate, ComponentMask, scaled Multiply, Sine and Abs node, found "
        f"{len(texture_coordinates)}, {len(component_masks)}, {len(scaled_multiply)}, {len(sines)} and {len(absolutes)}"
    )

if not mel.connect_material_expressions(texture_coordinates[0], "", component_masks[0], ""):
    raise RuntimeError("Could not connect TextureCoordinate to the unnamed ComponentMask input")
if not mel.connect_material_expressions(scaled_multiply[0], "", sines[0], ""):
    raise RuntimeError("Could not connect scaled Multiply to the unnamed Sine input")
if not mel.connect_material_expressions(sines[0], "", absolutes[0], ""):
    raise RuntimeError("Could not connect Sine to the unnamed Abs input")
mel.recompile_material(material)
if not lib.save_loaded_asset(material, only_if_is_dirty=False):
    raise RuntimeError("Could not save repaired v023 wound-steel material")

unreal.log("LINE_BOSS_WOUND_STEEL_MATERIAL_V023_REPAIR_PASS mask_input=unnamed sine_input=unnamed abs_input=unnamed")
unreal.SystemLibrary.quit_editor()
