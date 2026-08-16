import unreal

SOURCE = r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\CoilAGV\Cleaned_v918\SM_CA_MW_CoilAGV_Chassis_v918.glb"
DEST = "/Game/LineBoss/Candidates/PressShop/CoilAGV/Cleaned_v918"
NAME = "SM_CA_MW_CoilAGV_Chassis_v918"

task = unreal.AssetImportTask()
task.set_editor_properties({
    "filename": SOURCE,
    "destination_path": DEST,
    "destination_name": NAME,
    "automated": True,
    "replace_existing": True,
    "replace_existing_settings": True,
    "save": True,
})
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
matches = [p for p in unreal.EditorAssetLibrary.list_assets(DEST, recursive=True, include_folder=False)
           if p.rsplit("/", 1)[-1].split(".", 1)[0] == NAME]
asset = unreal.load_asset(matches[0]) if matches else None
if not asset:
    raise RuntimeError("Coil AGV static mesh import failed")
bounds = asset.get_bounds()
unreal.log(f"LINE_BOSS_COIL_AGV_UNREAL_IMPORT asset={asset.get_path_name()} box_extent={bounds.box_extent} material_slots={asset.get_num_sections(0)}")
unreal.EditorAssetLibrary.save_loaded_asset(asset)
