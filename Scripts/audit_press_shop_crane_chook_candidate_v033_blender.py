"""Independently re-import and fixed-render the v033 C-hook FBX."""

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SRC = ROOT / "SourceAssets/IndustrialKit/BridgeCrane/CHook/Candidate_v033"
FBX = SRC / "SM_LB_Crane_CHook_Candidate_v033.fbx"
OUT = ROOT / "Saved/ValidationScreenshots/SourceAssets/BridgeCrane/CHook/Candidate_v033"
AUDIT = ROOT / "Saved/Audits/press_shop_crane_chook_candidate_v033_source.json"
OUT.mkdir(parents=True, exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX), use_custom_normals=True)
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if len(meshes) != 1:
    raise RuntimeError(f"Expected one merged mesh, got {len(meshes)}")
hook = meshes[0]

# Neutral source stage; no project-map lighting can hide silhouette faults.
bpy.ops.mesh.primitive_plane_add(size=8.0, location=(0, 0, -0.76))
floor = bpy.context.object
floor_mat = bpy.data.materials.new("AuditFloor")
floor_mat.diffuse_color = (0.055, 0.065, 0.075, 1)
floor_mat.roughness = 0.72
floor.data.materials.append(floor_mat)
world = bpy.context.scene.world
if world is None:
    world = bpy.data.worlds.new("AuditWorld")
    bpy.context.scene.world = world
world.color = (0.012, 0.015, 0.020)
for name, location, energy, size in (
    ("Key", (3.5, -4.0, 4.2), 1300, 3.0),
    ("Fill", (-3.0, -2.0, 2.2), 850, 2.5),
    ("Rim", (-2.0, 3.0, 4.0), 1100, 2.0),
):
    data = bpy.data.lights.new(name, "AREA")
    data.energy, data.shape, data.size = energy, "DISK", size
    obj = bpy.data.objects.new(name, data)
    obj.location = location
    bpy.context.collection.objects.link(obj)
    obj.rotation_euler = (Vector((0, 0, 0.15)) - obj.location).to_track_quat("-Z", "Y").to_euler()

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 1200, 1200, 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.look = "AgX - Medium High Contrast"


def render(name, location, target=(0.05, 0.0, 0.05), lens=58):
    data = bpy.data.cameras.new(name)
    camera = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(camera)
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = lens
    scene.camera = camera
    path = OUT / f"lb_crane_chook_v033_{name.lower()}.png"
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera, do_unlink=True)
    return str(path)


images = [render("Side", (3.4, -4.4, 2.0)), render("Bore", (4.8, -0.3, 0.9), lens=62)]
dims = [round(float(value), 6) for value in hook.dimensions]
technical_pass = (2.35 <= dims[0] <= 2.48 and 0.50 <= dims[1] <= 0.62 and
                  1.95 <= dims[2] <= 2.08 and len(hook.material_slots) == 4)
payload = {
    "$schema": "line-boss/audit/bridge-crane-chook-candidate-v033-source/v1",
    "status": "SOURCE_FBX_GATE_PASS__VISUAL_REVIEW_REQUIRED__NOT_PROMOTED" if technical_pass else "SOURCE_FBX_GATE_FAIL__NOT_PROMOTED",
    "method": "Independent Blender 5.2 clean-scene FBX import plus fixed neutral-stage renders",
    "fbx": str(FBX), "mesh_count": len(meshes), "dimensions_m": dims,
    "material_slots": [slot.material.name for slot in hook.material_slots],
    "fixed_renders": images, "promotion_authorized": False,
}
AUDIT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if not technical_pass:
    raise RuntimeError(f"v033 source gate failed: {payload}")
print(f"LINE_BOSS_CRANE_CHOOK_V033_SOURCE_AUDIT_PASS dimensions_m={dims}")
