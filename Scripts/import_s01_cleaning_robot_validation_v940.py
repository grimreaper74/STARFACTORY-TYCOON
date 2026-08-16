from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal

ROOT=Path(unreal.Paths.project_dir())
PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap'
EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
SOURCES=[
 ('S01',ROOT/'SourceAssets/Candidate/PressTrains/S01_Destack/HandPaintedSplit_v937/Cairnwell_S01_Destack_HandPaintedSplit_v937.glb','/Game/LineBoss/Developer/Validation/BlenderApproved_v940/S01'),
 ('CLEANING_ROBOT',ROOT/'SourceAssets/Candidate/PressShop/CleaningRobot/Cairnwell_LB_CR01_v938/Cairnwell_LB_CR01_TexturedVisual_v938.glb','/Game/LineBoss/Developer/Validation/BlenderApproved_v940/CleaningRobot'),
]
OUT=ROOT/'Saved/Audits/PressShopIntegration/blender_approved_s01_cleaning_robot_import_v940.json'
lib=unreal.EditorAssetLibrary
sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if sha()!=EXPECTED: raise RuntimeError('Protected v438 mismatch before import')
if lib.does_directory_exist('/Game/LineBoss/Developer/Validation/BlenderApproved_v940'): raise RuntimeError('Refusing to overwrite v940 validation import')
records=[]
for label,source,dest in SOURCES:
 if not source.exists(): raise RuntimeError(f'Missing source {source}')
 task=unreal.AssetImportTask(); task.set_editor_properties({'filename':str(source),'destination_path':dest,'automated':True,'replace_existing':False,'replace_existing_settings':False,'save':True})
 unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
 unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
 assets=lib.list_assets(dest,recursive=True,include_folder=False); meshes=[]; materials=[]; textures=[]
 for p in assets:
  a=unreal.load_asset(p)
  if isinstance(a,unreal.StaticMesh):
   try: a.set_editor_property('nanite_settings',unreal.MeshNaniteSettings(enabled=False))
   except Exception: pass
   lib.save_loaded_asset(a,only_if_is_dirty=False); meshes.append(p)
  elif isinstance(a,(unreal.Material,unreal.MaterialInstance,unreal.MaterialInstanceConstant)): materials.append(p)
  elif isinstance(a,unreal.Texture): textures.append(p)
 records.append({'label':label,'source':str(source),'destination':dest,'assets':assets,'static_meshes':meshes,'materials':materials,'textures':textures})
if sha()!=EXPECTED: raise RuntimeError('Protected v438 changed during import')
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'revision':'v940','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__ISOLATED_IMPORT_NO_MAP_PLACEMENT','records':records,'protected_sha256':sha(),'meshy_credits_used_by_codex':0},indent=2),encoding='utf-8')
unreal.log('LINE_BOSS_BLENDER_APPROVED_IMPORT_V940_PASS')
