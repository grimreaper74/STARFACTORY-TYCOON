"""Build the isolated PR-009 trace-portal clearance source from immutable v002.

Run with Blender 5.2 in background mode, opening the preserved v002 production
source before this script.  The script never writes into Candidate_v002.
"""

from __future__ import annotations

import bpy
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Vector


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE_BLEND = REPO / "SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002/PR009_Source/CA_MW_PR009_AutomatedBlankStacker_ProductionSource_v002.blend"
OUTPUT_ROOT = REPO / "SourceAssets/PR009/AutomatedBlankStacker/TracePortalClearance_v001"
OUTPUT_BLEND = OUTPUT_ROOT / "PR009_Source/CA_MW_PR009_TracePortalClearance_ProductionSource_v001.blend"
OUTPUT_FBX = OUTPUT_ROOT / "PR009_Exports/SM_CA_MW_PR009_TracePortal_Clearance_01_v001.fbx"
OUTPUT_MANIFEST = OUTPUT_ROOT / "PR009_Audits/PR009_TRACE_PORTAL_CLEARANCE_SOURCE_v001.json"
OUTPUT_RENDERS = OUTPUT_ROOT / "PR009_Renders"

SOURCE_GROUP = "SM_CA_MW_PR009_TracePortal_01"
DERIVED_GROUP = "SM_CA_MW_PR009_TracePortal_Clearance_01_v001"
TARGET_CENTRE_Y_M = 3.15
WIDTH_FACTOR = 2.8 / 2.6
EXPECTED_COUNT = 11
EXPECTED_NAMES = {
    "PR009_07_TracePost_L",
    "PR009_07_TracePost_R",
    "PR009_07_TraceBeam",
    "PR009_07_TraceCamera_-0.82_Body",
    "PR009_07_TraceCamera_-0.82_Lens",
    "PR009_07_TraceCamera_0.0_Body",
    "PR009_07_TraceCamera_0.0_Lens",
    "PR009_07_TraceCamera_0.82_Body",
    "PR009_07_TraceCamera_0.82_Lens",
    "PR009_07_LightBar_-1.18",
    "PR009_07_LightBar_1.18",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def round_list(values, digits=6):
    return [round(float(value), digits) for value in values]


def object_record(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    lower = [min(corner[index] for corner in corners) for index in range(3)]
    upper = [max(corner[index] for corner in corners) for index in range(3)]
    return {
        "name": obj.name,
        "semantic": obj.get("semantic", ""),
        "location_m": round_list(obj.location),
        "rotation_euler_rad": round_list(obj.rotation_euler),
        "scale": round_list(obj.scale),
        "dimensions_m": round_list(obj.dimensions),
        "bounds_min_m": round_list(lower),
        "bounds_max_m": round_list(upper),
        "vertex_count": len(obj.data.vertices) if obj.type == "MESH" else 0,
    }


def group_bounds(objects):
    corners = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    lower = [min(corner[index] for corner in corners) for index in range(3)]
    upper = [max(corner[index] for corner in corners) for index in range(3)]
    return {
        "min_m": round_list(lower),
        "max_m": round_list(upper),
        "dimensions_m": round_list([upper[index] - lower[index] for index in range(3)]),
        "centre_m": round_list([(upper[index] + lower[index]) * 0.5 for index in range(3)]),
    }


def select_portal_objects():
    objects = sorted(
        [
            obj
            for obj in bpy.data.objects
            if obj.type == "MESH"
            and obj.get("module_id") == "07"
            and not bool(obj.get("collision_candidate", False))
        ],
        key=lambda obj: obj.name,
    )
    names = {obj.name for obj in objects}
    if len(objects) != EXPECTED_COUNT or names != EXPECTED_NAMES:
        raise RuntimeError(f"Unexpected trace-portal source membership: count={len(objects)} names={sorted(names)}")
    return objects


def author_derived_geometry(objects):
    before = group_bounds(objects)
    source_centre_y = before["centre_m"][1]
    delta_y = TARGET_CENTRE_Y_M - source_centre_y
    for obj in objects:
        if any(abs(float(value) - 1.0) > 0.000001 for value in obj.scale):
            raise RuntimeError(f"Source object has non-identity scale: {obj.name} {round_list(obj.scale)}")
        for vertex in obj.data.vertices:
            vertex.co.x *= WIDTH_FACTOR
        obj.location.x *= WIDTH_FACTOR
        obj.location.y += delta_y
        obj.data.update()
        obj.data.name = obj.name
        obj["export_asset"] = DERIVED_GROUP
        obj["derived_from_asset"] = SOURCE_GROUP
        obj["clear_opening_mm"] = 2800
        obj["portal_centre_y_mm"] = 3150
        obj["release_reason"] = "Full-size blank and source-authoritative gantry clearance"
    bpy.context.view_layer.update()
    return before, group_bounds(objects), delta_y


def export_fbx(objects):
    OUTPUT_FBX.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    bpy.context.scene.unit_settings.length_unit = "METERS"
    bpy.ops.export_scene.fbx(
        filepath=str(OUTPUT_FBX),
        use_selection=True,
        object_types={"MESH"},
        use_mesh_modifiers=True,
        use_custom_props=True,
        add_leaf_bones=False,
        bake_anim=False,
        axis_forward="-Y",
        axis_up="Z",
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE",
        use_space_transform=True,
        bake_space_transform=True,
        path_mode="AUTO",
        mesh_smooth_type="FACE",
    )
    production_script = SOURCE_BLEND.parent / "build_pr009_production_v002.py"
    spec = importlib.util.spec_from_file_location("pr009_v002_production", production_script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.canonicalize_fbx_v2(OUTPUT_FBX)
    bpy.ops.object.select_all(action="DESELECT")


def point_camera(camera, target):
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def render_evidence(objects):
    OUTPUT_RENDERS.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.025, 0.03, 0.035)

    camera_data = bpy.data.cameras.new("PR009_TracePortal_Clearance_Audit_Camera")
    camera = bpy.data.objects.new("PR009_TracePortal_Clearance_Audit_Camera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera_data.lens = 52
    scene.camera = camera

    views = [
        ("trace_portal_clearance_hero.png", (-5.2, 0.4, 3.8), (0.0, 3.15, 1.75)),
        ("trace_portal_clearance_service.png", (4.8, 0.8, 3.0), (0.0, 3.15, 1.65)),
        ("trace_portal_clearance_elevated.png", (-0.2, 0.1, 7.6), (0.0, 3.15, 1.15)),
    ]
    renders = []
    for filename, location, target in views:
        camera.location = location
        point_camera(camera, target)
        output = OUTPUT_RENDERS / filename
        scene.render.filepath = str(output)
        bpy.ops.render.render(write_still=True)
        renders.append({"file": output.name, "sha256": sha256(output), "bytes": output.stat().st_size})
    return renders


def validate(before, after, delta_y, objects):
    failures = []
    opening_m = 2.0 * (abs(next(obj.location.x for obj in objects if obj.name.endswith("TracePost_R"))) - next(obj.dimensions.x for obj in objects if obj.name.endswith("TracePost_R")) * 0.5)
    if abs(opening_m - 2.8) > 0.0005:
        failures.append(f"Clear opening {opening_m:.6f} m is not 2.800 m")
    if abs(after["centre_m"][1] - TARGET_CENTRE_Y_M) > 0.0005:
        failures.append(f"Portal centre Y {after['centre_m'][1]:.6f} m is not {TARGET_CENTRE_Y_M:.3f} m")
    if any(any(abs(value - 1.0) > 0.000001 for value in obj.scale) for obj in objects):
        failures.append("One or more derived objects has non-identity component scale")
    if after["max_m"][1] > 3.3555 or after["min_m"][1] < 2.9445:
        failures.append(f"Derived Y envelope is outside planned 2.945..3.355 m: {after['min_m'][1]}..{after['max_m'][1]}")
    if after["min_m"][0] > -1.565 or after["max_m"][0] < 1.565:
        failures.append("Derived beam width did not expand with the portal opening")
    return opening_m, failures


def main():
    if Path(bpy.data.filepath).resolve() != SOURCE_BLEND.resolve():
        raise RuntimeError(f"Open the immutable v002 source before running this script; got {bpy.data.filepath}")
    source_hash_before = sha256(SOURCE_BLEND)
    objects = select_portal_objects()
    before_records = [object_record(obj) for obj in objects]
    before, after, delta_y = author_derived_geometry(objects)
    opening_m, failures = validate(before, after, delta_y, objects)
    if failures:
        raise RuntimeError("Derived trace-portal validation failed: " + " | ".join(failures))

    OUTPUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND), check_existing=False)
    export_fbx(objects)
    renders = render_evidence(objects)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND), check_existing=False)

    source_hash_after = sha256(SOURCE_BLEND)
    if source_hash_after != source_hash_before:
        raise RuntimeError("Immutable Candidate_v002 source changed during derived build")

    manifest = {
        "$schema": "cairnwell/source/pr009-trace-portal-clearance/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "DIMENSIONED_DERIVED_TRACE_PORTAL_SOURCE_PASS__UNREAL_IMPORT_RUNTIME_COLLISION_AND_VISUAL_GATES_REQUIRED__NOT_PROMOTED",
        "source": {
            "blend": str(SOURCE_BLEND.relative_to(REPO)).replace("\\", "/"),
            "sha256_before": source_hash_before,
            "sha256_after": source_hash_after,
            "unchanged": source_hash_before == source_hash_after,
            "group": SOURCE_GROUP,
        },
        "derived": {
            "group": DERIVED_GROUP,
            "blend": str(OUTPUT_BLEND.relative_to(REPO)).replace("\\", "/"),
            "blend_sha256": sha256(OUTPUT_BLEND),
            "fbx": str(OUTPUT_FBX.relative_to(REPO)).replace("\\", "/"),
            "fbx_sha256": sha256(OUTPUT_FBX),
            "object_count": len(objects),
            "objects_before": before_records,
            "objects_after": [object_record(obj) for obj in objects],
            "bounds_before_m": before,
            "bounds_after_m": after,
            "source_y_delta_m": round(delta_y, 6),
            "width_factor": round(WIDTH_FACTOR, 9),
            "clear_opening_m": round(opening_m, 6),
            "identity_scale": True,
            "renders": renders,
        },
        "requirements": {
            "max_blank_mm": [1800, 2600],
            "target_clear_opening_mm": 2800,
            "blank_side_clearance_mm": 100,
            "authoritative_gantry_travel_mm": 2800,
            "portal_centre_y_mm": 3150,
            "unreal_world_x_delta_cm": -128.5,
        },
        "failures": [],
        "promotion_authorized": False,
        "pr010_started": False,
        "robots_modified": False,
    }
    OUTPUT_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": manifest["status"],
        "blend": str(OUTPUT_BLEND),
        "fbx": str(OUTPUT_FBX),
        "manifest": str(OUTPUT_MANIFEST),
        "object_count": len(objects),
        "clear_opening_m": opening_m,
        "bounds_after_m": after,
        "renders": len(renders),
    }, indent=2))


if __name__ == "__main__":
    main()
