"""Import exactly one PR-004 process-context FBX into a disposable candidate probe path."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import unreal


REPO = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MANIFEST = REPO / "SourceAssets/PR004/ProcessContext_v001/pr004_process_context_candidate_v001_manifest.json"
MODULE_ID = os.environ.get("LB_PR004_PROBE_MODULE", "")
DESTINATION = "/Game/LineBoss/Developer/ImportProbes/PR004/ProcessContext_v001"
OUTPUT = REPO / f"Saved/Audits/pr004_process_context_import_probe_{MODULE_ID or 'missing'}.json"

records = json.loads(MANIFEST.read_text(encoding="utf-8"))["modules"]
record = next((value for value in records if value["id"] == MODULE_ID), None)
if record is None:
    raise RuntimeError(f"Unknown or missing LB_PR004_PROBE_MODULE={MODULE_ID!r}")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
result = {
    "$schema": "line-boss/audit/pr004-process-context-import-probe/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "module_id": MODULE_ID,
    "source_fbx": record["fbx"],
    "destination": DESTINATION,
    "status": "IMPORT_STARTED_NOT_YET_PROVEN",
}
OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": record["fbx"],
    "destination_path": DESTINATION,
    "destination_name": record["object"],
    "automated": True,
    "replace_existing": True,
    "replace_existing_settings": True,
    "save": True,
})
options = unreal.FbxImportUI()
options.set_editor_properties({
    "import_mesh": True,
    "import_as_skeletal": False,
    "import_materials": False,
    "import_textures": False,
    "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
})
static_data = options.get_editor_property("static_mesh_import_data")
static_data.set_editor_properties({
    "combine_meshes": True,
    "convert_scene": True,
    "convert_scene_unit": True,
    "force_front_x_axis": False,
    "generate_lightmap_u_vs": True,
    "auto_generate_collision": False,
    "remove_degenerates": True,
})
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

asset_path = f"{DESTINATION}/{record['object']}"
mesh = unreal.load_asset(asset_path)
result.update({
    "completed_utc": datetime.now(timezone.utc).isoformat(),
    "asset": asset_path,
    "status": "SINGLE_FBX_IMPORT_PASS" if isinstance(mesh, unreal.StaticMesh) else "SINGLE_FBX_IMPORT_FAILED",
    "imported_object_paths": list(task.get_editor_property("imported_object_paths")),
})
OUTPUT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PR004_PROCESS_PROBE {MODULE_ID} {result['status']} {OUTPUT}")
