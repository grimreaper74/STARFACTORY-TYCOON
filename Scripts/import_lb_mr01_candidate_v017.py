"""Isolated Unreal import gate for MR01 raised-arm Candidate v017."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = ROOT / "SourceAssets/Robots/LB_MR01_MaintenanceRobot"
EXPORT = BASE / "Exports/Candidate_v017_IsolatedImport"
TOOLS = BASE / "Exports/Candidate_v013_IsolatedImport"
DEST_ROOT = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v017"
PAYLOAD_DEST = DEST_ROOT + "/Payload"
ARM_DEST = DEST_ROOT + "/Arm"
TOOLS_DEST = DEST_ROOT + "/Tools"
AUDIT = ROOT / "Saved/Audits/lb_mr01_candidate_v017_unreal_import.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def import_static(source: Path, destination: str, combine: bool) -> list[str]:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": destination,
        "automated": True,
        "replace_existing": False,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": False,
        "import_materials": True,
        "import_textures": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    options.get_editor_property("static_mesh_import_data").set_editor_properties({
        "combine_meshes": combine,
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": True,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list(task.get_editor_property("imported_object_paths"))


def import_skeletal(source: Path, destination: str) -> list[str]:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(source),
        "destination_path": destination,
        "automated": True,
        "replace_existing": False,
        "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True,
        "import_as_skeletal": True,
        "import_materials": True,
        "import_textures": False,
        "import_animations": False,
        "mesh_type_to_import": unreal.FBXImportType.FBXIT_SKELETAL_MESH,
    })
    options.get_editor_property("skeletal_mesh_import_data").set_editor_properties({
        "convert_scene": True,
        "convert_scene_unit": True,
        "force_front_x_axis": True,
        "import_meshes_in_bone_hierarchy": True,
        "use_t0_as_ref_pose": False,
        "update_skeleton_reference_pose": False,
    })
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list(task.get_editor_property("imported_object_paths"))


if unreal.EditorAssetLibrary.does_directory_exist(DEST_ROOT):
    raise RuntimeError(f"Preserve existing candidate; destination already exists: {DEST_ROOT}")

payload_fbx = EXPORT / "LB_MR01_StaticPayload_v017.fbx"
arm_fbx = EXPORT / "SK_LB_MR01_Arm6Axis_v017.fbx"
tool_files = [TOOLS / "SM_LB_MR01_ToolCarousel8_v013.fbx"] + [TOOLS / f"SM_LB_MR01_Tool_T{i}_v013.fbx" for i in range(1, 9)]
for path in [payload_fbx, arm_fbx, *tool_files]:
    if not path.exists():
        raise RuntimeError(f"Missing import authority: {path}")

imported = {
    "payload": import_static(payload_fbx, PAYLOAD_DEST, False),
    "arm": import_skeletal(arm_fbx, ARM_DEST),
    "tools": {},
}
for path in tool_files:
    imported["tools"][path.stem] = import_static(path, TOOLS_DEST, True)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.EditorAssetLibrary.save_directory(DEST_ROOT, only_if_is_dirty=False, recursive=True)

all_assets = unreal.EditorAssetLibrary.list_assets(DEST_ROOT, recursive=True, include_folder=False)
static_meshes = []
skeletal_meshes = []
skeletons = []
for asset_path in all_assets:
    asset = unreal.load_asset(asset_path)
    if isinstance(asset, unreal.StaticMesh):
        static_meshes.append(asset_path)
    elif isinstance(asset, unreal.SkeletalMesh):
        skeletal_meshes.append(asset_path)
    elif isinstance(asset, unreal.Skeleton):
        skeletons.append(asset_path)

arm_bone_count = None
if skeletal_meshes:
    skeletal = unreal.load_asset(skeletal_meshes[0])
    skeleton = skeletal.get_editor_property("skeleton")
    if skeleton:
        pose = skeleton.get_reference_pose()
        arm_bone_count = len(pose.get_bone_names())

checks = {
    "payload_imported_modular": len(static_meshes) >= 344,
    "exactly_one_skeletal_arm": len(skeletal_meshes) == 1,
    "arm_skeleton_created": len(skeletons) >= 1,
    "authoritative_ten_bone_arm": arm_bone_count == 10,
    "carousel_and_eight_tools_requested": len(imported["tools"]) == 9,
    "all_tool_import_tasks_returned_assets": all(paths for paths in imported["tools"].values()),
    "source_hashes_recorded": True,
    "rp01_wheels_not_imported_in_candidate": not any("RP01_DriveWheel" in path or "RP01_DriveHub" in path for path in all_assets),
}

result = {
    "schema": "lineboss.mr01_v017_unreal_import.v1",
    "candidate": "LB_MR01_RaisedArmCandidate_v017",
    "status": "IMPORT_GATE_PASS__CANDIDATE_NOT_PROMOTED" if all(checks.values()) else "FAIL",
    "destination": DEST_ROOT,
    "source_files": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in [payload_fbx, arm_fbx, *tool_files]},
    "asset_counts": {
        "all": len(all_assets),
        "static_meshes": len(static_meshes),
        "skeletal_meshes": len(skeletal_meshes),
        "skeletons": len(skeletons),
        "arm_bone_count": arm_bone_count,
    },
    "imported_object_paths": imported,
    "checks": checks,
    "shared_rp01_policy": "Wheels/hubs deliberately excluded; assemble from existing shared RP01 authority.",
    "promotion_authorized": False,
    "remaining_gates": [
        "reusable MR01 Blueprint assembly with shared RP01 base",
        "T6 mutually-exclusive carousel/coupler state",
        "arm, lift, mast and outrigger runtime motion",
        "collision/navigation/save authority",
        "fresh fixed-camera isolated and accepted-PR004-lighting screenshots",
    ],
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
if result["status"] == "FAIL":
    raise RuntimeError({key: value for key, value in checks.items() if not value})
unreal.log(f"LB_MR01_V017_IMPORT_PASS assets={len(all_assets)} static={len(static_meshes)} skeletal={len(skeletal_meshes)}")
