"""Read-only audit of the authored PR-005 HMI plaque objects."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


OUTPUT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\pr005_hmi_plaque_source.json")
NAMES = [
    "PR-005_HMIAssetPlate", "PR-005_HMIAssetText", "PR-005_HMICabinet",
    "PR-005_HMIConsoleHousing", "PR-005_HMILiveDisplaySurface",
    "PR-005_HMIScreen", "PR-005_HMIScreenBezel", "PR-005_HMIScreenBrow",
]


def record(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(point[index] for point in corners) for index in range(3)]
    maximum = [max(point[index] for point in corners) for index in range(3)]
    return {
        "name": obj.name,
        "type": obj.type,
        "parent": obj.parent.name if obj.parent else None,
        "matrix_world": [[round(float(value), 7) for value in row] for row in obj.matrix_world],
        "location_m": [round(float(value), 7) for value in obj.matrix_world.translation],
        "dimensions_m": [round(float(value), 7) for value in obj.dimensions],
        "bounds_world_m": {
            "min": [round(value, 7) for value in minimum],
            "max": [round(value, 7) for value in maximum],
        },
    }


records = []
for name in NAMES:
    obj = bpy.data.objects.get(name)
    if obj is None:
        raise RuntimeError(f"Missing authored object: {name}")
    records.append(record(obj))

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
OUTPUT.write_text(json.dumps({"source_blend": bpy.data.filepath, "objects": records}, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR005_HMI_PLAQUE_SOURCE_AUDIT_PASS output={OUTPUT}")
