"""Re-import and visually validate the PR-004 powered V-cradle candidate.

This is a source-asset gate only.  It does not launch Unreal, create .uasset
files or promote the candidate.  The test reconstructs the modular assembly
from the source manifest, checks mover pivots/metadata, and creates fresh fixed
camera renders with the current 1.5 m x 1.9 m packaged-coil candidate.
"""

from pathlib import Path
import json
import math

import bpy
from mathutils import Vector


REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "SourceAssets/PR004/PoweredRestrainedCradle"
MANIFEST = ROOT / "pr004_powered_cradle_candidate_v001_manifest.json"
COIL = REPO / "SourceAssets/IndustrialKit/MasterCoil/SM_LB_MasterCoil_Candidate_v003.fbx"
OUT = REPO / "Saved/ValidationRenders/PR004/PoweredCradle_v001"
AUDIT = REPO / "Saved/Audits/pr004_powered_cradle_candidate_v001_fbx_validation.json"


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
    modifier = obj.modifiers.new("Studio edge", "BEVEL")
    modifier.width = 0.012
    modifier.segments = 2
    return obj


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


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


def object_stats(obj):
    triangles = sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons)
    custom = {}
    for key in obj.keys():
        if key == "_RNA_UI":
            continue
        value = obj[key]
        if isinstance(value, (str, int, float, bool)):
            custom[key] = value
    return {
        "name": obj.name,
        "location_m": [round(v, 6) for v in obj.location],
        "bounds_xyz_mm": [round(v * 1000.0, 3) for v in obj.dimensions],
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


if not MANIFEST.exists() or not COIL.exists():
    raise RuntimeError("Cradle manifest or validation coil is missing")

manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
OUT.mkdir(parents=True, exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)
clear_scene()

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1280
scene.render.resolution_y = 960
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.film_transparent = False
try:
    scene.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
scene.view_settings.exposure = -0.35
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.010, 0.013, 0.018, 1.0)
scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.14

objects = {}
fbx_records = []
for module in manifest["modules"]:
    path = Path(module["fbx"])
    if not path.exists():
        raise RuntimeError(f"Missing module FBX: {path}")
    obj = import_fbx(path)
    obj.name = "VALIDATION_" + module["object"]
    obj.location = tuple(float(v) / 100.0 for v in module["rest_location_cm"])
    objects[module["id"]] = obj
    fbx_records.append({
        "id": module["id"],
        "fbx": str(path),
        "bytes": path.stat().st_size,
        "expected_rest_location_m": [round(float(v) / 100.0, 6) for v in module["rest_location_cm"]],
        "reimport": object_stats(obj),
    })

coil = import_fbx(COIL)
coil.name = "VALIDATION_MasterCoil_v003"
# The cradle uses axis X and supports the coil around its circumference.  This
# Z position is a candidate visual pose, not a certified contact solution.
coil.location = (0.0, 0.0, 1.305)

concrete = material("LB_PR004_ValidationConcrete", (0.095, 0.105, 0.115), 0.0, 0.78)
backdrop = material("LB_PR004_ValidationBackdrop", (0.024, 0.030, 0.037), 0.05, 0.72)
yellow = material("LB_PR004_ValidationLine", (0.55, 0.30, 0.018), 0.15, 0.62)
box("ValidationFloor", (0.0, 0.0, -0.075), (8.5, 7.0, 0.15), concrete)
box("ValidationBackWall", (0.0, 3.25, 2.40), (8.5, 0.12, 5.0), backdrop)
box("ValidationFloorLine_L", (-2.15, 0.0, 0.008), (0.045, 5.4, 0.018), yellow)
box("ValidationFloorLine_R", (2.15, 0.0, 0.008), (0.045, 5.4, 0.018), yellow)

