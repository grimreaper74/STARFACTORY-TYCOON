"""Create a source-preserving cleaned derivative of a detailed compact service enclosure."""
import bpy
import bmesh
import json
import os
import sys
from mathutils import Vector

output_blend, output_report = sys.argv[sys.argv.index("--") + 1:][:2]
source_name = "mesh_node"
source = bpy.data.objects.get(source_name)
if not source or source.type != "MESH":
    raise RuntimeError("Expected service-enclosure mesh not found: " + source_name)
source_mesh = source.data.copy(); source_matrix = source.matrix_world.copy()
for obj in list(bpy.data.objects): bpy.data.objects.remove(obj, do_unlink=True)
for collection in list(bpy.data.collections): bpy.data.collections.remove(collection)
scene = bpy.context.scene
collection = bpy.data.collections.new("CW_CompactServiceEnclosure_CleanupDerivative_v001")
scene.collection.children.link(collection)
asset = bpy.data.objects.new("CW_Module_CompactServiceEnclosure_CleanDerivative_v001", source_mesh)
collection.objects.link(asset); asset.matrix_world = source_matrix
bpy.context.view_layer.objects.active = asset; asset.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
modifier = asset.modifiers.new("CW_VisualCleanup_VoxelRemesh", "REMESH")
modifier.mode = "VOXEL"; modifier.voxel_size = .007; modifier.use_smooth_shade = True; modifier.use_remove_disconnected = False
bpy.ops.object.modifier_apply(modifier=modifier.name)
bm=bmesh.new(); bm.from_mesh(asset.data); components=[]; seen=set()
for vert in bm.verts:
    if vert in seen: continue
    stack, group=[vert], []; seen.add(vert)
    while stack:
        current=stack.pop(); group.append(current)
        for edge in current.link_edges:
            other=edge.other_vert(current)
            if other not in seen: seen.add(other); stack.append(other)
    components.append(group)
for group in components:
    if len(group)<30: bmesh.ops.delete(bm,geom=group,context="VERTS")
bm.to_mesh(asset.data); bm.free(); asset.data.update()
asset.data.materials.clear()
for material in list(bpy.data.materials): bpy.data.materials.remove(material)
def material(name,color,metallic,roughness):
    value=bpy.data.materials.new(name); value.use_nodes=True; node=value.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value=(*color,1); node.inputs["Metallic"].default_value=metallic; node.inputs["Roughness"].default_value=roughness
    return value
asset.data.materials.append(material("CW_Mat_WarmWhite_Candidate",(.73,.72,.67),.28,.34))
asset.data.materials.append(material("CW_Mat_Graphite_Candidate",(.035,.042,.048),.58,.28))
for poly in asset.data.polygons: poly.material_index=0
asset["CW_Status"]="candidate-only; visual-only; no collision; not Unreal-imported"
asset["CW_Provenance"]="Meshy_AI_Compact_industrial_pl_0810151315_generate.blend / mesh_node"
asset["CW_UsePolicy"]="whole compact service/plant enclosure only; later material, fit and runtime validation required"
asset["CW_Collision"]="NoCollision"
points=[asset.matrix_world@Vector(corner) for corner in asset.bound_box]; low=[min(point[i] for point in points) for i in range(3)]; high=[max(point[i] for point in points) for i in range(3)]
bm=bmesh.new(); bm.from_mesh(asset.data); nonmanifold=sum(1 for edge in bm.edges if not edge.is_manifold); loose=sum(1 for vert in bm.verts if not vert.link_edges); bm.free()
report={"derivative":os.path.basename(output_blend),"source_unchanged":True,"source":"Meshy_AI_Compact_industrial_pl_0810151315_generate.blend / mesh_node","object":asset.name,"policy":"candidate-only visual-only derivative; no collision; no Unreal import","cleanup":{"method":"duplicate-only voxel remesh plus micro-island cleanup","voxel_m":.007},"dimensions_m":[round(high[i]-low[i],5) for i in range(3)],"vertices":len(asset.data.vertices),"polygons":len(asset.data.polygons),"non_manifold_edges":nonmanifold,"loose_vertices":loose,"material_slots":[slot.material.name if slot.material else None for slot in asset.material_slots]}
os.makedirs(os.path.dirname(output_blend),exist_ok=True)
with open(output_report,"w",encoding="utf-8") as handle: json.dump(report,handle,indent=2); handle.write("\n")
bpy.ops.wm.save_as_mainfile(filepath=output_blend)
print(json.dumps(report))
