"""Record selected Unreal Geometry Script callable docs/signatures."""

from pathlib import Path
import json
import unreal

targets = {
    "copy_from": unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh,
    "copy_to": unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh,
    "repair_degenerate": unreal.GeometryScript_MeshRepair.repair_mesh_degenerate_geometry,
    "compact": unreal.GeometryScript_MeshRepair.compact_mesh,
    "recompute_normals": unreal.GeometryScript_Normals.recompute_normals,
    "xatlas_uv": unreal.GeometryScript_UVs.auto_generate_x_atlas_mesh_u_vs,
    "set_collision": unreal.GeometryScript_Collision.set_static_mesh_collision_from_mesh,
}
records = {name: str(getattr(fn, "__doc__", "")) for name, fn in targets.items()}
for cls_name in (
    "GeometryScriptCopyMeshFromAssetOptions", "GeometryScriptCopyMeshToAssetOptions",
    "GeometryScriptDegenerateTriangleOptions", "GeometryScriptCalculateNormalsOptions",
    "GeometryScriptXAtlasOptions", "GeometryScriptSetStaticMeshCollisionOptions",
    "GeometryScriptCollisionFromMeshOptions",
):
    cls = getattr(unreal, cls_name)
    records[cls_name] = str(getattr(cls, "__doc__", "")) + "\n" + str(sorted(x for x in dir(cls) if not x.startswith("_")))

output = Path(unreal.Paths.project_saved_dir()) / "Audits/geometry_signature_inventory.json"
output.write_text(json.dumps(records, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_GEOMETRY_SIGNATURE_PASS path={output}")
unreal.SystemLibrary.quit_editor()
