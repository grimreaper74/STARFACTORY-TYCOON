"""Inspect the actual native Unreal MaterialExpressionIf pin labels without saving assets."""
import json
from pathlib import Path
import unreal

ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2DSprites_v002/Materials"
NAME = "M_LB_PS_S02_DrawForm_SpriteMasterOverhead_Keyed_Unlit_v002"
material = unreal.load_asset(ROOT + "/" + NAME)
if material is None:
    raise RuntimeError("expected S02 candidate material")
node = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionIf, 0, 0)
inputs = list(unreal.MaterialEditingLibrary.get_material_expression_input_names(node))
outputs = list(unreal.MaterialEditingLibrary.get_material_expression_output_names(node))
record = {"inputs": inputs, "outputs": outputs}
unreal.log("PRESSSHOP_IF_PIN_AUDIT=" + json.dumps(record))
Path(unreal.Paths.project_saved_dir()).joinpath(
    "Audits", "PressShopIntegration", "pressshop_if_pin_audit_v001.json"
).write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
unreal.EditorPythonScripting.set_keep_python_script_alive(False)
unreal.SystemLibrary.quit_editor()

