"""Independent clean-scene FBX and render audit for PR-004 process context v001."""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
ROOT = REPO / "SourceAssets/PR004/ProcessContext_v001"
MANIFEST = ROOT / "pr004_process_context_candidate_v001_manifest.json"
AUDIT = REPO / "Saved/Audits/pr004_process_context_candidate_v001_independent.json"
RENDER_ROOT = REPO / "Saved/ValidationRenders/PR004/ProcessContext_v001_Independent"


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def import_fbx(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(path), use_custom_normals=True)
    return [obj for obj in bpy.data.objects if obj not in before and obj.type == "MESH"]


def combined_bounds(objects):
    corners = []
    for obj in objects:
        corners.extend(obj.matrix_world @ Vector(corner) for corner in obj.bound_box)
    mins = [min(point[axis] for point in corners) for axis in range(3)]
    maxs = [max(point[axis] for point in corners) for axis in range(3)]
    return [maxs[i] - mins[i] for i in range(3)]


def mesh_stats(objects):
    return {
        "objects": len(objects),
        "vertices": sum(len(obj.data.vertices) for obj in objects),
        "polygons": sum(len(obj.data.polygons) for obj in objects),
        "triangles": sum(sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons) for obj in objects),
    }


def material_names(objects):
    return sorted({slot.material.name for obj in objects for slot in obj.material_slots if slot.material})


def make_material(name, colour, metallic=0.0, roughness=0.8):
    value = bpy.data.materials.new(name)
    value.diffuse_color = (*colour, 1.0)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return value


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
records = manifest["modules"]
expected_ids = {
    "packaged_master_coil", "film_path_normal", "wound_film_roll",
    "compacted_plastic_bale", "compacted_band_bundle",
}
checks = {
    "manifest_candidate_not_promoted": manifest.get("status") == "SOURCE_CANDIDATE_NOT_PROMOTED",
    "exact_five_process_modules": len(records) == 5 and {record["id"] for record in records} == expected_ids,
    "all_fbx_exist": all(Path(record["fbx"]).exists() and Path(record["fbx"]).stat().st_size > 1000 for record in records),
    "all_sources_canonical_and_off_onedrive": all(
        str(Path(record["fbx"]).resolve()).lower().startswith(str(REPO.resolve()).lower())
        and "onedrive" not in str(Path(record["fbx"]).resolve()).lower()
        for record in records
    ),
    "all_asset_names_versioned": all(record["object"].endswith(("_v001", "_v003")) for record in records),
}

module_results = []
imported = {}
for record in records:
    reset_scene()
    fbx = Path(record["fbx"])
    objects = import_fbx(fbx)
    names = sorted(obj.name for obj in objects)
    bounds_m = combined_bounds(objects) if objects else [0.0, 0.0, 0.0]
    stats = mesh_stats(objects)
    materials = material_names(objects)
    transforms_identity = all(
        max(abs(value) for value in obj.location) < 1e-5
        and max(abs(value) for value in obj.rotation_euler) < 1e-5
        and max(abs(value - 1.0) for value in obj.scale) < 1e-5
        for obj in objects
    )
    module_results.append({
        "id": record["id"],
        "fbx": str(fbx),
        "objects": names,
        "bounds_xyz_m": [round(value, 5) for value in bounds_m],
        "mesh": stats,
        "materials": materials,
        "identity_transforms": transforms_identity,
    })
    imported[record["id"]] = module_results[-1]

checks.update({
    "all_fbx_reimport_as_mesh": all(result["mesh"]["objects"] >= 1 and result["mesh"]["triangles"] > 0 for result in module_results),
    "all_fbx_identity_transforms": all(result["identity_transforms"] for result in module_results),
    "all_fbx_have_material_slots": all(result["materials"] for result in module_results),
    "coil_dimensions_match_150x190x190_cm": all(
        abs(actual - expected) <= 0.025
        for actual, expected in zip(imported["packaged_master_coil"]["bounds_xyz_m"], (1.50, 1.90, 1.90))
    ),
    "film_path_is_full_155_cm_width": abs(imported["film_path_normal"]["bounds_xyz_m"][1] - 1.55) <= 0.04,
    "wound_film_is_full_width_sheet_shell": abs(imported["wound_film_roll"]["bounds_xyz_m"][1] - 1.55) <= 0.05
    and imported["wound_film_roll"]["mesh"]["triangles"] > 8000,
    "plastic_bale_is_layered_not_primitive": imported["compacted_plastic_bale"]["mesh"]["triangles"] > 4000
    and len(imported["compacted_plastic_bale"]["materials"]) >= 2,
    "band_bundle_is_compact_metal_geometry": imported["compacted_band_bundle"]["mesh"]["triangles"] > 5000
    and any("BandSteel" in name for name in imported["compacted_band_bundle"]["materials"]),
})

