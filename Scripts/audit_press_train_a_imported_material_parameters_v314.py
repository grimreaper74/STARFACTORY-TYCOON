"""Inspect representative imported FBX material instances for the v037 Train A intake."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MESH_PATH = "/Game/LineBoss/Candidates/PressTrains/TrainA/ModularVisual_v302/SM_CA_MW_PressTrainA_ModularAssembly_v037"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_imported_material_parameters_v314.json"
mesh = unreal.load_asset(MESH_PATH)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("mesh missing")
seen = set()
rows = []
for slot in mesh.get_editor_property("static_materials"):
    name = str(slot.get_editor_property("material_slot_name"))
    root_name = name.rstrip("_0123456789")
    if root_name in seen:
        continue
    seen.add(root_name)
    material = slot.get_editor_property("material_interface")
    row = {"slot": name, "material": material.get_path_name() if material else None}
    if isinstance(material, unreal.MaterialInstanceConstant):
        parent = material.get_editor_property("parent")
        row.update({
            "parent": parent.get_path_name() if parent else None,
            "vector_parameter_values": [str(v) for v in material.get_editor_property("vector_parameter_values")],
            "scalar_parameter_values": [str(v) for v in material.get_editor_property("scalar_parameter_values")],
            "texture_parameter_values": [str(v) for v in material.get_editor_property("texture_parameter_values")],
        })
    rows.append(row)
payload = {
    "$schema": "cairnwell/audit/press-train-a-imported-material-parameters-v314/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "representative_family_count": len(rows),
    "representative_materials": rows,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
