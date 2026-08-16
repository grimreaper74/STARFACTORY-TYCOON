"""Read-only inventory of retained MR01 v022 for a clean Unreal successor export."""

from datetime import datetime, timezone
import json
from pathlib import Path

import bpy


OUT = Path(__file__).resolve().parents[1] / "Saved/Audits/SupportRobots/mr01_v022_blender_export_structure.json"


def collections_for(obj):
    return sorted(collection.name for collection in obj.users_collection)


rows = []
for obj in bpy.data.objects:
    if obj.type not in {"MESH", "ARMATURE", "EMPTY"}:
        continue
    rows.append({
        "name": obj.name,
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "collections": collections_for(obj),
        "location": [round(float(v), 6) for v in obj.location],
        "rotation_euler": [round(float(v), 6) for v in obj.rotation_euler],
        "scale": [round(float(v), 6) for v in obj.scale],
        "hide_render": bool(obj.hide_render),
        "custom_properties": sorted(str(key) for key in obj.keys() if key != "_RNA_UI"),
    })

payload = {
    "$schema": "cairnwell/audit/mr01-v022-blender-export-structure/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__READ_ONLY_SOURCE_INVENTORY",
    "blend": bpy.data.filepath,
    "collections": sorted(collection.name for collection in bpy.data.collections),
    "objects": sorted(rows, key=lambda row: (row["type"], row["name"])),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print("LINE_BOSS_MR01_V022_STRUCTURE {} objects".format(len(rows)))
