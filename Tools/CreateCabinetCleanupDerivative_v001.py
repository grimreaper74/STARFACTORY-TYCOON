"""Create a separate visual-only clean cabinet derivative from immutable v632 source."""
import bpy
import bmesh
import json
import os
import sys
from mathutils import Vector

output_blend, output_report = sys.argv[sys.argv.index("--") + 1:][:2]
source_name = "SM_CA_Factory_ElectricalCabinet_MeshyMaster_v632"
source = bpy.data.objects.get(source_name)
if not source or source.type != "MESH":
    raise RuntimeError("Expected cabinet mesh not found: " + source_name)
source_mesh = source.data.copy()
source_matrix = source.matrix_world.copy()

for obj in list(bpy.data.objects):
    bpy.data.objects.remove(obj, do_unlink=True)
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)
scene = bpy.context.scene
collection = bpy.data.collections.new("CW_Cabinet_CleanupDerivative_v001")
scene.collection.children.link(collection)
hmi = bpy.data.objects.new("CW_Module_ElectricalCabinet_CleanDerivative_v001", source_mesh)
collection.objects.link(hmi)
hmi.matrix_world = source_matrix
bpy.context.view_layer.objects.active = hmi
hmi.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

modifier = hmi.modifiers.new("CW_VisualCleanup_VoxelRemesh", "REMESH")
modifier.mode = "VOXEL"
modifier.voxel_size = 0.007
modifier.use_smooth_shade = True
modifier.use_remove_disconnected = False
bpy.ops.object.modifier_apply(modifier=modifier.name)

bm = bmesh.new(); bm.from_mesh(hmi.data)
components, seen = [], set()
for vert in bm.verts:
    if vert in seen:
        continue
    stack, group = [vert], []
    seen.add(vert)
    while stack:
        current = stack.pop()
        group.append(current)
        for edge in current.link_edges:
            other = edge.other_vert(current)
            if other not in seen:
                seen.add(other); stack.append(other)
    components.append(group)
for group in components:
    if len(group) < 30:
        bmesh.ops.delete(bm, geom=group, context="VERTS")
bm.to_mesh(hmi.data); bm.free(); hmi.data.update()

hmi.data.materials.clear()
for material in list(bpy.data.materials):
    bpy.data.materials.remove(material)
def make_material(name, color, metallic, roughness):
    material = bpy.data.materials.new(name); material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return material
hmi.data.materials.append(make_material("CW_Mat_WarmWhite_Candidate", (0.73, 0.72, 0.67), .28, .34))
hmi.data.materials.append(make_material("CW_Mat_Graphite_Candidate", (.035, .042, .048), .58, .28))
for polygon in hmi.data.polygons: polygon.material_index = 0
hmi["CW_Status"] = "candidate-only; visual-only; no collision; not Unreal-imported"
hmi["CW_Provenance"] = "CA_Factory_Cabinet_HMI_MeshyMasters_v632.blend / " + source_name
hmi["CW_UsePolicy"] = "full electrical/service cabinet only; later material, fit and runtime validation required"
hmi["CW_Collision"] = "NoCollision"

points = [hmi.matrix_world @ Vector(corner) for corner in hmi.bound_box]
low = [min(point[i] for point in points) for i in range(3)]
high = [max(point[i] for point in points) for i in range(3)]
bm = bmesh.new(); bm.from_mesh(hmi.data)
nonmanifold = sum(1 for edge in bm.edges if not edge.is_manifold)
loose = sum(1 for vert in bm.verts if not vert.link_edges)
bm.free()
report = {
    "derivative": os.path.basename(output_blend),
    "source_unchanged": True,
    "source": "CA_Factory_Cabinet_HMI_MeshyMasters_v632.blend / " + source_name,
    "object": hmi.name,
    "policy": "candidate-only visual-only derivative; no collision; no Unreal import",
    "cleanup": {"method": "duplicate-only voxel remesh plus micro-island cleanup", "voxel_m": .007},
    "dimensions_m": [round(high[i] - low[i], 5) for i in range(3)],
    "vertices": len(hmi.data.vertices), "polygons": len(hmi.data.polygons),
    "non_manifold_edges": nonmanifold, "loose_vertices": loose,
    "material_slots": [slot.material.name if slot.material else None for slot in hmi.material_slots]
}
os.makedirs(os.path.dirname(output_blend), exist_ok=True)
with open(output_report, "w", encoding="utf-8") as handle:
    json.dump(report, handle, indent=2); handle.write("\n")
bpy.ops.wm.save_as_mainfile(filepath=output_blend)
print(json.dumps(report))
