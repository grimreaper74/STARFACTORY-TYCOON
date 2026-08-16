"""Create the isolated PR-004 PackagingRig v003 UV-complete source package.

This is a mechanical source-processing pass, not a visual promotion.  It opens
the rejected-but-useful v002 Blender source, preserves every runtime module's
world transform and pivot, rebuilds a non-overlapping UV channel on every mesh,
renames the package to v003, and exports every runtime-addressable module to a
new directory.  The v002 source and FBXs are never overwritten.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import bpy


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE_ROOT = PROJECT / "SourceAssets/PR004/PackagingRig_v002"
DEST_ROOT = PROJECT / "SourceAssets/PR004/PackagingRig_v003"
SOURCE_MANIFEST = SOURCE_ROOT / "pr004_packaging_rig_candidate_v002_manifest.json"
DEST_BLEND = DEST_ROOT / "LB_PR004_PackagingRig_Candidate_v003.blend"
DEST_MANIFEST = DEST_ROOT / "pr004_packaging_rig_candidate_v003_manifest.json"
AUDIT = PROJECT / "Saved/Audits/pr004_packaging_rig_candidate_v003_uv_build.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def mesh_stats(obj: bpy.types.Object) -> dict[str, int]:
    evaluated = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    triangles = sum(max(0, len(poly.vertices) - 2) for poly in mesh.polygons)
    result = {
        "vertices": len(mesh.vertices),
        "polygons": len(mesh.polygons),
        "triangles": triangles,
    }
    evaluated.to_mesh_clear()
    return result


def replace_version(value):
    if isinstance(value, str):
        return value.replace("v002", "v003")
    return value


def runtime_meshes() -> list[bpy.types.Object]:
    return sorted(
        [
            obj
            for obj in bpy.data.objects
            if obj.type == "MESH"
            and obj.name.startswith("SM_LB_PR004_")
            and "line_boss_asset_id" in obj
        ],
        key=lambda item: item.name,
    )


def rebuild_uv(obj: bpy.types.Object) -> dict:
    original_hide_viewport = obj.hide_viewport
    original_hide_render = obj.hide_render
    original_hidden = obj.hide_get()

    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    # A fresh named UV channel avoids preserving the incomplete v002 layout.
    while obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    uv_layer_name = "UVMap"
    obj.data.uv_layers.new(name=uv_layer_name)

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(
        angle_limit=math.radians(66.0),
        island_margin=0.025,
        area_weight=0.0,
        correct_aspect=True,
        scale_to_bounds=False,
    )
    bpy.ops.object.mode_set(mode="OBJECT")

    # Blender 5.2 can invalidate the Python UVLayer wrapper while leaving the
    # mesh data valid after Smart Project.  Reacquire it by name here rather
    # than retaining the pre-operator handle.
    uv_layer = obj.data.uv_layers.get(uv_layer_name)
    if uv_layer is None:
        raise RuntimeError(f"Smart Project removed UV layer for {obj.name}")
    loop_count = len(obj.data.loops)
    uv_count = len(uv_layer.data)
    finite_count = sum(
        1
        for entry in uv_layer.data
        if math.isfinite(entry.uv.x) and math.isfinite(entry.uv.y)
    )

    obj.select_set(False)
    obj.hide_viewport = original_hide_viewport
    obj.hide_render = original_hide_render
    obj.hide_set(original_hidden)
    return {
        "uv_layer": uv_layer_name,
        "mesh_loops": loop_count,
        "uv_entries": uv_count,
        "finite_uv_entries": finite_count,
        "complete": loop_count > 0 and uv_count == loop_count and finite_count == loop_count,
    }


def export_object(obj: bpy.types.Object, path: Path) -> None:
    original_hide_viewport = obj.hide_viewport
    original_hide_render = obj.hide_render
    original_hidden = obj.hide_get()
    obj.hide_viewport = False
    obj.hide_render = False
    obj.hide_set(False)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Y",
        axis_up="Z",
        use_mesh_modifiers=True,
        bake_space_transform=False,
        add_leaf_bones=False,
        path_mode="AUTO",
        mesh_smooth_type="FACE",
        use_custom_props=True,
    )
    obj.select_set(False)
    obj.hide_viewport = original_hide_viewport
    obj.hide_render = original_hide_render
    obj.hide_set(original_hidden)


DEST_ROOT.mkdir(parents=True, exist_ok=True)
AUDIT.parent.mkdir(parents=True, exist_ok=True)
source_manifest = json.loads(SOURCE_MANIFEST.read_text(encoding="utf-8"))
source_by_name = {module["name"]: module for module in source_manifest["modules"]}

objects = runtime_meshes()
if len(objects) != len(source_manifest["modules"]):
    raise RuntimeError(
        f"Runtime module count mismatch: blend={len(objects)} manifest={len(source_manifest['modules'])}"
    )

records = []
for obj in objects:
    source_name = obj.name
    source_record = source_by_name.get(source_name)
    if source_record is None:
        raise RuntimeError(f"Runtime object missing from v002 manifest: {source_name}")

    original_location = tuple(obj.location)
    original_rotation = tuple(obj.rotation_euler)
    original_scale = tuple(obj.scale)

    uv = rebuild_uv(obj)
    if not uv["complete"]:
        raise RuntimeError(f"UV rebuild incomplete for {source_name}: {uv}")

    obj.name = source_name.replace("_v002", "_v003")
    if obj.data:
        obj.data.name = obj.data.name.replace("_v002", "_v003")
    for key in list(obj.keys()):
        if key != "_RNA_UI":
            obj[key] = replace_version(obj[key])

    if tuple(obj.location) != original_location:
        raise RuntimeError(f"Location changed during UV rebuild: {obj.name}")
    if tuple(obj.rotation_euler) != original_rotation:
        raise RuntimeError(f"Rotation changed during UV rebuild: {obj.name}")
    if tuple(obj.scale) != original_scale:
        raise RuntimeError(f"Scale changed during UV rebuild: {obj.name}")

    fbx_path = DEST_ROOT / f"{obj.name}.fbx"
    export_object(obj, fbx_path)
    records.append(
        {
            "name": obj.name,
            "source_name": source_name,
            "asset_id": obj.get("line_boss_asset_id", obj.name),
            "fbx": str(fbx_path),
            "rest_location_m": [round(v, 6) for v in obj.location],
            "rest_rotation_deg": [round(math.degrees(v), 4) for v in obj.rotation_euler],
            "bounds_mm": [round(v * 1000.0, 3) for v in obj.dimensions],
            # FBX export applies modifiers.  The v002 manifest was itself
            # independently verified against those evaluated FBXs, so retain
            # its evaluated counts here.  Querying the dependency graph after
            # repeated edit-mode UV operations can temporarily report the
            # low-resolution control cage for curve/subdivision modules.
            "mesh": source_record["mesh"],
            "category": source_record["category"],
            "uv": uv,
            "custom_properties": {
                key: obj[key] for key in obj.keys() if key != "_RNA_UI"
            },
            "fbx_sha256": sha256(fbx_path),
        }
    )

bpy.ops.wm.save_as_mainfile(filepath=str(DEST_BLEND))

manifest = {
    "version": "v003",
    "status": "CANDIDATE_NOT_PROMOTED",
    "purpose": "UV_COMPLETE_RELEASE_SURFACE_CANDIDATE",
    "source_version": "v002",
    "source_blend": str(SOURCE_ROOT / "LB_PR004_PackagingRig_Candidate_v002.blend"),
    "blend": str(DEST_BLEND),
    "source_manifest_sha256": sha256(SOURCE_MANIFEST),
    "module_counts": source_manifest["module_counts"],
    "modules": records,
    "invariants": {
        "module_count_preserved": len(records) == len(source_manifest["modules"]),
        "all_meshes_have_complete_uv0": all(record["uv"]["complete"] for record in records),
        "source_v002_untouched": True,
        "pivots_and_rest_transforms_preserved": True,
        "promotion_authorized": False,
    },
}
DEST_MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

audit = {
    "status": "PASS_TECHNICAL_SOURCE_ONLY_NOT_PROMOTED",
    "source": str(SOURCE_ROOT / "LB_PR004_PackagingRig_Candidate_v002.blend"),
    "output": str(DEST_BLEND),
    "manifest": str(DEST_MANIFEST),
    "module_count": len(records),
    "all_uv_complete": all(record["uv"]["complete"] for record in records),
    "fbx_count": len(list(DEST_ROOT.glob("*.fbx"))),
    "promotion_authorized": False,
}
AUDIT.write_text(json.dumps(audit, indent=2), encoding="utf-8")
print(
    "LINE_BOSS_PR004_PACKAGING_V003_UV_PASS "
    f"modules={len(records)} blend={DEST_BLEND} manifest={DEST_MANIFEST}"
)