# Fresh independent renders.  Reimport all modules into one clean scene and
# place the master coil beside the process meshes in their authored frame.
reset_scene()
all_objects = {}
for record in records:
    objects = import_fbx(Path(record["fbx"]))
    all_objects[record["id"]] = objects
    if record["id"] == "packaged_master_coil":
        for obj in objects:
            obj.location = (-3.42, 0.0, 1.42)

floor = make_material("LB_PR004_Context_AuditFloor", (0.075, 0.078, 0.074), 0.0, 0.90)
bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, -0.05))
floor_obj = bpy.context.active_object
floor_obj.name = "VALIDATION_Floor"
floor_obj.dimensions = (9.2, 7.0, 0.10)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
floor_obj.data.materials.append(floor)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1500
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.world.color = (0.006, 0.008, 0.010)

for location, energy, size, colour in (
    ((-4.5, -4.8, 6.2), 1300.0, 3.2, (0.78, 0.86, 1.0)),
    ((3.8, -3.2, 4.8), 1050.0, 2.8, (1.0, 0.76, 0.55)),
    ((0.5, 4.0, 6.5), 1550.0, 3.8, (0.68, 0.80, 1.0)),
):
    data = bpy.data.lights.new("AuditArea", "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    data.color = colour
    light = bpy.data.objects.new("AuditArea", data)
    bpy.context.collection.objects.link(light)
    light.location = location
    look_at(light, (0.0, 0.0, 1.0))

camera_data = bpy.data.cameras.new("AuditCamera")
camera = bpy.data.objects.new("AuditCamera", camera_data)
bpy.context.collection.objects.link(camera)
scene.camera = camera

RENDER_ROOT.mkdir(parents=True, exist_ok=True)
views = (
    ("pr004_process_context_v001_oblique.png", (7.8, -9.2, 6.3), (-0.25, 0.0, 1.15), 56.0),
    ("pr004_process_context_v001_coil_close.png", (-6.6, -4.6, 3.7), (-3.42, 0.0, 1.42), 60.0),
    ("pr004_process_context_v001_waste_close.png", (5.2, -5.2, 3.5), (1.70, -1.20, 0.95), 62.0),
)
render_paths = []
for filename, location, target, lens in views:
    camera.location = location
    camera.data.lens = lens
    look_at(camera, target)
    path = RENDER_ROOT / filename
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    render_paths.append(path)

checks["three_fresh_independent_renders_written"] = all(path.exists() and path.stat().st_size > 10000 for path in render_paths)

technical_pass = all(checks.values())
result = {
    "$schema": "line-boss/audit/pr004-process-context-v001-independent-fbx/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "SOURCE_FBX_GATE_PASS__VISUAL_REVIEW_REQUIRED__CANDIDATE_NOT_PROMOTED" if technical_pass else "SOURCE_FBX_GATE_FAIL__CANDIDATE_NOT_PROMOTED",
    "independent_review": True,
    "method": "Independent clean-scene Blender 5.2 FBX re-import, geometry/material inspection and fresh fixed-camera render",
    "technical_pass": technical_pass,
    "checks": checks,
    "modules": module_results,
    "renders": [str(path) for path in render_paths],
    "visual_gate_passed": False,
    "promotion": "FORBIDDEN",
    "next_gate": "Inspect these renders, then import only into the quarantined Unreal PR-004 validation map and inspect fresh Unreal captures.",
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": result["status"], "audit": str(AUDIT), "renders": result["renders"]}, indent=2))
