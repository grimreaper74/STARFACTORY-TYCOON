"""Import the face-smoothed, dimension-locked CR01 v032 FBX into Unreal."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Robots/LB_CR01_CleaningAMR/Exports/Candidate_v032/LB_CR01_FullRobot_LOD0_XForward_v032.fbx"
DEST = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v032/LOD0"
AUDIT = ROOT / "Saved/Audits/lb_cr01_candidate_v032_unreal_import.json"
EXPECTED = [152.0, 98.0, 112.0]

if not SOURCE.exists():
    raise RuntimeError(f"Missing {SOURCE}")
if unreal.EditorAssetLibrary.does_directory_exist(DEST):
    raise RuntimeError("v032 destination already exists; preserve candidate evidence")

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
    "force_front_x_axis": True,
    "generate_lightmap_u_vs": True,
    "auto_generate_collision": False,
    "remove_degenerates": True,
})
task.set_editor_property("options", options)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

mesh_paths = [
    path for path in unreal.EditorAssetLibrary.list_assets(DEST, recursive=False, include_folder=False)
    if isinstance(unreal.load_asset(path), unreal.StaticMesh)
]
if len(mesh_paths) < 560:
    raise RuntimeError(f"Incomplete modular import: {len(mesh_paths)}")

bounds = [unreal.load_asset(path).get_bounding_box() for path in mesh_paths]
minimum = [min(box.min.to_tuple()[axis] for box in bounds) for axis in range(3)]
maximum = [max(box.max.to_tuple()[axis] for box in bounds) for axis in range(3)]
size = [maximum[axis] - minimum[axis] for axis in range(3)]
bounds_pass = all(abs(actual - expected) <= 0.2 for actual, expected in zip(size, EXPECTED))
if not bounds_pass:
    raise RuntimeError(f"v032 bounds failed: {size}")

result = {
    "status": "IMPORT_GATE_PASS__CANDIDATE_NOT_PROMOTED",
    "source": str(SOURCE),
    "destination": DEST,
    "mesh_count": len(mesh_paths),
    "aggregate_bounds_cm": {"min": minimum, "max": maximum, "size": size},
    "bounds_pass": bounds_pass,
    "smoothing_export": "FACE",
    "remaining_gates": [
        "Pro-matching visual refinement",
        "component pivot validation",
        "mechanism runtime animation",
        "collision and navigation",
        "fresh fixed-camera Unreal evidence",
    ],
}
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_LB_CR01_V032_IMPORT_PASS meshes={len(mesh_paths)} bounds={size}")
