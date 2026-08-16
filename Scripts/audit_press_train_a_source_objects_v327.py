"""Audit v037 object names/types/materials to isolate sign and label geometry."""
import bpy
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
src = root / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v037/CA_MW_PressTrainA_ModularAssembly_v037.blend"
out = root / "Saved/Audits/PressTrains/press_train_a_source_object_audit_v327.json"
bpy.ops.wm.open_mainfile(filepath=str(src))
rows = []
keywords = ("sign", "label", "text", "station", "s01", "s02", "s03", "s04", "s05", "s06", "s07", "cairn", "process", "nameplate", "decal")
for obj in bpy.data.objects:
    mats = [slot.material.name if slot.material else None for slot in getattr(obj, "material_slots", [])]
    searchable = " ".join([obj.name, *[m or "" for m in mats]]).lower()
    row = {
        "name": obj.name,
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "location": list(obj.location),
        "dimensions": list(obj.dimensions),
        "materials": mats,
        "suspected_graphic": any(k in searchable for k in keywords),
    }
    if obj.type == "FONT":
        row["body"] = obj.data.body
        row["suspected_graphic"] = True
    rows.append(row)
payload = {
    "source": str(src),
    "object_count": len(rows),
    "type_counts": {t: sum(1 for r in rows if r["type"] == t) for t in sorted({r["type"] for r in rows})},
    "suspected_graphics": [r for r in rows if r["suspected_graphic"]],
    "all_objects": rows,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"object_count": len(rows), "suspected_count": len(payload["suspected_graphics"]), "output": str(out)}, indent=2))
