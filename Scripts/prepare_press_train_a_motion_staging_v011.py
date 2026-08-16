"""Export deduplicated local-pivot meshes for exact v003 Unreal reconstruction."""

import bpy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Matrix


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v003"
BLEND = SOURCE / "CA_MW_PressTrainA_AssemblyStudy_v003.blend"
MANIFEST_PATH = SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v003.json"
STAGING = ROOT / "Saved/ImportStaging/PressTrainAMotion_v011"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_motion_staging_v011.json"
if STAGING.exists() or OUT.exists():
    raise RuntimeError("Refusing to overwrite v011 authored staging")
STAGING.mkdir(parents=True)
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
collection = bpy.data.collections.get("TRAIN_A_ASSEMBLY")
if collection is None:
    raise RuntimeError("TRAIN_A_ASSEMBLY collection missing")
by_name = {obj.name: obj for obj in collection.all_objects}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def signature(obj):
    mesh = obj.data
    payload = {
        "vertices": [[round(coord, 7) for coord in vertex.co] for vertex in mesh.vertices],
        "polygons": [list(poly.vertices) for poly in mesh.polygons],
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
    }
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


source_hashes_before = {path.name: sha(path) for path in (BLEND, MANIFEST_PATH)}
signature_to_asset = {}
assets = []
instances = []
for record in manifest["instances"]:
    obj = by_name.get(record["name"])
    if obj is None or obj.type != "MESH":
        raise RuntimeError(f"Assembly object missing: {record['name']}")
    sig = signature(obj)
    asset_name = signature_to_asset.get(sig)
    if asset_name is None:
        asset_name = f"SM_CA_MW_PTA_Motion_{sig[:12]}_v011"
        signature_to_asset[sig] = asset_name
        duplicate = obj.copy()
        duplicate.data = obj.data.copy()
        duplicate.name = asset_name
        duplicate.location = (0, 0, 0)
        duplicate.rotation_euler = (0, 0, 0)
        duplicate.scale = (1, 1, 1)
        duplicate.data.transform(Matrix.Scale(100.0, 4))
        bpy.context.scene.collection.objects.link(duplicate)
        bpy.ops.object.select_all(action="DESELECT")
        duplicate.select_set(True)
        bpy.context.view_layer.objects.active = duplicate
        target = STAGING / f"{asset_name}.fbx"
        bpy.ops.export_scene.fbx(
            filepath=str(target), use_selection=True, object_types={"MESH"},
            global_scale=1.0, apply_unit_scale=False, apply_scale_options="FBX_SCALE_NONE",
            axis_forward="-Z", axis_up="Y", use_mesh_modifiers=True,
            mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
            use_triangles=True, path_mode="AUTO")
        assets.append({
            "asset": asset_name,
            "file": target.name,
            "sha256": sha(target),
            "geometry_signature": sig,
            "dimensions_mm": [round(value * 1000, 3) for value in obj.dimensions],
            "materials": [slot.material.name for slot in obj.material_slots if slot.material],
            "source_examples": [record["name"]],
        })
        bpy.data.objects.remove(duplicate, do_unlink=True)
    else:
        next(row for row in assets if row["asset"] == asset_name)["source_examples"].append(record["name"])
    instances.append({"object": record["name"], "asset": asset_name})

source_hashes_after = {path.name: sha(path) for path in (BLEND, MANIFEST_PATH)}
report = {
    "$schema": "cairnwell/import-staging/press-train-a-motion-v011/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__DEDUPLICATED_V003_MOTION_INSTANCE_STAGING__SOURCE_UNCHANGED"
    if source_hashes_before == source_hashes_after else "FAIL__V003_SOURCE_CHANGED_DURING_STAGING",
    "source_blend": str(BLEND.relative_to(ROOT)).replace("\\", "/"),
    "source_hashes_before": source_hashes_before,
    "source_hashes_after": source_hashes_after,
    "authored_instance_count": len(instances),
    "expected_instance_count": 336,
    "unique_asset_count": len(assets),
    "staging_root": str(STAGING.relative_to(ROOT)).replace("\\", "/"),
    "assets": assets,
    "instances": instances,
}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "instances": len(instances), "assets": len(assets)}, indent=2))
if report["status"].startswith("FAIL") or len(instances) != 336:
    raise RuntimeError(report["status"])
