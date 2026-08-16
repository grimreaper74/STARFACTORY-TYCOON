import bpy
import json
from pathlib import Path
from mathutils import Vector

out = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressTrains\complete_blender_train_v925.json")
out.parent.mkdir(parents=True, exist_ok=True)

objects = []
mins = Vector((float("inf"),) * 3)
maxs = Vector((float("-inf"),) * 3)
for obj in bpy.context.scene.objects:
    if obj.type != "MESH" or obj.hide_render:
        continue
    for corner in obj.bound_box:
        p = obj.matrix_world @ Vector(corner)
        mins.x, mins.y, mins.z = min(mins.x, p.x), min(mins.y, p.y), min(mins.z, p.z)
        maxs.x, maxs.y, maxs.z = max(maxs.x, p.x), max(maxs.y, p.y), max(maxs.z, p.z)
    objects.append({
        "name": obj.name,
        "location": list(obj.location),
        "rotation_euler_degrees": [v * 57.295779513 for v in obj.rotation_euler],
        "dimensions": list(obj.dimensions),
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
    })

payload = {
    "blend": bpy.data.filepath,
    "mesh_object_count": len(objects),
    "world_bounds_min": list(mins),
    "world_bounds_max": list(maxs),
    "world_dimensions": list(maxs - mins),
    "objects": objects,
    "scene_objects": [{
        "name": obj.name,
        "type": obj.type,
        "instance_type": obj.instance_type,
        "instance_collection": obj.instance_collection.name if obj.instance_collection else None,
        "hide_render": obj.hide_render,
        "location": list(obj.location),
        "rotation_euler_degrees": [v * 57.295779513 for v in obj.rotation_euler],
        "scale": list(obj.scale),
    } for obj in bpy.context.scene.objects],
}
out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print("LINE_BOSS_COMPLETE_BLEND_AUDIT_V925", out)
