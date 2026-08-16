"""Export a closed-state visual intake mesh for MR01 v004 or CR01 v007.

This is deliberately an isolated Unreal visual/scale/collision intake package,
not the final moving-component runtime export. Exact sockets and authorized
pivots are recorded in the manifest for the later componentized successor.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Vector


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def bounds_mm(obj: bpy.types.Object) -> dict:
    points = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(p[i] for p in points) * 1000.0 for i in range(3)]
    maximum = [max(p[i] for p in points) * 1000.0 for i in range(3)]
    return {
        "min": [round(v, 3) for v in minimum],
        "max": [round(v, 3) for v in maximum],
        "size": [round(maximum[i] - minimum[i], 3) for i in range(3)],
    }


def eligible(obj: bpy.types.Object) -> bool:
    return (
        obj.type in {"MESH", "CURVE", "FONT"}
        and not obj.name.startswith(("REF_", "SCK_", "PVT_", "UCX_", "REVIEW_", "STAGE_"))
        and not obj.hide_render
    )


def duplicate_for_export(objects: list[bpy.types.Object], package_name: str) -> bpy.types.Object:
    staging = bpy.data.collections.new(f"EXPORT_STAGE_{package_name}")
    bpy.context.scene.collection.children.link(staging)
    copies = []
    seen = set()
    for source in objects:
        if source.name in seen or not eligible(source):
            continue
        seen.add(source.name)
        world = source.matrix_world.copy()
        clone = source.copy()
        if source.data:
            clone.data = source.data.copy()
        clone.parent = None
        staging.objects.link(clone)
        clone.matrix_world = world
        copies.append(clone)
    if not copies:
        raise RuntimeError("No eligible visible objects for intake export")

    bpy.ops.object.select_all(action="DESELECT")
    converted = []
    for obj in copies:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        if obj.type != "MESH":
            bpy.ops.object.convert(target="MESH")
            obj = bpy.context.view_layer.objects.active
        converted.append(obj)
        obj.select_set(False)

    for obj in converted:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = converted[0]
    bpy.ops.object.join()
    result = bpy.context.view_layer.objects.active
    result.name = package_name
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    return result


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2 or args[0].lower() not in {"mr01", "cr01"}:
        raise SystemExit("Usage: -- mr01|cr01 output_directory")
    mode = args[0].lower()
    output = Path(args[1]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    source = Path(bpy.data.filepath).resolve()

    collection_names = ["LB_RP01_DOCK_SHARED"]
    if mode == "mr01":
        collection_names += ["30_LB_MR01_DOCK_STATIC", "31_LB_MR01_DOCK_MOVING", "32_LB_MR01_DOCK_TOOLS"]
        expected_root = "ROOT_LB_MR01_SERVICE_DOCK_V005" if "ROOT_LB_MR01_SERVICE_DOCK_V005" in bpy.data.objects else "ROOT_LB_MR01_SERVICE_DOCK_V004"
        package_name = "SM_LB_MR01_ServiceDock_ClosedIntake_v002" if expected_root.endswith("V005") else "SM_LB_MR01_ServiceDock_ClosedIntake_v001"
    else:
        collection_names += ["20_LB_CR01_DOCK_STATIC", "21_LB_CR01_DOCK_MOVING"]
        expected_root = "ROOT_LB_CR01_SERVICE_DOCK_V008" if "ROOT_LB_CR01_SERVICE_DOCK_V008" in bpy.data.objects else "ROOT_LB_CR01_SERVICE_DOCK_V007"
        package_name = "SM_LB_CR01_ServiceDock_ClosedIntake_v002" if expected_root.endswith("V008") else "SM_LB_CR01_ServiceDock_ClosedIntake_v001"
    if expected_root not in bpy.data.objects:
        raise RuntimeError(f"Unexpected source; missing {expected_root}")
    missing = [name for name in collection_names if name not in bpy.data.collections]
    if missing:
        raise RuntimeError(f"Missing export collections: {missing}")

    sources = [obj for name in collection_names for obj in bpy.data.collections[name].objects]
    package = duplicate_for_export(sources, package_name)
    package_bounds = bounds_mm(package)
    if package_bounds["size"][0] > 2601.0:
        raise RuntimeError(f"Package exceeds authorized 2600 mm width: {package_bounds}")

    bpy.ops.object.select_all(action="DESELECT")
    package.select_set(True)
    bpy.context.view_layer.objects.active = package
    fbx = output / f"{package_name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(fbx), use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True,
        add_leaf_bones=False, bake_anim=False, mesh_smooth_type="FACE",
    )

    socket_names = ["SCK_DockDatum", "SCK_ChargeContact_L", "SCK_ChargeContact_R", "SCK_NetworkContact"]
    if mode == "cr01":
        socket_names += ["SCK_WaterFill", "SCK_DirtyExtract"]
    pivot_names = [] if mode == "cr01" else ["PVT_DockCalibrationProbe", "PVT_DockToolRackDoor", "PVT_DockWasteDrawer"]
    manifest = {
        "$schema": f"cairnwell/export/service-dock-closed-intake-v001/{mode}/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__CLOSED_VISUAL_INTAKE_EXPORT__COMPONENTIZED_RUNTIME_EXPORT_OPEN__NOT_PROMOTED",
        "mode": mode,
        "source_blend": str(source),
        "source_blend_sha256": sha256(source),
        "source_collections": collection_names,
        "source_object_count_before_dedup": len(sources),
        "package_name": package_name,
        "package_bounds_blender_mm": package_bounds,
        "material_slots": [slot.material.name if slot.material else None for slot in package.material_slots],
        "fbx": str(fbx),
        "fbx_sha256": sha256(fbx),
        "sockets_blender_mm": {name: [round(v * 1000.0, 3) for v in bpy.data.objects[name].matrix_world.translation] for name in socket_names},
        "authorized_pivots_blender_mm": {name: [round(v * 1000.0, 3) for v in bpy.data.objects[name].matrix_world.translation] for name in pivot_names},
        "holds": [
            "Closed-state visual intake only; moving parts are intentionally not yet componentized",
            "Unreal import, material, scale, collision and fixed-camera gates remain open",
            "No Press Shop map placement is authorized"
        ],
        "promotion_authorized": False,
    }
    manifest_path = output / f"{package_name}_EXPORT_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "fbx": str(fbx), "bounds_mm": package_bounds, "materials": len(package.material_slots)}, indent=2))


if __name__ == "__main__":
    main()