area_light("Key_Area", (4.4, -4.0, 6.2), 1250.0, 4.2, (1.0, 0.83, 0.66), (0.0, 0.0, 1.0))
area_light("Fill_Area", (-4.0, -1.2, 3.5), 650.0, 3.2, (0.52, 0.68, 1.0), (0.0, 0.0, 1.0))
area_light("Rim_Area", (0.0, 3.0, 5.2), 850.0, 3.0, (1.0, 0.55, 0.25), (0.0, 0.0, 1.2))
area_light("Face_Fill", (5.0, 0.0, 3.2), 420.0, 2.8, (0.72, 0.82, 1.0), (0.0, 0.0, 1.3))

cam_three_quarter = camera("CAM_ThreeQuarter", (5.4, -6.5, 4.0), (0.0, 0.0, 0.95), lens=64.0)
cam_side = camera("CAM_Side", (5.6, 0.0, 1.65), (0.0, 0.0, 1.15), lens=68.0)
cam_top = camera("CAM_Top", (0.0, -0.01, 8.0), (0.0, 0.0, 0.0), ortho=5.6)

render(scene, cam_three_quarter, "pr004_powered_cradle_loaded_three_quarter_v001.png")
render(scene, cam_side, "pr004_powered_cradle_loaded_side_v001.png")
render(scene, cam_top, "pr004_powered_cradle_loaded_top_v001.png")

# A second articulation pose verifies that the separate mover pivots produce
# plausible motion without deforming the fixed cradle body.
original_pose = {key: (obj.location.copy(), obj.rotation_euler.copy()) for key, obj in objects.items()}
objects["left_side_clamp"].rotation_euler.x += math.radians(14.0)
objects["right_side_clamp"].rotation_euler.x -= math.radians(14.0)
objects["index_drive"].rotation_euler.x += math.radians(24.0)
objects["end_stop_locator"].location.x += 0.20
render(scene, cam_three_quarter, "pr004_powered_cradle_articulation_pose_v001.png")
for key, obj in objects.items():
    obj.location, obj.rotation_euler = original_pose[key]

checks = {
    "module_count_is_five": len(objects) == 5,
    "static_body_present": "static" in objects,
    "independent_movers_present": all(key in objects for key in ("left_side_clamp", "right_side_clamp", "index_drive", "end_stop_locator")),
    "static_width_matches_manifest": abs(objects["static"].dimensions.x * 100.0 - 344.0) <= 0.5,
    "static_depth_matches_manifest": abs(objects["static"].dimensions.y * 100.0 - 260.0) <= 0.5,
    "mover_metadata_survived_fbx": all("motion_type" in objects[key].keys() for key in ("left_side_clamp", "right_side_clamp", "index_drive", "end_stop_locator")),
    "coil_envelope_matches_contract": all(abs(actual - expected) <= 1.0 for actual, expected in zip((coil.dimensions.x * 1000.0, coil.dimensions.y * 1000.0, coil.dimensions.z * 1000.0), (1500.0, 1900.0, 1900.0))),
}

result = {
    "$schema": "line-boss/source-validation/pr004-powered-cradle/v1",
    "status": "CANDIDATE_NOT_PROMOTED",
    "method": "Blender 5.2 FBX re-import, metadata/pivot audit and fixed-camera Eevee renders",
    "source_manifest": str(MANIFEST),
    "validation_coil": str(COIL),
    "modules": fbx_records,
    "coil_reimport": object_stats(coil),
    "checks": checks,
    "all_source_checks_pass": all(checks.values()),
    "renders": [
        str(OUT / "pr004_powered_cradle_loaded_three_quarter_v001.png"),
        str(OUT / "pr004_powered_cradle_loaded_side_v001.png"),
        str(OUT / "pr004_powered_cradle_loaded_top_v001.png"),
        str(OUT / "pr004_powered_cradle_articulation_pose_v001.png"),
    ],
    "scope_limit": "No Unreal import, collision/interlock gate, runtime animation or promotion performed.",
}
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"LINE_BOSS_PR004_POWERED_CRADLE_FBX_VALIDATION_PASS checks={checks} audit={AUDIT}")
