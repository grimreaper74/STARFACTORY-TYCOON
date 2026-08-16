"""Read-only clean-scene FBX round-trip bounds audit for rejected Unreal v351 intake."""
import bpy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
FBX = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/ProDetailModular_v046/FBX/SM_CA_MW_PressTrainA_ProDetailModular_v046.fbx"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_pro_detail_fbx_roundtrip_v352.json"
if OUT.exists():
    raise RuntimeError(f"Refusing to overwrite {OUT}")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX), automatic_bone_orientation=False)
objects = [o for o in bpy.context.scene.objects if o.type in {"MESH", "CURVE", "FONT"} and not o.hide_render]
minimum = Vector((float("inf"),) * 3)
maximum = Vector((float("-inf"),) * 3)
per_object = []
for obj in objects:
    lo = Vector((float("inf"),) * 3)
    hi = Vector((float("-inf"),) * 3)
    for corner in obj.bound_box:
        p = obj.matrix_world @ Vector(corner)
        for axis in range(3):
            lo[axis] = min(lo[axis], p[axis]); hi[axis] = max(hi[axis], p[axis])
            minimum[axis] = min(minimum[axis], p[axis]); maximum[axis] = max(maximum[axis], p[axis])
    per_object.append({"name": obj.name, "min": list(lo), "max": list(hi)})
h = hashlib.sha256(FBX.read_bytes()).hexdigest().upper()
payload = {"$schema": "cairnwell/audit/press-train-a-pro-detail-fbx-roundtrip-v352/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(), "status": "READ_ONLY_FBX_ROUNDTRIP_AUDIT",
    "fbx_sha256": h, "object_count": len(objects), "bounds_min_m": list(minimum),
    "bounds_max_m": list(maximum), "bounds_size_m": list(maximum-minimum),
    "line_end_objects": sorted(per_object, key=lambda item: item["min"][1])[:8] +
                        sorted(per_object, key=lambda item: item["max"][1], reverse=True)[:8],
    "source_mutated": False, "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
