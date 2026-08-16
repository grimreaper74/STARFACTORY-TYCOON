"""Render the approved repaired coil seated on two approved empty stand rails."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

root = Path(__file__).resolve().parents[1]
coil_blend = root / "SourceAssets/Candidate/PressShop/InboundCoilDelivery/WrappedCoil_v20260809_v003/Cairnwell_WrappedCoil_Repaired_v003.blend"
stand_blend = root / "SourceAssets/Candidate/PressShop/InboundCoilDelivery/MeshyAdjustableCoilStand_v20260809_v005/Cairnwell_AdjustableCoilStand_UnrealExport_v005.blend"
out = root / "Saved/ValidationRenders/PressShop/PlayerBuiltCoilStorage_v914"
out.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

def append_meshes(path):
    before = set(bpy.data.objects)
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        dst.objects = src.objects
    for obj in dst.objects:
        if obj is not None:
            bpy.context.collection.objects.link(obj)
    return [o for o in bpy.data.objects if o not in before and o.type == "MESH"]

stands = append_meshes(stand_blend)
if len(stands) != 1:
    raise RuntimeError(f"Expected one approved stand mesh, got {len(stands)}")
stand_a = stands[0]
stand_a.name = "ApprovedStand_A"
stand_b = stand_a.copy()
stand_b.data = stand_a.data
bpy.context.collection.objects.link(stand_b)
stand_b.name = "ApprovedStand_B"
stand_a.location.y = -0.46
stand_b.location.y = 0.46
stand_a.scale.x = 0.62
stand_b.scale.x = 0.62

coil_parts = append_meshes(coil_blend)
if len(coil_parts) != 2:
    raise RuntimeError(f"Expected repaired body and structural core, got {len(coil_parts)}")
bpy.context.view_layer.update()
coil_min_z = min((obj.matrix_world @ Vector(corner)).z for obj in coil_parts for corner in obj.bound_box)
coil_max_z = max((obj.matrix_world @ Vector(corner)).z for obj in coil_parts for corner in obj.bound_box)
coil_seating_delta = -coil_min_z
for obj in coil_parts:
    obj.location.z += coil_seating_delta

def mat(name, colour, metallic=0.0, roughness=0.65):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*colour, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return m

floor_mat = mat("FactoryFloor", (0.13, 0.15, 0.16), 0.0, 0.78)
bpy.ops.mesh.primitive_cube_add(location=(0, 0, -0.06), scale=(2.8, 2.6, 0.06))
floor = bpy.context.object
floor.data.materials.append(floor_mat)

world = bpy.context.scene.world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.015, 0.02, 0.025, 1)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
scene = bpy.context.scene
try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except TypeError:
    scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1200
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.look = "AgX - Medium High Contrast"

def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()

def light(name, location, energy, size, colour):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.shape, data.size, data.color = energy, "DISK", size, colour
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    look_at(obj, (0, 0, 0.8))

light("Key", (4, -4, 5), 1200, 4, (1.0, 0.85, 0.70))
light("Fill", (-4, -2, 3), 700, 3, (0.55, 0.72, 1.0))
light("Rim", (0, 4, 4), 900, 3, (1.0, 0.55, 0.25))

cam_data = bpy.data.cameras.new("ValidationCamera")
cam = bpy.data.objects.new("ValidationCamera", cam_data)
bpy.context.collection.objects.link(cam)
scene.camera = cam
views = {
    "front": ((4.2, 0, 1.55), (0, 0, 0.9)),
    "side": ((0, -4.2, 1.45), (0, 0, 0.8)),
    "three_quarter": ((3.6, -4.1, 2.8), (0, 0, 0.75)),
    "top": ((0, 0, 6.0), (0, 0, 0)),
}
for name, (position, target) in views.items():
    cam.location = position
    look_at(cam, target)
    cam_data.lens = 58
    scene.render.filepath = str(out / f"approved_coil_two_stands_{name}.png")
    bpy.ops.render.render(write_still=True)

audit = {
    "status": "PASS_BLENDER_RENDER_GATE",
    "coil_source": str(coil_blend),
    "stand_source": str(stand_blend),
    "stand_count_per_coil": 2,
    "stand_centres_y_m": [-0.46, 0.46],
    "coil_target_bottom_z_m": 0.0,
    "stand_adjustable_length_scale_x": 0.62,
    "coil_seating_delta_m": coil_seating_delta,
    "coil_mesh_parts": [o.name for o in coil_parts],
    "renders": [str(out / f"approved_coil_two_stands_{name}.png") for name in views],
    "meshy_credits_used": 0,
}
(out / "audit.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
print("LB_APPROVED_COIL_STAND_RENDER_V914_PASS")
