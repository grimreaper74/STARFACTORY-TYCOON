import unreal
from pathlib import Path
SOURCE=Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\SourceAssets\Candidate\PressShop\PR002\UserScannerRuntime_v20260810_v921\RuntimeGLB_v922")
DEST="/Game/LineBoss/Candidates/PressShop/PR002/RuntimeGLB_v922"
names=["SM_CA_MW_PR002_ScannerWeighCell_v922","SM_CA_MW_PR002_RemovableWrappedCoil_v922"]
tasks=[]
for name in names:
 t=unreal.AssetImportTask();t.set_editor_properties({"filename":str(SOURCE/(name+".glb")),"destination_path":DEST,"destination_name":name,"automated":True,"replace_existing":True,"replace_existing_settings":True,"save":True});tasks.append(t)
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
for name in names:
 matches=[p for p in unreal.EditorAssetLibrary.list_assets(DEST,recursive=True,include_folder=False) if p.rsplit("/",1)[-1].split(".",1)[0]==name]
 if not matches:raise RuntimeError(name)
 asset=unreal.load_asset(matches[0]);b=asset.get_bounds();unreal.log(f"LINE_BOSS_PR002_GLTF_V922 module={name} asset={asset.get_path_name()} extent={b.box_extent} sections={asset.get_num_sections(0)}")
 unreal.EditorAssetLibrary.save_loaded_asset(asset)
