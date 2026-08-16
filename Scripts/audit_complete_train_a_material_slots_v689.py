"""Read-only semantic material-slot inventory for the v688 Train A meshes."""
from pathlib import Path
from datetime import datetime, timezone
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / r"Saved\Audits\PressTrains\complete_train_a_asset_performance_v688.json"
OUT = ROOT / r"Saved\Audits\PressTrains\complete_train_a_material_slots_v689.json"
if OUT.exists():
    raise RuntimeError("Refusing to overwrite v689")
audit = json.loads(SOURCE.read_text(encoding="utf-8"))
rows = []
for asset_row in audit["assets"]:
    if asset_row["visual_instances"] <= 0 or not asset_row["asset"].startswith("/Game/LineBoss/"):
        continue
    mesh = unreal.load_asset(asset_row["asset"])
    if not isinstance(mesh, unreal.StaticMesh):
        rows.append({"asset": asset_row["asset"], "load": "FAIL", "slots": []})
        continue
    slots = []
    for index, slot in enumerate(mesh.get_editor_property("static_materials")):
        interface = slot.get_editor_property("material_interface")
        slots.append({
            "index": index,
            "material_slot_name": str(slot.get_editor_property("material_slot_name")),
            "imported_material_slot_name": str(slot.get_editor_property("imported_material_slot_name")),
            "current_material": interface.get_path_name() if interface else None,
        })
    rows.append({"asset": asset_row["asset"], "load": "PASS", "slots": slots})
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "revision": "v689",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READ_ONLY_SEMANTIC_SLOT_INVENTORY",
    "assets": rows,
    "protected_map_modified": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_COMPLETE_TRAIN_A_MATERIAL_SLOT_AUDIT_V689_PASS")
