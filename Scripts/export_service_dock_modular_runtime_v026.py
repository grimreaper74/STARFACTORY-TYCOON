"""Export verified service-dock modules without modifying the authored .blend.

MR01 exports its closed/static body and three independently placeable movers at
the source-authorised pivots. CR01 currently has no authorised moving pivots, so
its service equipment remains in the static package rather than receiving
invented animation. The manifest is the authority for Unreal placement.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


EXCLUDED_PREFIXES = ("REF_", "SCK_", "PVT_", "UCX_", "REVIEW_", "STAGE_", "ROOT_")
COMMON_MOVERS = {
    "SM_LB_RP01_DockIsolationDoor",
    "SM_LB_RP01_DockRearServiceDoor_L",
    "SM_LB_RP01_DockRearServiceDoor_R",
}
MR_MOVERS = {
    "calibration_probe": {
        "objects": {"SM_LB_MR01_DockCalibrationProbe"},
        "pivot": "PVT_DockCalibrationProbe",
        "motion": {"type": "linear", "axis_source": "X", "travel_mm": 180.0},
    },
    "tool_rack_door": {
        "objects": {"SM_LB_MR01_DockToolRackDoor"},
        "pivot": "PVT_DockToolRackDoor",
        "motion": {"type": "rotation", "axis_source": "Z", "range_deg": [0.0, 100.0]},
    },
    "waste_drawer": {
        "objects": {"SM_LB_MR01_DockWasteDrawer", "SM_LB_MR01_DockWasteDrawerInsert"},
        "pivot": "PVT_DockWasteDrawer",
        "motion": {"type": "linear", "axis_source": "Y", "travel_mm": 450.0},
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def eligible(obj: bpy.types.Object) -> bool:
    return obj.type in {"MESH", "CURVE", "FONT"} and not obj.name.startswith(EXCLUDED_PREFIXES) and not obj.hide_render


def world_bounds_mm(objects: list[bpy.types.Object]) -> dict:
    points = [obj.matrix_world @ Vector(corner) for obj in objects if obj.type == "MESH" for corner in obj.bound_box]
    minimum = [min(point[i] for point in points) * 1000.0 for i in range(3)]
    maximum = [max(point[i] for point in points) * 1000.0 for i in range(3)]
    return {
        "min": [round(value, 3) for value in minimum],
        "max": [round(value, 3) for value in maximum],
        "size": [round(maximum[i] - minimum[i], 3) for i in range(3)],
    }


def export_component(name: str, sources: list[bpy.types.Object], pivot_world: Vector, output: Path) -> dict:
    sources = [obj for obj in sources if eligible(obj)]
    if not sources:
        raise RuntimeError(f"{name}: no eligible source objects")
    authored_bounds = world_bounds_mm(sources)
    staging = bpy.data.collections.new(f"EXPORT_STAGE_{name}")
    bpy.context.scene.collection.children.link(staging)
    clones = []
    for source in sources:
        clone = source.copy()
        if source.data:
            clone.data = source.data.copy()
        clone.parent = None
        staging.objects.link(clone)
        clone.matrix_world = Matrix.Translation(-pivot_world) @ source.matrix_world
        clones.append(clone)

    bpy.ops.object.select_all(action="DESELECT")
    meshes = []
    for clone in clones:
        clone.select_set(True)
        bpy.context.view_layer.objects.active = clone
        if clone.type != "MESH":
            bpy.ops.object.convert(target="MESH")
            clone = bpy.context.view_layer.objects.active
        meshes.append(clone)
        clone.select_set(False)
    for mesh in meshes:
        mesh.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.join()
    package = bpy.context.view_layer.objects.active
    package.name = name
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    fbx = output / f"{name}.fbx"
    bpy.ops.object.select_all(action="DESELECT")
    package.select_set(True)
    bpy.context.view_layer.objects.active = package
    bpy.ops.export_scene.fbx(
        filepath=str(fbx), use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True,
        add_leaf_bones=False, bake_anim=False, mesh_smooth_type="FACE",
    )
    return {
        "asset_name": name,
        "source_objects": sorted(obj.name for obj in sources),
        "source_object_count": len(sources),
        "pivot_blender_mm": [round(value * 1000.0, 3) for value in pivot_world],
        "authored_world_bounds_mm": authored_bounds,
        "fbx": str(fbx),
        "fbx_sha256": sha256(fbx),
    }


def main() -> None:
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) != 2 or args[0].lower() not in {"mr01", "cr01"}:
        raise SystemExit("usage: blender SOURCE.blend --python SCRIPT -- mr01|cr01 OUTPUT_DIR")
    mode = args[0].lower()
    output = Path(args[1]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    source = Path(bpy.data.filepath).resolve()

    variant_collection = "30_LB_MR01_DOCK_STATIC" if mode == "mr01" else "20_LB_CR01_DOCK_STATIC"
    moving_collection = "31_LB_MR01_DOCK_MOVING" if mode == "mr01" else "21_LB_CR01_DOCK_MOVING"
    tools_collection = "32_LB_MR01_DOCK_TOOLS" if mode == "mr01" else None
    required = ["LB_RP01_DOCK_SHARED", variant_collection, moving_collection]
    if tools_collection:
        required.append(tools_collection)
    missing = [name for name in required if name not in bpy.data.collections]
    if missing:
        raise RuntimeError(f"missing source collections: {missing}")

    explicitly_moving = set().union(*(spec["objects"] for spec in MR_MOVERS.values())) if mode == "mr01" else set()
    static_sources = []
    for collection_name in required:
        for obj in bpy.data.collections[collection_name].objects:
            if obj.name in COMMON_MOVERS or obj.name in explicitly_moving:
                continue
            if obj not in static_sources:
                static_sources.append(obj)
    # CR01 has no approved travel/pivots: retain all variant service hardware in the static visual.
    if mode == "cr01":
        for obj in bpy.data.collections[moving_collection].objects:
            if obj.name not in COMMON_MOVERS and obj not in static_sources:
                static_sources.append(obj)

    prefix = "MR01" if mode == "mr01" else "CR01"
    components = {
        "static": export_component(f"SM_LB_{prefix}_ServiceDock_Static_v026", static_sources, Vector((0, 0, 0)), output)
    }
    if components["static"]["authored_world_bounds_mm"]["size"][0] > 2601.0:
        raise RuntimeError("static package exceeds authorised 2600 mm width")

    if mode == "mr01":
        for key, spec in MR_MOVERS.items():
            pivot_obj = bpy.data.objects.get(spec["pivot"])
            if not pivot_obj:
                raise RuntimeError(f"missing authorised pivot {spec['pivot']}")
            sources = [bpy.data.objects[name] for name in spec["objects"]]
            item = export_component(f"SM_LB_MR01_ServiceDock_{key}_v026", sources, pivot_obj.matrix_world.translation.copy(), output)
            item["motion_authority"] = spec["motion"]
            item["pivot_object"] = spec["pivot"]
            components[key] = item

    sockets = ["SCK_DockDatum", "SCK_ChargeContact_L", "SCK_ChargeContact_R", "SCK_NetworkContact"]
    if mode == "cr01":
        sockets += ["SCK_WaterFill", "SCK_DirtyExtract"]
    manifest = {
        "$schema": f"cairnwell/export/service-dock-modular-runtime-v026/{mode}/v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS__MODULAR_EXPORT__UNREAL_IMPORT_AND_RUNTIME_GATES_OPEN__NOT_PROMOTED",
        "source_blend": str(source),
        "source_blend_sha256": sha256(source),
        "mode": mode,
        "components": components,
        "sockets_blender_mm": {
            name: [round(value * 1000.0, 3) for value in bpy.data.objects[name].matrix_world.translation]
            for name in sockets
        },
        "policy": {
            "common_door_motion": "TBC__EXCLUDED_FROM_RUNTIME_EXPORT",
            "cr01_service_motion": "TBC__NO_AUTHORISED_PIVOTS_OR_TRAVEL__STATIC_ONLY",
            "safe_restore": "CLOSED_AND_DEENERGISED_REQUIRED",
        },
        "promotion_authorized": False,
    }
    manifest_path = output / f"LB_{prefix}_ServiceDock_ModularRuntime_v026_EXPORT_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"status": manifest["status"], "manifest": str(manifest_path), "components": list(components)}, indent=2))


if __name__ == "__main__":
    main()
