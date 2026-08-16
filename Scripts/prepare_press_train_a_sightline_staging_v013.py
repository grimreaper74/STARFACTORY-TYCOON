"""Export deduplicated local-pivot meshes for validated Train A v007."""

import bpy
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
TARGET_VERSION = os.environ.get("LB_PTA_SIGHTLINE_TARGET_VERSION", "v013")
SOURCE_VERSION = os.environ.get("LB_PTA_SIGHTLINE_SOURCE_VERSION", "v007")
SOURCE_PASS_PREFIX = os.environ.get("LB_PTA_SIGHTLINE_SOURCE_PASS_PREFIX", "PASS__V007_REAL_DIE_SPACE")
CORRECT_ROBOT_LOCAL_Y = os.environ.get("LB_PTA_STAGING_CORRECT_ROBOT_LOCAL_Y", "0") == "1"
SOURCE = ROOT / f"SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_{SOURCE_VERSION}"
BLEND = SOURCE / f"CA_MW_PressTrainA_AssemblyStudy_{SOURCE_VERSION}.blend"
MANIFEST_PATH = SOURCE / f"PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_{SOURCE_VERSION}.json"
VALIDATION_PATH = SOURCE / f"PRESS_TRAIN_A_ASSEMBLY_STUDY_VALIDATION_{SOURCE_VERSION}.json"
STAGING = ROOT / f"Saved/ImportStaging/PressTrainASightline_{TARGET_VERSION}"
OUT = ROOT / f"Saved/Audits/PressTrains/press_train_a_sightline_staging_{TARGET_VERSION}.json"
if STAGING.exists() or OUT.exists():
    raise RuntimeError(f"Refusing to overwrite {TARGET_VERSION} sightline staging")
STAGING.mkdir(parents=True)
manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
validation = json.loads(VALIDATION_PATH.read_text(encoding="utf-8"))
if not validation["status"].startswith(SOURCE_PASS_PREFIX):
    raise RuntimeError(f"{SOURCE_VERSION} source validation is not the expected PASS")
bpy.ops.wm.open_mainfile(filepath=str(BLEND))
collection = bpy.data.collections.get("TRAIN_A_ASSEMBLY")
if collection is None:
    raise RuntimeError("TRAIN_A_ASSEMBLY collection missing")
by_name = {obj.name: obj for obj in collection.all_objects}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def signature(obj, role):
    payload = {
        "vertices": [[round(coord, 7) for coord in vertex.co] for vertex in obj.data.vertices],
        "polygons": [list(poly.vertices) for poly in obj.data.polygons],
        "materials": [slot.material.name if slot.material else None for slot in obj.material_slots],
    }
    if CORRECT_ROBOT_LOCAL_Y and str(role).startswith("unload_robot_"):
        payload["unreal_local_y_preflip"] = True
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode("utf-8")).hexdigest().upper()


source_before = {path.name: sha(path) for path in (BLEND, MANIFEST_PATH, VALIDATION_PATH)}
signature_to_asset = {}
assets = []
instances = []
for record in manifest["instances"]:
    obj = by_name.get(record["name"])
    if obj is None or obj.type != "MESH":
        raise RuntimeError(f"Assembly object missing: {record['name']}")
    sig = signature(obj, record.get("role"))
    asset_name = signature_to_asset.get(sig)
    if asset_name is None:
        asset_name = f"SM_CA_MW_PTA_Sightline_{sig[:12]}_{TARGET_VERSION}"
        signature_to_asset[sig] = asset_name
        duplicate = obj.copy()
        duplicate.data = obj.data.copy()
        duplicate.name = asset_name
        duplicate.location = (0, 0, 0)
        duplicate.rotation_euler = (0, 0, 0)
        duplicate.scale = (1, 1, 1)
        # The legacy Blender->FBX->Unreal conversion mirrors mesh-local Y while actor
        # world Y stays unchanged. Pre-flip only directional robot geometry so Unreal
        # restores the authored joint endpoints; symmetric train parts remain untouched.
        if CORRECT_ROBOT_LOCAL_Y and str(record.get("role", "")).startswith("unload_robot_"):
            duplicate.data.transform(Matrix.Diagonal((1.0, -1.0, 1.0, 1.0)))
        duplicate.data.transform(Matrix.Scale(100.0, 4))
        bpy.context.scene.collection.objects.link(duplicate)
        bpy.ops.object.select_all(action="DESELECT")
        duplicate.select_set(True)
        bpy.context.view_layer.objects.active = duplicate
        target = STAGING / f"{asset_name}.fbx"
        bpy.ops.export_scene.fbx(filepath=str(target), use_selection=True, object_types={"MESH"},
            global_scale=1.0, apply_unit_scale=False, apply_scale_options="FBX_SCALE_NONE",
            axis_forward="-Z", axis_up="Y", use_mesh_modifiers=True, mesh_smooth_type="FACE",
            add_leaf_bones=False, bake_anim=False, use_triangles=True, path_mode="AUTO")
        assets.append({"asset": asset_name, "file": target.name, "sha256": sha(target),
                       "geometry_signature": sig,
                       "dimensions_mm": [round(value * 1000, 3) for value in obj.dimensions],
                       "materials": [slot.material.name for slot in obj.material_slots if slot.material],
                       "source_examples": [record["name"]]})
        bpy.data.objects.remove(duplicate, do_unlink=True)
    else:
        next(row for row in assets if row["asset"] == asset_name)["source_examples"].append(record["name"])
    instances.append({"object": record["name"], "asset": asset_name})

source_after = {path.name: sha(path) for path in (BLEND, MANIFEST_PATH, VALIDATION_PATH)}
report = {"$schema": f"cairnwell/import-staging/press-train-a-sightline-{TARGET_VERSION}/v1",
          "generated_utc": datetime.now(timezone.utc).isoformat(),
          "status": f"PASS__DEDUPLICATED_{SOURCE_VERSION.upper()}_SIGHTLINE_STAGING__SOURCE_UNCHANGED"
          if source_before == source_after else f"FAIL__{SOURCE_VERSION.upper()}_SOURCE_CHANGED_DURING_STAGING",
          "source_blend": str(BLEND.relative_to(ROOT)).replace("\\", "/"),
          "source_hashes_before": source_before, "source_hashes_after": source_after,
          "authored_instance_count": len(instances), "expected_instance_count": manifest["instance_count"],
          "unique_asset_count": len(assets),
          "robot_local_y_preflip_for_unreal_axis_conversion": CORRECT_ROBOT_LOCAL_Y,
          "staging_root": str(STAGING.relative_to(ROOT)).replace("\\", "/"),
          "assets": assets, "instances": instances}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"status": report["status"], "instances": len(instances),
                  "assets": len(assets)}, indent=2))
if report["status"].startswith("FAIL") or len(instances) != manifest["instance_count"]:
    raise RuntimeError(report["status"])
