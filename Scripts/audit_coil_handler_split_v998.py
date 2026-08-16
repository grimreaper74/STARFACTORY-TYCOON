"""Inventory the Meshy coil-handler split and identify plausible lift subassemblies."""
import bpy
import json
from pathlib import Path
from mathutils import Vector

ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE = ROOT / "SourceAssets/Candidate/PressShop/Inbound/CoilHandlerAGV_v20260810/Original/Meshy_AI__0810171248_part-segmentation.blend"
OUT = ROOT / "Saved/Audits/PressShopIntegration/coil_handler_split_inventory_v998.json"

bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
bpy.context.view_layer.update()
rows = []
all_points = []
for obj in bpy.context.scene.objects:
    if obj.type != "MESH":
        continue
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    all_points.extend(points)
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    dims = high - low
    centre = (low + high) * 0.5
    tris = sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons)
    rows.append({
        "name": obj.name, "vertices": len(obj.data.vertices), "triangles": tris,
        "centre_m": [round(v, 6) for v in centre],
        "low_m": [round(v, 6) for v in low], "high_m": [round(v, 6) for v in high],
        "dimensions_m": [round(v, 6) for v in dims],
        "volume_proxy_m3": round(dims.x * dims.y * dims.z, 7),
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
    })

low = Vector(tuple(min(point[i] for point in all_points) for i in range(3)))
high = Vector(tuple(max(point[i] for point in all_points) for i in range(3)))
rows.sort(key=lambda row: row["volume_proxy_m3"], reverse=True)
payload = {
    "status": "PASS__SPLIT_INVENTORIED__MOTION_SELECTION_PENDING_VISUAL_REVIEW",
    "source": str(SOURCE), "mesh_objects": len(rows),
    "envelope_m": [round(v, 6) for v in high - low], "parts": rows,
    "rule": "texture master is appearance authority; split is motion guide only",
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_COIL_HANDLER_SPLIT_V998", len(rows), payload["envelope_m"])
