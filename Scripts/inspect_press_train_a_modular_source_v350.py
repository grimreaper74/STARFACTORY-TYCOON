"""Read-only Blender inventory for planning the Pro-detail successor."""
import bpy
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ModularAssembly_v037/CA_MW_PressTrainA_ModularAssembly_v037.blend"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_modular_source_inventory_v350.json"
if OUT.exists():
    raise RuntimeError(f"Refusing to overwrite {OUT}")
bpy.ops.wm.open_mainfile(filepath=str(SRC))
stage_counts = Counter()
stage_bounds = defaultdict(lambda: [[float("inf")] * 3, [float("-inf")] * 3])
objects = []
for obj in bpy.data.objects:
    if obj.type not in {"MESH", "CURVE", "FONT"} or obj.hide_render:
        continue
    stage = next((s for s in ("S01", "S02", "S03", "S04", "S05", "S06", "S07") if s in obj.name), "COMMON")
    stage_counts[stage] += 1
    corners = [obj.matrix_world @ obj.data.vertices[i].co for i in range(len(obj.data.vertices))] if obj.type == "MESH" else []
    if corners:
        for axis in range(3):
            stage_bounds[stage][0][axis] = min(stage_bounds[stage][0][axis], *(v[axis] for v in corners))
            stage_bounds[stage][1][axis] = max(stage_bounds[stage][1][axis], *(v[axis] for v in corners))
    objects.append({"name": obj.name, "type": obj.type, "stage": stage,
                    "location_m": list(obj.location), "dimensions_m": list(obj.dimensions)})
payload = {"source": str(SRC.relative_to(ROOT)).replace("\\", "/"),
           "status": "READ_ONLY_SOURCE_INVENTORY__NO_SOURCE_CHANGE",
           "object_count": len(objects), "stage_counts": dict(stage_counts),
           "stage_bounds_m": {k: {"min": v[0], "max": v[1], "size": [v[1][i]-v[0][i] for i in range(3)]}
                              for k, v in stage_bounds.items()},
           "objects": objects, "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"object_count": len(objects), "stage_counts": dict(stage_counts), "stage_bounds_m": payload["stage_bounds_m"]}, indent=2))
