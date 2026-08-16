"""Create separately versioned, material-only Cairnwell review derivatives.
Inputs are previously cleaned Blender derivatives and are never overwritten.
"""
import bpy
import json
import os
import sys
from mathutils import Vector

output_blend, output_manifest, module_kind = sys.argv[sys.argv.index("--") + 1:][:3]
specs = {
    "hmi": {
        "source_object": "CW_Module_OperatorHMI_CleanDerivative_v002",
        "output_object": "CW_Module_OperatorHMI_CairnwellLivery_v001",
        "identity": "HMI-PR005-01",
        "policy": "freestanding operator HMI module only"
    },
    "cabinet": {
        "source_object": "CW_Module_ElectricalCabinet_CleanDerivative_v001",
        "output_object": "CW_Module_ElectricalCabinet_CairnwellLivery_v001",
        "identity": "PR005-DC01",
        "policy": "full electrical/service cabinet module only"
    }
}
if module_kind not in specs:
    raise RuntimeError("Unknown module kind: " + module_kind)
spec = specs[module_kind]
source = bpy.data.objects.get(spec["source_object"])
if not source:
    raise RuntimeError("Expected clean candidate is missing: " + spec["source_object"])

mesh = source.data.copy()
for object_ in list(bpy.data.objects): bpy.data.objects.remove(object_, do_unlink=True)
for collection in list(bpy.data.collections): bpy.data.collections.remove(collection)
scene=bpy.context.scene
collection=bpy.data.collections.new("CW_CairnwellLiveryReview_v001"); scene.collection.children.link(collection)
asset=bpy.data.objects.new(spec["output_object"],mesh); collection.objects.link(asset)

for material in list(bpy.data.materials): bpy.data.materials.remove(material)
def mat(name,hex_value,metallic,roughness,emission=None):
    value=bpy.data.materials.new(name); value.use_nodes=True; node=value.node_tree.nodes.get("Principled BSDF")
    colour=tuple(int(hex_value[index:index+2],16)/255 for index in (1,3,5))
    node.inputs["Base Color"].default_value=(*colour,1); node.inputs["Metallic"].default_value=metallic; node.inputs["Roughness"].default_value=roughness
    if emission:
        node.inputs["Emission Color"].default_value=(*colour,1); node.inputs["Emission Strength"].default_value=emission
    return value
warm=mat("CW_WarmWhite_RAL9002", "#F3F1E9", .25, .35)
graph=mat("CW_FoundryCharcoal_RAL7021", "#202428", .55, .28)
green=mat("CW_CairnwellGreen_RAL6004", "#1F4B44", .35, .32)
yellow=mat("CW_SafetyYellow_RAL1023", "#F2C300", .25, .34)
red=mat("CW_SignalRed_RAL3020", "#C7352C", .2, .3)
screen=mat("CW_DisplayCoolGrey", "#70777C", .15, .2, .08)
for value in (warm,graph,green,yellow,red,screen): asset.data.materials.append(value)

# Base remains warm white. Material indices are based on face position/normals so
# this is an intentionally separate visual proposal rather than a source edit.
for polygon in asset.data.polygons: polygon.material_index=0
world_z=[(asset.matrix_world @ vertex.co).z for vertex in asset.data.vertices]
z_min,z_max=min(world_z),max(world_z)
for polygon in asset.data.polygons:
    center=asset.matrix_world @ polygon.center
    normal=(asset.matrix_world.to_3x3() @ polygon.normal).normalized()
    # Graphite lower plinth / foot, plus side/under hardware.
    if center.z < z_min + (z_max-z_min)*.095:
        polygon.material_index=1
    # Restrained operator-side green identity/service face around the front band.
    if normal.y < -.70 and center.z > z_min+(z_max-z_min)*.48 and center.z < z_min+(z_max-z_min)*.88 and abs(center.x) < .20:
        polygon.material_index=2
    # Display inset reads as a neutral technological screen.
    if normal.y < -.70 and center.z > z_min+(z_max-z_min)*.69 and center.z < z_min+(z_max-z_min)*.84 and abs(center.x) < .15:
        polygon.material_index=5
    # Safety-yellow reserved for the E-stop surround / cabinet functional edge.
    if normal.y < -.70 and center.z > z_min+(z_max-z_min)*.54 and center.z < z_min+(z_max-z_min)*.64 and center.x > .11:
        polygon.material_index=3
    # Signal red only on a very small functional stop face.
    if normal.y < -.75 and center.z > z_min+(z_max-z_min)*.54 and center.z < z_min+(z_max-z_min)*.62 and center.x > .18:
        polygon.material_index=4

asset["CW_Status"]="candidate-only; visual-only; no collision; not Unreal-imported"
asset["CW_Provenance"]=spec["source_object"]+" (clean geometry candidate); livery derivative is material-only"
asset["CW_IdentityPlate"]=spec["identity"]
asset["CW_UsePolicy"]=spec["policy"]+"; local fit, material review and runtime validation required"
asset["CW_Collision"]="NoCollision"
points=[asset.matrix_world@Vector(corner) for corner in asset.bound_box]; low=[min(point[i] for point in points) for i in range(3)]; high=[max(point[i] for point in points) for i in range(3)]
manifest={"asset":asset.name,"kind":"material-only Cairnwell review derivative","source_clean_candidate":spec["source_object"],"identity":spec["identity"],"source_files_unchanged":True,"status":"candidate-only; visual-only; no collision; not Unreal imported","dimensions_m":[round(high[i]-low[i],5) for i in range(3)],"palette":{"warm_white":"#F3F1E9","foundry_charcoal":"#202428","cairnwell_green":"#1F4B44","safety_yellow":"#F2C300","signal_red":"#C7352C","steel_grey":"#70777C"},"policy":"Yellow/red are functional marking only. No gameplay, collision, pivot or runtime bindings changed."}
os.makedirs(os.path.dirname(output_blend),exist_ok=True)
with open(output_manifest,"w",encoding="utf-8") as handle: json.dump(manifest,handle,indent=2);handle.write("\n")
bpy.ops.wm.save_as_mainfile(filepath=output_blend)
print(json.dumps(manifest))
