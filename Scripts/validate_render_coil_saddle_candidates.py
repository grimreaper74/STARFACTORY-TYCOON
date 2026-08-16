"""Re-import and visually validate the packaged coil v003 / saddle v002 FBX.

This is a source-asset gate only. It does not start Unreal, create .uasset files
or alter the Press Shop population. Four fixed Blender renders and an audit JSON
are written so the candidate can be reviewed before any engine import.
"""

from pathlib import Path
import json
import math

import bpy
from mathutils import Vector


REPO = Path(__file__).resolve().parents[1]
COIL_FBX = REPO / "SourceAssets/IndustrialKit/MasterCoil/SM_LB_MasterCoil_Candidate_v003.fbx"
SADDLE_FBX = REPO / "SourceAssets/IndustrialKit/CoilSaddle/SM_LB_CoilSaddle_Candidate_v002.fbx"
OUT = REPO / "Saved/ValidationRenders/IndustrialKit/CoilSaddleCandidates_v003"
AUDIT = REPO / "Saved/Audits/coil_saddle_candidates_fbx_validation_v003.json"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def import_fbx(path):
    bpy.ops.object.select_all(action="DESELECT")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_props=True)
    objects = [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]
    if not objects:
        raise RuntimeError(f"No mesh imported from {path}")
    if len(objects) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objects:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = objects[0]
        bpy.ops.object.join()
        objects = [bpy.context.active_object]
    return objects[0]


