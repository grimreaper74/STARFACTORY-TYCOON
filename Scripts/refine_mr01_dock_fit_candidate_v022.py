"""Create MR01 v022 by correcting only the v014 side-bumper axis regression."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector


EXPECTED_SOURCE_SHA256 = "A895A80D1912D21523266C09040DE90B3097A8BD50C8B9FA703CEE4AC6AE747C"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def bounds_mm(obj: bpy.types.Object) -> dict:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(point[i] for point in points) * 1000.0 for i in range(3)]
    maximum = [max(point[i] for point in points) * 1000.0 for i in range(3)]
    return {
        "min": [round(value, 3) for value in minimum],
        "max": [round(value, 3) for value in maximum],
        "size": [round(maximum[i] - minimum[i], 3) for i in range(3)],
    }


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 3:
        raise SystemExit("Usage: -- output_v022.blend audit.json render.png")
    output = Path(args[0]).resolve()
    audit_path = Path(args[1]).resolve()
    render_path = Path(args[2]).resolve()
    source = Path(bpy.data.filepath).resolve()
    source_hash = sha256(source)
    if source_hash != EXPECTED_SOURCE_SHA256:
        raise RuntimeError(f"Refusing unexpected MR01 source: {source_hash}")

    names = ("SM_LB_MR01_BumperSide_L", "SM_LB_MR01_BumperSide_R")
    bumpers = [bpy.data.objects.get(name) for name in names]
    if any(obj is None for obj in bumpers):
        raise RuntimeError(f"Missing side bumper objects: {[name for name, obj in zip(names, bumpers) if obj is None]}")
    before = {obj.name: bounds_mm(obj) for obj in bumpers}
    before_locations = {obj.name: [round(value, 9) for value in obj.location] for obj in bumpers}
    before_rotations = {obj.name: [round(value, 9) for value in obj.rotation_euler] for obj in bumpers}
    before_materials = {obj.name: [slot.material.name if slot.material else None for slot in obj.material_slots] for obj in bumpers}

    # v014 called resize(length=42,width=1220,height=64), turning the intended
    # longitudinal rails across CFR Y. Restore the intended 1220 x 42 x 64 mm
    # orientation while preserving centre, rotation, material and every other object.
    for obj in bumpers:
        obj.dimensions = (0.042, 1.220, 0.064)  # Blender XYZ = CFR Y, -X, Z.
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.select_set(False)
        obj["lb_v022_fix"] = "restore intended CFR 1220x42x64 mm longitudinal side bumper"

    after = {obj.name: bounds_mm(obj) for obj in bumpers}
    failures = []
    for obj in bumpers:
        if any(abs(a - b) > 1e-9 for a, b in zip(obj.location, before_locations[obj.name])):
            failures.append(f"location changed: {obj.name}")
        if any(abs(a - b) > 1e-9 for a, b in zip(obj.rotation_euler, before_rotations[obj.name])):
            failures.append(f"rotation changed: {obj.name}")
        mats = [slot.material.name if slot.material else None for slot in obj.material_slots]
        if mats != before_materials[obj.name]:
            failures.append(f"material changed: {obj.name}")
        if any(abs(value - 1.0) > 1e-6 for value in obj.scale):
            failures.append(f"non-unit scale: {obj.name}")
        if any(abs(a - b) > 1.0 for a, b in zip(after[obj.name]["size"], [42.0, 1220.0, 64.0])):
            failures.append(f"corrected Blender-size mismatch: {obj.name}: {after[obj.name]['size']}")

    physical_collections = {
        "10_LB_RP01_EXACT_SHARED_LINKED", "20_LB_MR01_STATIC", "21_LB_MR01_MOVING",
        "22_LB_MR01_ARM_SKELETAL", "24_LB_MR01_FLEXIBLE_DRESS_CANDIDATE",
        "25_LB_MR01_V013_INSTALLED_TOOLS", "28_LB_MR01_V014_VISUAL_REWORK",
    }
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH" and physical_collections.intersection(c.name for c in obj.users_collection)]
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    minimum = [min(point[i] for point in points) * 1000.0 for i in range(3)]
    maximum = [max(point[i] for point in points) * 1000.0 for i in range(3)]
    physical_bounds = {
        "min_blender_mm": [round(value, 3) for value in minimum],
        "max_blender_mm": [round(value, 3) for value in maximum],
        "size_blender_mm": [round(maximum[i] - minimum[i], 3) for i in range(3)],
        "cfr_interpretation": "Blender X=CFR Y width; Blender Y=-CFR X length; Blender Z=CFR Z height",
    }
    if physical_bounds["size_blender_mm"][0] > 940.0:
        failures.append(f"travel width still exceeds authority tolerance: {physical_bounds['size_blender_mm'][0]}")

    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.scene["lb_candidate"] = "LB_MR01_DOCK_FIT_CANDIDATE_V022"
    bpy.context.scene["lb_promotion_authorized"] = False
    bpy.ops.wm.save_as_mainfile(filepath=str(output))

    render_path.parent.mkdir(parents=True, exist_ok=True)
    camera = bpy.data.objects.get("CAM_MR01_V013_Stowed")
    if camera:
        scene = bpy.context.scene
        scene.camera = camera
        scene.render.filepath = str(render_path)
        scene.render.resolution_x = 1280
        scene.render.resolution_y = 720
        scene.render.resolution_percentage = 100
        scene.render.image_settings.file_format = "PNG"
        bpy.ops.render.render(write_still=True)
    else:
        failures.append("missing retained stowed review camera")

    payload = {
        "$schema": "cairnwell/audit/mr01-dock-fit-candidate-v022/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__TWO_SIDE_BUMPER_AXIS_REGRESSION_CORRECTED__UNREAL_RUNTIME_AND_VISUAL_GATES_OPEN__NOT_PROMOTED" if not failures else "FAIL__V022_SOURCE_GATE",
        "source_v020": str(source),
        "source_v020_sha256": source_hash,
        "output_v022": str(output),
        "output_v022_sha256": sha256(output),
        "changed_object_count": 2,
        "changed_objects": list(names),
        "before_bounds_blender_mm": before,
        "after_bounds_blender_mm": after,
        "physical_bounds_after": physical_bounds,
        "dock_portal_width_mm": 1260.0,
        "lateral_clearance_each_side_mm": round((1260.0 - physical_bounds["size_blender_mm"][0]) / 2.0, 3),
        "fit_interpretation": "Corrected 930 mm MR01 travel width fits the v002 1260 mm portal; full combined mesh/sweep proof remains required.",
        "failures": failures,
        "holds": [
            "Fresh Unreal import must be non-overwriting and v021 runtime/save/authority behavior must regress green.",
            "Actual combined dock/robot collision and moving service sweeps remain open.",
            "Visual quality remains on hold and no promotion is authorised.",
        ],
        "promotion_authorized": False,
    }
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "physical_bounds": physical_bounds, "failures": failures}, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
