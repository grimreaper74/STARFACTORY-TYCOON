"""Export 336 deterministic per-object FBX files from source v013.

Each file contains one evaluated mesh at a local identity transform.  The
receipt maps the immutable source object identity to an Unreal-safe asset name,
allowing a fresh child of the retained native runtime map to replace visuals
without changing actor transforms, pivots, hierarchy or runtime bindings.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v013"
BLEND = SOURCE / "CA_MW_PressTrainA_AssemblyStudy_v013.blend"
MANIFEST = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v013.json"
VALIDATION = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_VALIDATION_v013.json"
STAGING = ROOT / "Saved/ImportStaging/PressTrainAFabrication_v031"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_fabrication_staging_v031.json"
if STAGING.exists() or OUT.exists():
    raise RuntimeError("refusing to overwrite v031 fabrication staging")
STAGING.mkdir(parents=True)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
if validation.get("status") != "PASS__V013_SOURCE_GEOMETRY_AND_PBR_REFINEMENT__UNREAL_INTEGRATION_REQUIRED__NOT_PROMOTED":
    raise RuntimeError("v013 validation is not the expected PASS receipt")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))
collection = bpy.data.collections.get("TRAIN_A_ASSEMBLY")
if collection is None:
    raise RuntimeError("TRAIN_A_ASSEMBLY collection missing")
objects = {obj.name: obj for obj in collection.all_objects if obj.type == "MESH"}
records = manifest["instances"]
if len(objects) != 336 or len(records) != 336:
    raise RuntimeError(f"v013 identity count mismatch objects={len(objects)} records={len(records)}")

depsgraph = bpy.context.evaluated_depsgraph_get()
exports = []
for index, record in enumerate(records, 1):
    source_name = str(record["name"])
    source = objects.get(source_name)
    if source is None:
        raise RuntimeError(f"source object missing: {source_name}")
    asset_name = f"SM_CA_MW_PTA_Fabrication_{index:03d}_v031"
    target = STAGING / f"{asset_name}.fbx"

    evaluated = source.evaluated_get(depsgraph)
    mesh = bpy.data.meshes.new_from_object(evaluated, depsgraph=depsgraph)
    duplicate = bpy.data.objects.new(asset_name, mesh)
    bpy.context.scene.collection.objects.link(duplicate)
    duplicate.location = (0.0, 0.0, 0.0)
    duplicate.rotation_euler = (0.0, 0.0, 0.0)
    duplicate.scale = (1.0, 1.0, 1.0)

    bpy.ops.object.select_all(action="DESELECT")
    duplicate.select_set(True)
    bpy.context.view_layer.objects.active = duplicate
    bpy.ops.export_scene.fbx(
        filepath=str(target),
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Y",
        axis_up="Z",
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        bake_anim=False,
        use_triangles=True,
        path_mode="AUTO",
    )
    exports.append({
        "source_object": source_name,
        "asset_name": asset_name,
        "file": target.name,
        "bytes": target.stat().st_size,
        "sha256": sha256(target),
        "expected_dimensions_mm": [round(float(value) * 1000.0, 3) for value in source.dimensions],
        "material_slots": [slot.material.name for slot in source.material_slots if slot.material],
        "stage": record.get("stage"),
        "role": record.get("role"),
        "runtime_parent": record.get("runtime_parent"),
    })
    bpy.data.objects.remove(duplicate, do_unlink=True)
    bpy.data.meshes.remove(mesh)

payload = {
    "$schema": "cairnwell/import-staging/press-train-a-fabrication-v031/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__336_DETERMINISTIC_LOCAL_PIVOT_FBX_FILES__UNREAL_IMPORT_REQUIRED__NOT_PROMOTED",
    "source_blend": str(BLEND.relative_to(ROOT)).replace("\\", "/"),
    "source_blend_sha256": sha256(BLEND),
    "source_manifest_sha256": sha256(MANIFEST),
    "staging_root": str(STAGING.relative_to(ROOT)).replace("\\", "/"),
    "export_count": len(exports),
    "exports": exports,
    "source_files_modified": [],
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({
    "status": payload["status"],
    "export_count": payload["export_count"],
    "staging_root": payload["staging_root"],
}, indent=2))
