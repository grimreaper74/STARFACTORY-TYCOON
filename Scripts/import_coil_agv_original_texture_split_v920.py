import unreal
from pathlib import Path

SOURCE=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\CoilAGV\OriginalTextureSplit_v920")
DEST="/Game/LineBoss/Candidates/PressShop/CoilAGV/OriginalTextureSplit_v920"
names=["SM_CA_MW_CoilAGV_Chassis_v920","SM_CA_MW_CoilAGV_LiftDeck_v920"]
tasks=[]
for name in names:
    task=unreal.AssetImportTask(); task.set_editor_properties({"filename":str(SOURCE/(name+".glb")),"destination_path":DEST,"destination_name":name,"automated":True,"replace_existing":True,"replace_existing_settings":True,"save":True}); tasks.append(task)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
for name in names:
    matches=[p for p in unreal.EditorAssetLibrary.list_assets(DEST,recursive=True,include_folder=False) if p.rsplit("/",1)[-1].split(".",1)[0]==name]
    if not matches: raise RuntimeError(f"Missing imported AGV module {name}")
    asset=unreal.load_asset(matches[0]); b=asset.get_bounds()
    unreal.log(f"LINE_BOSS_AGV_V920 module={name} asset={asset.get_path_name()} extent={b.box_extent} sections={asset.get_num_sections(0)}")
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
