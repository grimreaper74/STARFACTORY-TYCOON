import unreal
from pathlib import Path

SOURCE=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\PR002\UserScannerRuntime_v20260810_v921\UnrealStaging_v849")
DEST="/Game/LineBoss/Candidates/PressShop/PR002/UserScannerRuntime_v921"
tasks=[]
for fbx in sorted(SOURCE.glob("*.fbx")):
    task=unreal.AssetImportTask(); task.set_editor_properties({"filename":str(fbx),"destination_path":DEST,"destination_name":fbx.stem,"automated":True,"replace_existing":True,"replace_existing_settings":True,"save":True})
    options=unreal.FbxImportUI(); options.set_editor_properties({"import_mesh":True,"import_materials":True,"import_textures":True,"import_as_skeletal":False,"automated_import_should_detect_type":False})
    options.static_mesh_import_data.set_editor_properties({"combine_meshes":True,"generate_lightmap_u_vs":True,"auto_generate_collision":True,"import_uniform_scale":100.0})
    task.options=options; tasks.append(task)
unreal.SystemLibrary.execute_console_command(None,"Interchange.FeatureFlags.Import.FBX 0")
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
for fbx in sorted(SOURCE.glob("*.fbx")):
    path=f"{DEST}/{fbx.stem}.{fbx.stem}"; asset=unreal.load_asset(path)
    if not asset: raise RuntimeError(f"Missing PR002 module {path}")
    b=asset.get_bounds(); unreal.log(f"LINE_BOSS_PR002_V921 module={fbx.stem} extent={b.box_extent} sections={asset.get_num_sections(0)}")
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
