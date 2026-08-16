"""Import the approved Walker GLB with Interchange and inventory created assets."""
from pathlib import Path
import json, unreal
ROOT=Path(unreal.Paths.project_dir()).resolve()
SRC=ROOT/r'SourceAssets\Candidate\PressTrains\Shared\UserApprovedS03Walker_v20260809_v001\Runtime_v001\SM_CA_MW_S03_Walker_UserApproved_Runtime_v001.glb'
DEST='/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v014/ApprovedWalker'
OUT=ROOT/r'Saved\Audits\PressTrains\approved_walker_glb_import_v20260809_v014.json'
if not SRC.is_file() or OUT.exists():raise RuntimeError('fresh/source invariant')
t=unreal.AssetImportTask();t.set_editor_properties({'filename':str(SRC),'destination_path':DEST,'automated':True,'replace_existing':False,'save':True})
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([t]);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
paths=[str(x) for x in t.imported_object_paths]
assets=[]
for p in unreal.EditorAssetLibrary.list_assets(DEST,recursive=True,include_folder=False):
 a=unreal.EditorAssetLibrary.load_asset(p);assets.append({'path':p,'class':a.get_class().get_name() if a else None})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'IMPORT_COMPLETE__ASSET_INVENTORY_REQUIRES_REVIEW','source':str(SRC),'destination':DEST,'task_paths':paths,'assets':assets,'meshy_credits_used':0},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_APPROVED_WALKER_GLB_IMPORT_V014_PASS')
