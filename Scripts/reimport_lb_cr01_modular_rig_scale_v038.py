"""Correct the CR01 v038 Blender-metre to Unreal-centimetre import scale in place."""
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
SOURCE = ROOT / "SourceAssets/Robots/LB_CR01_CleaningAMR/Exports/Candidate_v038_ModularRig"
DEST = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v038_ModularRig"
fbx_files = sorted(SOURCE.glob("*.fbx"))
if len(fbx_files) != 16:
    raise RuntimeError(f"Expected 16 FBXs, found {len(fbx_files)}")

tasks = []
for fbx in fbx_files:
    task = unreal.AssetImportTask()
    task.set_editor_properties({
        "filename": str(fbx), "destination_path": DEST, "automated": True,
        "replace_existing": True, "replace_existing_settings": True, "save": True,
    })
    options = unreal.FbxImportUI()
    options.set_editor_properties({
        "import_mesh": True, "import_as_skeletal": False, "import_materials": True,
        "import_textures": False, "mesh_type_to_import": unreal.FBXImportType.FBXIT_STATIC_MESH,
    })
    options.get_editor_property("static_mesh_import_data").set_editor_properties({
        "combine_meshes": True, "convert_scene": True, "convert_scene_unit": True,
        "force_front_x_axis": True, "transform_vertex_to_absolute": False,
        "import_uniform_scale": 100.0, "generate_lightmap_u_vs": True,
        "auto_generate_collision": False, "remove_degenerates": True,
    })
    task.set_editor_property("options", options)
    tasks.append(task)

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
body = unreal.load_asset(DEST + "/SM_LB_CR01_BodyStatic_XForward_v038")
box = body.get_bounding_box()
size = box.max - box.min
if not (98.0 <= size.x <= 100.0 and 151.0 <= size.y <= 153.0 and 111.0 <= size.z <= 113.0):
    raise RuntimeError(f"Corrected body bounds invalid: {size}")
unreal.EditorAssetLibrary.save_directory(DEST, only_if_is_dirty=False, recursive=False)
unreal.log(f"LINE_BOSS_LB_CR01_V038_SCALE_PASS size_cm=({size.x},{size.y},{size.z})")
