"""Export the shared HMI as a small, pivot-safe Unreal module set.

The source contains many intentionally detailed Blender objects. Unreal should
not receive 178 unrelated scene meshes, so this exporter combines the static
cabinet while retaining only parts that need independent interaction, material
animation or movement.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def arguments():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    return parser.parse_args(argv)


def descendants(parent):
    return {child for child in parent.children_recursive if child.type == "MESH"}


def combined_copy(name, sources):
    bpy.ops.object.select_all(action="DESELECT")
    copies = []
    for source in sorted(sources, key=lambda item: item.name):
        duplicate = source.copy()
        duplicate.data = source.data.copy()
        duplicate.animation_data_clear()
        duplicate.parent = None
        duplicate.matrix_world = source.matrix_world.copy()
        bpy.context.collection.objects.link(duplicate)
        duplicate.select_set(True)
        copies.append(duplicate)
    if not copies:
        raise RuntimeError(f"Export group {name} is empty")
    bpy.context.view_layer.objects.active = copies[0]
    bpy.ops.object.join()
    result = bpy.context.view_layer.objects.active
    result.name = name
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
    return result


def object_bounds_cm(obj):
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    minimum = [min(point[index] for point in corners) * 100.0 for index in range(3)]
    maximum = [max(point[index] for point in corners) * 100.0 for index in range(3)]
    return {
        "min_cm": [round(value, 3) for value in minimum],
        "max_cm": [round(value, 3) for value in maximum],
        "size_cm": [round(maximum[index] - minimum[index], 3) for index in range(3)],
    }


def export_fbx(obj, output_path):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(output_path),
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Y",
        axis_up="Z",
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        use_tspace=True,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="COPY",
        embed_textures=True,
    )


def main():
    args = arguments()
    output_dir = Path(args.output_dir).resolve()
    manifest_path = Path(args.manifest).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.context.view_layer.update()

    all_meshes = set(bpy.context.scene.objects)
    all_meshes = {obj for obj in all_meshes if obj.type == "MESH"}
    rear_mover = bpy.data.objects.get("PR-005_HMIRearServiceDoorMover")
    if rear_mover is None:
        raise RuntimeError("Rear service-door mover is missing")

    named_groups = {
        "SM_LB_HMI_RearServiceDoor": descendants(rear_mover),
        "SM_LB_HMI_DisplaySurface": {bpy.data.objects["PR-005_HMILiveDisplaySurface"]},
        "SM_LB_HMI_ControlPower": {bpy.data.objects["PR-005_HMIControlPowerKey"]},
        "SM_LB_HMI_ModeSelector": {bpy.data.objects["PR-005_HMIModeSelector"]},
        "SM_LB_HMI_ResetButton": {bpy.data.objects["PR-005_HMIButton_01"]},
        "SM_LB_HMI_CycleStartButton": {bpy.data.objects["PR-005_HMIButton_02"]},
        "SM_LB_HMI_EmergencyStop": {
            bpy.data.objects["PR-005_HMIEStop"],
            bpy.data.objects["PR-005_HMIEStopGuard"],
        },
        "SM_LB_HMI_StackRed": {bpy.data.objects["PR-005_HMIStackLight_01"]},
        "SM_LB_HMI_StackAmber": {bpy.data.objects["PR-005_HMIStackLight_02"]},
        "SM_LB_HMI_StackGreen": {bpy.data.objects["PR-005_HMIStackLight_03"]},
    }
    reserved = set().union(*named_groups.values())
    named_groups["SM_LB_HMI_CabinetBody"] = all_meshes - reserved

    records = []
    for asset_name, source_objects in named_groups.items():
        combined = combined_copy(asset_name, source_objects)
        output_path = output_dir / f"{asset_name}.fbx"
        export_fbx(combined, output_path)
        records.append(
            {
                "asset_name": asset_name,
                "fbx": str(output_path),
                "source_objects": sorted(obj.name for obj in source_objects),
                "source_mesh_count": len(source_objects),
                "material_slots": [slot.material.name if slot.material else None for slot in combined.material_slots],
                "bounds": object_bounds_cm(combined),
            }
        )
        bpy.data.objects.remove(combined, do_unlink=True)

    manifest = {
        "asset_id": "IND-HMI-001",
        "revision": "shared_operator_hmi_v003_ue001",
        "source_blend": bpy.data.filepath,
        "status": "UNREAL_CANDIDATE_NOT_PROMOTED",
        "units": "centimetres",
        "assembly_origin": "centre of plinth footprint at finished-floor level",
        "cabinet_contract_cm": {"width": 60.0, "depth": 46.0, "console_height": 128.0, "overall_height": 159.0},
        "screen_contract": "17-inch 4:3 display on 20-degree downward-sloped operator face",
        "modules": records,
        "interaction_sockets_cm": {
            "operator": [0.0, -95.0, 102.0],
            "rear_service": [53.0, 0.0, 62.0],
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"LINE_BOSS_HMI_UE_EXPORT_PASS modules={len(records)} manifest={manifest_path}")


if __name__ == "__main__":
    main()
