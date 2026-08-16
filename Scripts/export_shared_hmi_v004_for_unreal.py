"""Export Blender HMI v004 into pivot-safe Unreal Modeling candidate modules."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def arguments():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--manifest", required=True)
    return parser.parse_args(argv)


def renderable_descendants(parent):
    return {child for child in parent.children_recursive if child.type in {"MESH", "CURVE", "FONT"}}


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
        bpy.context.view_layer.objects.active = duplicate
        duplicate.select_set(True)
        if duplicate.type != "MESH":
            bpy.ops.object.convert(target="MESH")
            duplicate = bpy.context.object
        duplicate.select_set(False)
        copies.append(duplicate)
    if not copies:
        raise RuntimeError(f"Export group {name} is empty")
    for duplicate in copies:
        duplicate.select_set(True)
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
    # Interchange 5.8 has a reproducible parser crash on a separated FBX that
    # still contains mixed n-gons.  Validate and triangulate the isolated copy
    # before export; the authored Blender model is never modified.
    obj.data.validate(clean_customdata=False)
    triangulate = obj.modifiers.new(name="UE_Interchange_Triangulate", type="TRIANGULATE")
    triangulate.quad_method = "BEAUTY"
    triangulate.ngon_method = "BEAUTY"
    bpy.ops.object.modifier_apply(modifier=triangulate.name)
    bpy.ops.export_scene.fbx(
        filepath=str(output_path), use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Y", axis_up="Z", use_mesh_modifiers=True,
        mesh_smooth_type="FACE", use_tspace=True, add_leaf_bones=False,
        bake_anim=False, path_mode="AUTO",
    )


def separate_by_material(obj):
    """Return mesh parts with one material assignment each.

    Geometry Script rebuilds are safest when a StaticMesh section has a
    single semantic material.  Separating here avoids losing per-face FBX
    material IDs during Unreal-native repair.
    """
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="MATERIAL")
    bpy.ops.object.mode_set(mode="OBJECT")
    return sorted(
        [item for item in bpy.context.selected_objects if item.type == "MESH"],
        key=lambda item: item.name,
    )


def material_name(obj):
    used = sorted({polygon.material_index for polygon in obj.data.polygons})
    for index in used:
        if index < len(obj.material_slots) and obj.material_slots[index].material:
            return obj.material_slots[index].material.name
    for slot in obj.material_slots:
        if slot.material:
            return slot.material.name
    return "HMI_charcoal_painted_steel"


def safe_suffix(value):
    value = re.sub(r"[^A-Za-z0-9]+", "_", value).strip("_")
    return value[:48] or "Default"


def get(*names):
    found = set()
    for name in names:
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Required v004 object is missing: {name}")
        found.add(obj)
    return found


def prefixed(prefix):
    return {obj for obj in bpy.context.scene.objects if obj.name.startswith(prefix) and obj.type in {"MESH", "CURVE", "FONT"}}


def main():
    args = arguments()
    output_dir = Path(args.output_dir).resolve()
    manifest_path = Path(args.manifest).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    root = bpy.data.objects.get("IND-HMI-001_SharedOperatorConsole")
    if root is None:
        raise RuntimeError("IND-HMI-001 v004 root is missing")

    all_renderables = renderable_descendants(root)
    door_root = bpy.data.objects.get("HMI_RearServiceDoor_Hinge")
    if door_root is None:
        raise RuntimeError("HMI rear-service door hinge is missing")
    named_groups = {
        "SM_LB_HMI04_RearServiceDoor": renderable_descendants(door_root),
        "SM_LB_HMI04_DisplaySurface": get("HMI_DisplaySurface") | prefixed("HMI_UI_"),
        "SM_LB_HMI04_ControlPower": get("HMI_ControlPower", "HMI_ControlPower_ChromeCollar"),
        "SM_LB_HMI04_ModeSelector": get("HMI_ModeSelector", "HMI_ModeSelector_ChromeCollar"),
        "SM_LB_HMI04_ResetButton": get("HMI_ResetButton", "HMI_ResetButton_ChromeCollar"),
        "SM_LB_HMI04_CycleStartButton": get("HMI_CycleStartButton", "HMI_CycleStartButton_ChromeCollar"),
        "SM_LB_HMI04_EmergencyStop": get("HMI_EmergencyStop", "HMI_EmergencyStop_YellowCollar"),
        "SM_LB_HMI04_StackRed": get("HMI_StackRed", "HMI_StackRedDivider"),
        "SM_LB_HMI04_StackAmber": get("HMI_StackAmber", "HMI_StackAmberDivider"),
        "SM_LB_HMI04_StackGreen": get("HMI_StackGreen", "HMI_StackGreenDivider"),
    }
    reserved = set().union(*named_groups.values())
    named_groups["SM_LB_HMI04_CabinetBody"] = all_renderables - reserved

    records = []
    for asset_name, sources in named_groups.items():
        combined = combined_copy(asset_name, sources)
        parts = separate_by_material(combined)
        for part_index, part in enumerate(parts):
            semantic_material = material_name(part)
            part_asset_name = f"{asset_name}_{safe_suffix(semantic_material)}"
            if any(record["asset_name"] == part_asset_name for record in records):
                part_asset_name += f"_{part_index:02d}"
            part.name = part_asset_name
            bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
            bpy.context.view_layer.objects.active = part
            bpy.ops.object.origin_set(type="ORIGIN_CURSOR", center="MEDIAN")
            output_path = output_dir / f"{part_asset_name}.fbx"
            export_fbx(part, output_path)
            records.append({
                "asset_name": part_asset_name,
                "semantic_group": asset_name,
                "semantic_material": semantic_material,
                "fbx": str(output_path),
                "source_objects": sorted(obj.name for obj in sources),
                "source_object_count": len(sources),
                "material_slots": [slot.material.name if slot.material else None for slot in part.material_slots],
                "bounds": object_bounds_cm(part),
            })
        for part in parts:
            bpy.data.objects.remove(part, do_unlink=True)

    manifest = {
        "asset_id": "IND-HMI-001", "revision": "shared_operator_hmi_v004_ue_modeling001",
        "source_blend": bpy.data.filepath, "status": "UNREAL_MODELING_CANDIDATE_NOT_PROMOTED",
        "units": "centimetres", "assembly_origin": "centre of plinth footprint at finished-floor level",
        "cabinet_contract_cm": {"width": 60.0, "depth": 46.0, "console_height": 128.0, "overall_height": 159.0},
        "screen_contract": "17-inch 4:3 display on 20-degree upward-facing operator panel",
        "modules": records,
        "semantic_material_policy": "Unreal-native explicit assignments; imported FBX materials forbidden",
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"LINE_BOSS_HMI_V004_UE_EXPORT_PASS modules={len(records)} manifest={manifest_path}")


if __name__ == "__main__":
    main()