def material(name, colour, metallic=0.0, roughness=0.6):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*colour, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def box(name, location, dimensions, mat):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("Studio edge", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 2
    return obj


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def camera(name, location, target, lens=58.0, ortho=None):
    data = bpy.data.cameras.new(name + "_Data")
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    data.lens = lens
    if ortho is not None:
        data.type = "ORTHO"
        data.ortho_scale = ortho
    look_at(obj, target)
    return obj


def area_light(name, location, energy, size, colour, target):
    data = bpy.data.lights.new(name + "_Data", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = colour
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)
    return obj


def bounds_world(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
    maximum = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
    return minimum, maximum


def stats(obj):
    triangles = sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons)
    minimum, maximum = bounds_world(obj)
    dimensions = maximum - minimum
    custom = {}
    for key in obj.keys():
        if key != "_RNA_UI":
            value = obj[key]
            if isinstance(value, (str, int, float, bool)):
                custom[key] = value
    return {
        "name": obj.name,
        "bounds_min_xyz_m": [round(v, 6) for v in minimum],
        "bounds_max_xyz_m": [round(v, 6) for v in maximum],
        "bounds_xyz_mm": [round(v * 1000.0, 3) for v in dimensions],
        "vertices": len(obj.data.vertices),
        "polygons": len(obj.data.polygons),
        "triangles": triangles,
        "materials": [slot.material.name for slot in obj.material_slots if slot.material],
        "custom_properties": custom,
    }


def render(scene, cam, filename):
    scene.camera = cam
    scene.render.filepath = str(OUT / filename)
    bpy.ops.render.render(write_still=True)


if not COIL_FBX.exists() or not SADDLE_FBX.exists():
    raise RuntimeError("Candidate FBX files are missing; run both source generators first")

OUT.mkdir(parents=True, exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)
clear_scene()
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1200
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
scene.render.image_settings.color_mode = "RGBA"
scene.render.resolution_percentage = 100
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
scene.view_settings.exposure = -0.35

scene.world.color = (0.010, 0.013, 0.017)
world = scene.world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.010, 0.013, 0.018, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.16

coil = import_fbx(COIL_FBX)
coil.name = "VALIDATION_MasterCoil_v003"
saddle = import_fbx(SADDLE_FBX)
saddle.name = "VALIDATION_CoilSaddle_v002"

# Preserve raw FBX evidence before assembling the two meshes.
coil_raw = stats(coil)
saddle_raw = stats(saddle)

saddle.location = (0.0, 0.0, 0.0)
coil.location = (0.0, 0.0, 1.47)
bpy.context.view_layer.update()

concrete = material("LB_Validation_Concrete", (0.115, 0.125, 0.135), 0.0, 0.78)
backdrop = material("LB_Validation_Backdrop", (0.025, 0.030, 0.036), 0.05, 0.72)
yellow = material("LB_Validation_FloorLine", (0.55, 0.30, 0.018), 0.15, 0.62)
floor = box("ValidationFloor", (0.0, 0.0, -0.075), (7.5, 6.0, 0.15), concrete)
box("ValidationBackWall", (0.0, 2.80, 2.20), (7.5, 0.12, 4.55), backdrop)
box("ValidationFloorLine_Left", (-1.65, 0.0, 0.008), (0.045, 4.5, 0.018), yellow)
box("ValidationFloorLine_Right", (1.65, 0.0, 0.008), (0.045, 4.5, 0.018), yellow)

area_light("Key_Area", (3.2, -3.5, 5.4), 1000.0, 4.0, (1.0, 0.84, 0.67), (0.0, 0.0, 1.1))
area_light("Fill_Area", (-3.2, -1.2, 3.2), 550.0, 3.0, (0.54, 0.68, 1.0), (0.0, 0.0, 1.0))
area_light("Rim_Area", (0.0, 2.4, 4.5), 800.0, 2.8, (1.0, 0.52, 0.22), (0.0, 0.0, 1.2))
area_light("Face_Fill", (4.2, 0.0, 3.1), 340.0, 2.4, (0.72, 0.82, 1.0), (0.0, 0.0, 1.35))

cam_assembly = camera("CAM_AssemblyThreeQuarter", (4.55, -5.35, 3.35), (0.0, 0.0, 1.02), lens=60.0)
cam_face = camera("CAM_FlatFace", (4.25, 0.0, 1.47), (0.0, 0.0, 1.47), lens=66.0)
cam_packaging = camera("CAM_PackagingDetail", (3.45, -3.05, 2.85), (0.0, 0.0, 1.45), lens=74.0)
cam_saddle = camera("CAM_SaddleOnly", (3.75, -4.15, 2.45), (0.0, 0.0, 0.36), lens=62.0)

render(scene, cam_assembly, "coil_v003_on_saddle_v002_three_quarter.png")
render(scene, cam_face, "coil_v003_flat_face.png")
render(scene, cam_packaging, "coil_v003_packaging_detail.png")
coil.hide_render = True
render(scene, cam_saddle, "saddle_v002_three_quarter.png")
coil.hide_render = False

coil_dims = coil_raw["bounds_xyz_mm"]
saddle_dims = saddle_raw["bounds_xyz_mm"]
checks = {
    "coil_width_1500_mm": abs(coil_dims[0] - 1500.0) <= 1.0,
    "coil_od_y_1900_mm": abs(coil_dims[1] - 1900.0) <= 1.0,
    "coil_od_z_1900_mm": abs(coil_dims[2] - 1900.0) <= 1.0,
    "coil_opaque_material_slots_present": len(coil_raw["materials"]) >= 8,
    "coil_custom_metadata_survived_fbx": coil_raw["custom_properties"].get("clear_bore_mm") == 610,
    "saddle_floor_anchors_metadata": saddle_raw["custom_properties"].get("floor_anchor_count") == 8,
    "saddle_not_blue_primary_finish": any("FrameCharcoal" in name for name in saddle_raw["materials"]),
    "saddle_width_exceeds_coil_width": saddle_dims[0] > coil_dims[0],
}

result = {
    "status": "CANDIDATES_NOT_PROMOTED",
    "validation_method": "Blender 5.2 FBX re-import plus fixed-camera Eevee renders",
    "source_files": {"coil_fbx": str(COIL_FBX), "saddle_fbx": str(SADDLE_FBX)},
    "fbx_bytes": {"coil": COIL_FBX.stat().st_size, "saddle": SADDLE_FBX.stat().st_size},
    "coil_fbx_reimport": coil_raw,
    "saddle_fbx_reimport": saddle_raw,
    "checks": checks,
    "all_technical_source_checks_pass": all(checks.values()),
    "renders": [
        str(OUT / "coil_v003_on_saddle_v002_three_quarter.png"),
        str(OUT / "coil_v003_flat_face.png"),
        str(OUT / "coil_v003_packaging_detail.png"),
        str(OUT / "saddle_v002_three_quarter.png"),
    ],
    "scope_limit": "No Unreal import, runtime gate, population edit or promotion performed.",
}
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"LINE_BOSS_COIL_SADDLE_FBX_VALIDATION_PASS checks={checks} audit={AUDIT}")
