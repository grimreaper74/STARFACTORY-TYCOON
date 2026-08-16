"""Create candidate-only centimetre-coordinate FBX staging derivatives; never edits retained sources."""

import bpy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v001"
MANIFEST = json.loads((SOURCE / "PRESS_TRAIN_A_ASSEMBLY_STUDY_MANIFEST_v001.json").read_text(encoding="utf-8"))
STAGING = ROOT / "Saved/ImportStaging/PressTrainAAssemblyIntegration_v004"
OUT = ROOT / "Saved/Audits/PressTrains/press_train_a_assembly_integration_staging_v004.json"
if STAGING.exists() or OUT.exists():
    raise RuntimeError("Refusing to overwrite existing v004 import staging")
STAGING.mkdir(parents=True)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


sources = [SOURCE / MANIFEST["assembly_fbx"]["file"]]
sources.extend(ROOT / record["path"] for record in MANIFEST["source_files"])
rows = []
for source in sources:
    if not source.exists():
        raise FileNotFoundError(source)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(source), use_custom_normals=True, ignore_leaf_bones=True)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh objects imported from {source}")
    for obj in meshes:
        obj.location = tuple(value * 100.0 for value in obj.location)
        obj.scale = tuple(value * 100.0 for value in obj.scale)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in meshes:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    target = STAGING / source.name
    bpy.ops.export_scene.fbx(
        filepath=str(target), use_selection=True, object_types={"MESH"},
        global_scale=1.0, apply_unit_scale=False, apply_scale_options="FBX_SCALE_NONE",
        axis_forward="-Z", axis_up="Y", use_mesh_modifiers=True,
        mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
        use_triangles=True, path_mode="AUTO",
    )
    rows.append({"source": str(source.relative_to(ROOT)).replace("\\", "/"),
                 "source_sha256": sha(source), "staging": str(target.relative_to(ROOT)).replace("\\", "/"),
                 "staging_sha256": sha(target), "bytes": target.stat().st_size,
                 "mesh_objects": len(meshes), "coordinate_scale_baked": 100.0})

report = {"generated_utc": datetime.now(timezone.utc).isoformat(),
          "status": "PASS__CANDIDATE_ONLY_CM_COORDINATE_STAGING__RETAINED_SOURCES_UNCHANGED",
          "staging_root": str(STAGING.relative_to(ROOT)).replace("\\", "/"),
          "file_count": len(rows), "files": rows}
OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
