"""Audit the preserved MR01 v017 Unreal import after the importer audit API fault."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = ROOT / "SourceAssets/Robots/LB_MR01_MaintenanceRobot"
DEST = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v017"
AUDIT = ROOT / "Saved/Audits/lb_mr01_candidate_v017_unreal_import.json"
SOURCES = [
    BASE / "Exports/Candidate_v017_IsolatedImport/LB_MR01_StaticPayload_v017.fbx",
    BASE / "Exports/Candidate_v017_IsolatedImport/SK_LB_MR01_Arm6Axis_v017.fbx",
    BASE / "Exports/Candidate_v013_IsolatedImport/SM_LB_MR01_ToolCarousel8_v013.fbx",
    *[BASE / f"Exports/Candidate_v013_IsolatedImport/SM_LB_MR01_Tool_T{i}_v013.fbx" for i in range(1, 9)],
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


assets = unreal.EditorAssetLibrary.list_assets(DEST, recursive=True, include_folder=False)
payload_static = []
tool_static = []
skeletal_meshes = []
skeletons = []
for path in assets:
    asset = unreal.load_asset(path)
    if isinstance(asset, unreal.StaticMesh):
        if "/Payload/" in path:
            payload_static.append(path)
        elif "/Tools/" in path:
            tool_static.append(path)
    elif isinstance(asset, unreal.SkeletalMesh):
        skeletal_meshes.append(path)
    elif isinstance(asset, unreal.Skeleton):
        skeletons.append(path)

tool_names = sorted(path.rsplit("/", 1)[-1] for path in tool_static)
expected_tools = sorted(["SM_LB_MR01_ToolCarousel8_v013"] + [f"SM_LB_MR01_Tool_T{i}_v013" for i in range(1, 9)])

bone_names = []
if len(skeletons) == 1:
    skeleton = unreal.load_asset(skeletons[0])
    bone_names = [str(name) for name in skeleton.get_reference_pose().get_bone_names()]

bounds = [unreal.load_asset(path).get_bounding_box() for path in payload_static]
minimum = [min(box.min.to_tuple()[axis] for box in bounds) for axis in range(3)] if bounds else []
maximum = [max(box.max.to_tuple()[axis] for box in bounds) for axis in range(3)] if bounds else []
size = [maximum[axis] - minimum[axis] for axis in range(3)] if bounds else []

checks = {
    "candidate_namespace_present": unreal.EditorAssetLibrary.does_directory_exist(DEST),
    "payload_mesh_count_matches_clean_reimport": len(payload_static) == 344,
    "exactly_one_skeletal_arm": len(skeletal_meshes) == 1,
    "exactly_one_arm_skeleton": len(skeletons) == 1,
    "authoritative_ten_bone_arm": len(bone_names) == 10,
    "carousel_and_eight_tools_exact": tool_names == expected_tools,
    "all_source_files_still_present": all(path.exists() for path in SOURCES),
    "rp01_wheels_and_hubs_excluded": not any("RP01_DriveWheel" in path or "RP01_DriveHub" in path for path in assets),
    "working_title_absent_from_asset_names": not any("LineBoss" in path.rsplit("/", 1)[-1] for path in assets),
}

result = {
    "schema": "lineboss.mr01_v017_unreal_import.v1",
    "candidate": "LB_MR01_RaisedArmCandidate_v017",
    "status": "IMPORT_GATE_PASS__CANDIDATE_NOT_PROMOTED" if all(checks.values()) else "FAIL",
    "destination": DEST,
    "source_files": {str(path.relative_to(ROOT)).replace("\\", "/"): sha256(path) for path in SOURCES},
    "asset_counts": {
        "all": len(assets),
        "payload_static_meshes": len(payload_static),
        "tool_static_meshes": len(tool_static),
        "skeletal_meshes": len(skeletal_meshes),
        "skeletons": len(skeletons),
        "arm_bone_count": len(bone_names),
    },
    "arm_bone_names": bone_names,
    "payload_aggregate_bounds_cm": {"min": minimum, "max": maximum, "size": size},
    "tool_assets": tool_names,
    "checks": checks,
    "shared_rp01_policy": "Assemble four independently driven corner modules from existing RP01 authority; do not duplicate them here.",
    "importer_note": "Initial import saved successfully; original post-import audit failed only because AnimPose has no Python len(). This fresh read-only audit uses AnimPose.get_bone_names().",
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
if result["status"] == "FAIL":
    raise RuntimeError({key: value for key, value in checks.items() if not value})
unreal.log(f"LB_MR01_V017_IMPORT_AUDIT_PASS payload={len(payload_static)} tools={len(tool_static)} bones={len(bone_names)}")
