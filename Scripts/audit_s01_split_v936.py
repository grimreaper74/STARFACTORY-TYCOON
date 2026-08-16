"""Audit the selected S01 split Blender source without modifying it."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

out = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressTrains\s01_selected_split_v936.json")
out.parent.mkdir(parents=True, exist_ok=True)

rows = []
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    world = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    lo = Vector((min(p.x for p in world), min(p.y for p in world), min(p.z for p in world)))
    hi = Vector((max(p.x for p in world), max(p.y for p in world), max(p.z for p in world)))
    rows.append({
        "name": obj.name,
        "location": [round(v, 6) for v in obj.location],
        "dimensions": [round(v, 6) for v in (hi-lo)],
        "center": [round(v, 6) for v in ((lo+hi)*0.5)],
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "materials": [m.name if m else None for m in obj.data.materials],
    })

rows.sort(key=lambda r: (-r["polygons"], r["name"]))
payload = {"source": bpy.data.filepath, "mesh_count": len(rows), "objects": rows}
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_S01_SPLIT_AUDIT_V936", out, len(rows))
