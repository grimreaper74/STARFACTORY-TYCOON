"""Read-only parameter audit for the controlled inbound brushed-steel material."""
from pathlib import Path
import json
import unreal

project = Path(unreal.Paths.project_dir())
path = "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001/Materials_v001/MI_CA_Inbound_BrushedSteel_v001"
material = unreal.EditorAssetLibrary.load_asset(path)
if material is None:
    raise RuntimeError("Missing controlled inbound brushed steel")

def parameter_rows(property_name):
    rows = []
    try:
        values = material.get_editor_property(property_name)
    except Exception as exc:
        return [{"unavailable": str(exc)}]
    for value in values:
        info = value.get_editor_property("parameter_info")
        row = {"name": str(info.get_editor_property("name"))}
        for key in ("parameter_value", "value"):
            try:
                row["value"] = str(value.get_editor_property(key))
                break
            except Exception:
                pass
        rows.append(row)
    return rows

parent = material.get_editor_property("parent")
out = project / "Saved/Audits/PressShopIntegration/inbound_brushed_steel_parameters_v546.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({
    "status": "READ_ONLY",
    "asset": path,
    "class": material.get_class().get_name(),
    "parent": parent.get_path_name() if parent else None,
    "scalar_parameters": parameter_rows("scalar_parameter_values"),
    "vector_parameters": parameter_rows("vector_parameter_values"),
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_STEEL_PARAMETER_AUDIT_V546_PASS")
