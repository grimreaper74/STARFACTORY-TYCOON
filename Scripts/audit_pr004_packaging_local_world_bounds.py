"""Read-only Blender audit of PR-004 packaging local versus world bounds."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


project = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
out = project / "Saved/Audits/pr004_packaging_v003_local_world_bounds.json"
names = {
    "SM_LB_PR004_BareCoilCore_v003",
    "SM_LB_PR004_WrapSection_01_v003",
    "SM_LB_PR004_WrapSection_13_v003",
    "SM_LB_PR004_WrapSection_14_v003",
    "SM_LB_PR004_EdgeProtector_01_L_v003",
    "SM_LB_PR004_Band_01_v003",
}
records = []
for obj in bpy.data.objects:
    if obj.name not in names:
        continue
    local = [Vector(corner) for corner in obj.bound_box]
    world = [obj.matrix_world @ corner for corner in local]
    records.append({
        "name": obj.name,
        "location_m": [round(value, 6) for value in obj.location],
        "local_min_m": [round(min(point[i] for point in local), 6) for i in range(3)],
        "local_max_m": [round(max(point[i] for point in local), 6) for i in range(3)],
        "world_min_m": [round(min(point[i] for point in world), 6) for i in range(3)],
        "world_max_m": [round(max(point[i] for point in world), 6) for i in range(3)],
    })
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"records": sorted(records, key=lambda item: item["name"])}, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR004_PACKAGING_BOUNDS_AUDIT={out}")
