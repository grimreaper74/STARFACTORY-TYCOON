"""Read-only audit of the combined v037 Train A Unreal material slots."""
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
ASSET = "/Game/LineBoss/Candidates/PressTrains/TrainA/ModularVisual_v302/SM_CA_MW_PressTrainA_ModularAssembly_v037"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_modular_unreal_materials_v313.json"
mesh = unreal.EditorAssetLibrary.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError("mesh missing")
rows = []
for index, slot in enumerate(mesh.get_editor_property("static_materials")):
    material = slot.get_editor_property("material_interface")
    rows.append({
        "index": index,
        "slot_name": str(slot.get_editor_property("material_slot_name")),
        "imported_slot_name": str(slot.get_editor_property("imported_material_slot_name")),
        "material": material.get_path_name() if material else None,
        "class": material.get_class().get_name() if material else None,
    })
payload = {
    "$schema": "cairnwell/audit/press-train-a-modular-unreal-materials-v313/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "asset": ASSET,
    "slot_count": len(rows),
    "default_or_missing_count": sum(1 for row in rows if not row["material"] or "DefaultMaterial" in row["material"]),
    "material_slots": rows,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
