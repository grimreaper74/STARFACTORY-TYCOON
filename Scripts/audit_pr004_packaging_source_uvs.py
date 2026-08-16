"""Read-only Blender audit of PR-004 packaging source UV availability."""

from __future__ import annotations

import json
from pathlib import Path

import bpy


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = REPO / "Saved/Audits/pr004_packaging_source_uv_audit_v001.json"

records = []
for obj in sorted((item for item in bpy.data.objects if item.type == "MESH"), key=lambda item: item.name):
    records.append({
        "object": obj.name,
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "uv_layers": [layer.name for layer in obj.data.uv_layers],
        "material_slots": [slot.material.name if slot.material else None for slot in obj.material_slots],
    })

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS" if records and all(record["uv_layers"] for record in records) else "UV_REBUILD_REQUIRED",
    "blend": bpy.data.filepath,
    "mesh_object_count": len(records),
    "objects_with_uvs": sum(bool(record["uv_layers"]) for record in records),
    "records": records,
}, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR004_PACKAGING_SOURCE_UV_AUDIT={OUT}")
