"""Read-only imported material/slot inspection for control-room v001."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
DEST = "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v001/Meshes"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_material_slot_inspection_v001.json"
categories = (
    "Architecture", "Consoles", "Systems", "Furniture", "Interaction",
    "Service", "Identity", "State_Restored", "State_Mothballed",
)
rows = {}
for category in categories:
    mesh = unreal.EditorAssetLibrary.load_asset(f"{DEST}/SM_CA_MW_MCR_{category}_v001")
    if not isinstance(mesh, unreal.StaticMesh):
        rows[category] = {"missing": True}
        continue
    slots = []
    for material in mesh.get_editor_property("static_materials"):
        interface = material.get_editor_property("material_interface")
        slots.append({
            "slot_name": str(material.get_editor_property("material_slot_name")),
            "imported_slot_name": str(material.get_editor_property("imported_material_slot_name")),
            "material": interface.get_path_name() if interface else None,
        })
    rows[category] = {"slot_count": len(slots), "slots": slots}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")
print(json.dumps({category: row.get("slot_count") for category, row in rows.items()}, indent=2))

