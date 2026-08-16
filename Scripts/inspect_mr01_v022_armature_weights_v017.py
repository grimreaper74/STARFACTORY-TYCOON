"""Blender-side read-only audit of the MR01 v022 armature and rigid weights."""

import json
from pathlib import Path

import bpy


root = Path(bpy.data.filepath).parents[5]
out = root / "Saved/Audits/SupportRobots/mr01_v022_armature_weights_v017.json"
armature = bpy.data.objects.get("Armature")
mesh = bpy.data.objects.get("SK_LB_MR01_Arm6Axis")
if armature is None or mesh is None:
    raise RuntimeError("MR01 armature or skeletal mesh missing")

bones = []
for bone in armature.data.bones:
    bones.append({
        "name": bone.name,
        "parent": bone.parent.name if bone.parent else None,
        "head_local_m": [round(v, 6) for v in bone.head_local],
        "tail_local_m": [round(v, 6) for v in bone.tail_local],
        "use_deform": bool(bone.use_deform),
    })

groups = []
for group in mesh.vertex_groups:
    vertex_count = 0
    total_weight = 0.0
    min_weight = None
    max_weight = 0.0
    for vertex in mesh.data.vertices:
        for membership in vertex.groups:
            if membership.group == group.index:
                vertex_count += 1
                total_weight += membership.weight
                min_weight = membership.weight if min_weight is None else min(min_weight, membership.weight)
                max_weight = max(max_weight, membership.weight)
                break
    groups.append({
        "name": group.name,
        "vertex_count": vertex_count,
        "weight_sum": round(total_weight, 4),
        "min_weight": round(min_weight or 0.0, 4),
        "max_weight": round(max_weight, 4),
    })

modifiers = [{"name": m.name, "type": m.type, "object": getattr(m, "object", None).name if getattr(m, "object", None) else None}
             for m in mesh.modifiers]
parent_bone = mesh.parent_bone if mesh.parent_type == "BONE" else None
payload = {
    "$schema": "cairnwell/audit/mr01-v022-armature-weights-v017/v1",
    "status": "PASS__READ_ONLY_ARMATURE_AND_WEIGHT_INVENTORY",
    "blend": bpy.data.filepath,
    "armature": armature.name,
    "armature_transform": {
        "location_m": [round(v, 6) for v in armature.location],
        "rotation_rad": [round(v, 6) for v in armature.rotation_euler],
        "scale": [round(v, 6) for v in armature.scale],
    },
    "bones": bones,
    "mesh": mesh.name,
    "mesh_parent": mesh.parent.name if mesh.parent else None,
    "mesh_parent_type": mesh.parent_type,
    "mesh_parent_bone": parent_bone,
    "mesh_vertex_count": len(mesh.data.vertices),
    "modifiers": modifiers,
    "vertex_groups": groups,
    "bone_names_without_vertex_group": sorted(set(b["name"] for b in bones) - set(g["name"] for g in groups)),
    "vertex_groups_without_bone": sorted(set(g["name"] for g in groups) - set(b["name"] for b in bones)),
    "source_modified": False,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print("LINE_BOSS_MR01_ARMATURE_WEIGHTS_V017 {}".format(out))
