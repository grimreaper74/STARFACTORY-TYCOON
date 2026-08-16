"""Non-overwriting Unreal intake for the retained MR01 v022 static payload."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Robots/LB_MR01_MaintenanceRobot/Exports/Candidate_v022_IsolatedImport/LB_MR01_StaticPayload_v022.fbx"
DEST_ROOT = "/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v022"
DEST = DEST_ROOT + "/Payload"
AUDIT = ROOT / "Saved/Audits/SupportRobots/mr01_v022_static_payload_unreal_import.json"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


if not SOURCE.exists():
    raise RuntimeError("Missing v022 FBX: {}".format(SOURCE))
existing_candidate = unreal.EditorAssetLibrary.does_directory_exist(DEST_ROOT)
if not existing_candidate:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(SOURCE),
        "destination_path": DEST,
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
        "combine_meshes": False,
        "convert_scene": True,
        "convert_scene_unit": True,
        # The v022 FBX is already authored as Blender -Y = CFR +X.  Reapplying
        # Force Front X caused the rejected v021 90-degree presentation mismatch.
        "force_front_x_axis": False,
        "generate_lightmap_u_vs": True,
        "auto_generate_collision": False,
        "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    unreal.EditorAssetLibrary.save_directory(DEST_ROOT, only_if_is_dirty=False, recursive=True)

assets = unreal.EditorAssetLibrary.list_assets(DEST, recursive=True, include_folder=False)
meshes = []
for asset_path in assets:
    asset = unreal.load_asset(asset_path)
    if isinstance(asset, unreal.StaticMesh):
        meshes.append((asset_path, asset))

boxes = [asset.get_bounding_box() for _path, asset in meshes]
minimum = [min(box.min.to_tuple()[axis] for box in boxes) for axis in range(3)]
maximum = [max(box.max.to_tuple()[axis] for box in boxes) for axis in range(3)]
size = [maximum[axis] - minimum[axis] for axis in range(3)]


def bounds_for(name):
    for path, mesh in meshes:
        if mesh.get_name() == name:
            box = mesh.get_bounding_box()
            return {
                "min_cm": list(box.min.to_tuple()),
                "max_cm": list(box.max.to_tuple()),
                "size_cm": [box.max.to_tuple()[i] - box.min.to_tuple()[i] for i in range(3)],
            }
    raise RuntimeError("Missing imported mesh {}".format(name))


checks = {
    "exact_static_mesh_count": len(meshes) == 345,
    "native_axis_length_exceeds_width": size[0] > size[1],
    "travel_width_at_or_below_94cm": size[1] <= 94.0,
    "travel_length_between_150_and_160cm": 150.0 <= size[0] <= 160.0,
}
payload = {
    "$schema": "cairnwell/audit/mr01-v022-static-payload-unreal-import/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__V022_NATIVE_X_FORWARD_PAYLOAD_IMPORTED__BLUEPRINT_RUNTIME_GATES_OPEN__NOT_PROMOTED" if all(checks.values()) else "FAIL__V022_IMPORT_AXIS_OR_COUNT",
    "source_fbx": str(SOURCE),
    "source_fbx_sha256": sha256(SOURCE),
    "destination": DEST,
    "mode": "AUDIT_EXISTING_NON_OVERWRITTEN_IMPORT" if existing_candidate else "FRESH_NON_OVERWRITING_IMPORT",
    "static_mesh_count": len(meshes),
    "aggregate_bounds_cm": {"min": minimum, "max": maximum, "size": size},
    "bumper_front_bounds": bounds_for("SM_LB_MR01_BumperFront"),
    "bumper_rear_bounds": bounds_for("SM_LB_MR01_BumperRear"),
    "bumper_side_l_bounds": bounds_for("SM_LB_MR01_BumperSide_L"),
    "bumper_side_r_bounds": bounds_for("SM_LB_MR01_BumperSide_R"),
    "checks": checks,
    "promotion_authorized": False,
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
if not all(checks.values()):
    raise RuntimeError({key: value for key, value in checks.items() if not value})
unreal.log("LINE_BOSS_MR01_V022_PAYLOAD_IMPORT {}".format(payload["status"]))
