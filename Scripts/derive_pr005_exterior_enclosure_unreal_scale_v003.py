"""Create immutable-source-safe FBX derivatives compensating UE 5.8's 1/100 import."""

import hashlib
import json
from pathlib import Path

import bpy
from mathutils import Matrix


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/Candidate/PressShop/PR005/Candidate_v002"
DEST = ROOT / "SourceAssets/Candidate/PressShop/PR005/UnrealDerived_v003"
EXPORTS = DEST / "Exports"
MANIFEST = json.loads((SOURCE / "PR005_EXTERIOR_ENCLOSURE_MANIFEST_v002.json").read_text(encoding="utf-8"))


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if DEST.exists():
    raise RuntimeError(f"refusing to overwrite preserved derivative {DEST}")
EXPORTS.mkdir(parents=True)
rows = []
for source_row in MANIFEST["assets"]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source_fbx = SOURCE / source_row["fbx"]
    bpy.ops.import_scene.fbx(filepath=str(source_fbx), use_anim=False)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if len(meshes) != 1:
        raise RuntimeError(f"expected one mesh in {source_fbx}, found {len(meshes)}")
    obj = meshes[0]
    obj.data.transform(Matrix.Scale(100.0, 4))
    derived_name = source_row["asset_name"].replace("_v002", "_v003")
    obj.name = derived_name
    obj.data.name = derived_name
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    output = EXPORTS / f"{derived_name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(output), use_selection=True, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS", object_types={"MESH"},
        add_leaf_bones=False, bake_anim=False, mesh_smooth_type="FACE")
    rows.append({
        "asset_name": derived_name,
        "fbx": str(output.relative_to(DEST)).replace("\\", "/"),
        "sha256": sha256(output),
        "source_asset_name": source_row["asset_name"],
        "source_fbx": source_row["fbx"],
        "source_sha256": source_row["sha256"],
        "local_vertex_scale_compensation": 100.0,
        "expected_dimensions_mm": source_row["dimensions_mm"],
        "pivot_m": source_row["pivot_m"],
        "bounds_min_mm": source_row["bounds_min_mm"],
        "bounds_max_mm": source_row["bounds_max_mm"],
        "materials": source_row["materials"],
    })

payload = {
    "$schema": "cairnwell/source/pr005-exterior-enclosure-unreal-derived-v003/v1",
    "status": "DERIVED_FBX_SCALE_COMPENSATION_ONLY__UNREAL_IMPORT_AUDIT_REQUIRED__NOT_INTEGRATED_NOT_PROMOTED",
    "source_candidate": "SourceAssets/Candidate/PressShop/PR005/Candidate_v002",
    "reason": "UE 5.8 Interchange imported the valid v002 FBXs at exactly 1/100 dimensions and ignored import_uniform_scale. Local vertex coordinates are multiplied by 100 in new derived files; immutable v002 is unchanged.",
    "world_placement": "TBC_NOT_INVENTED",
    "assets": rows,
    "promotion_authorized": False,
}
(DEST / "PR005_EXTERIOR_ENCLOSURE_UNREAL_DERIVED_MANIFEST_v003.json").write_text(
    json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({"status": payload["status"], "assets": len(rows)}, indent=2))
