"""Read-only audit of the native keyed S02 material graph."""
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MATERIAL_PATH = "/Game/LineBoss/Candidates/PressShop/PressShop2DSprites_v002/Materials/M_LB_PS_S02_DrawForm_SpriteMasterOverhead_Keyed_Unlit_v002"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_s02_overhead_material_graph_audit_v001.json"

def describe_input(node, name):
    try:
        value = node.get_editor_property(name)
        return repr(value)
    except Exception as exc:
        return "ERROR: " + repr(exc)

material = unreal.load_asset(MATERIAL_PATH)
if not isinstance(material, unreal.Material):
    raise RuntimeError("S02 keyed material is missing")
expressions = list(material.get_editor_property("expressions") or [])
nodes = []
for expression in expressions:
    entry = {"class": expression.get_class().get_name(), "name": expression.get_name()}
    if isinstance(expression, unreal.MaterialExpressionIf):
        entry["inputs"] = {
            "a": describe_input(expression, "a"),
            "b": describe_input(expression, "b"),
            "a_greater_than_b": describe_input(expression, "a_greater_than_b"),
            "a_equals_b": describe_input(expression, "a_equals_b"),
            "a_less_than_b": describe_input(expression, "a_less_than_b"),
        }
    nodes.append(entry)
report = {
    "status": "PASS__READ_ONLY_KEYED_MATERIAL_GRAPH_AUDIT",
    "material": material.get_path_name(),
    "blend_mode": str(material.get_editor_property("blend_mode")),
    "shading_model": str(material.get_editor_property("shading_model")),
    "opacity_mask": describe_input(material, "opacity_mask"),
    "expression_count": len(nodes),
    "expressions": nodes,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_S02_KEYED_MATERIAL_GRAPH_AUDIT=" + json.dumps(report, sort_keys=True))
unreal.SystemLibrary.quit_editor()

