from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal

ROOT=Path(unreal.Paths.project_dir())
PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap'
EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
SOURCE=ROOT/'SourceAssets/Candidate/PressTrains/S07_InspectionUnload/NewPortal_v949/Cairnwell_S07_InspectionUnload_NewPortal_v949.glb'
DEST='/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260810_v950/S07Portal'
OUT=ROOT/'Saved/Audits/PressShopIntegration/s07_new_portal_import_v950.json'
lib=unreal.EditorAssetLibrary
sha=lambda:hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if sha()!=EXPECTED: raise RuntimeError('Protected v438 mismatch before import')
if not SOURCE.exists(): raise RuntimeError(str(SOURCE))
if lib.does_directory_exist(DEST): raise RuntimeError('Refusing to overwrite v950')
task=unreal.AssetImportTask(); task.set_editor_properties({'filename':str(SOURCE),'destination_path':DEST,'automated':True,'replace_existing':False,'replace_existing_settings':False,'save':True})
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]); unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
assets=lib.list_assets(DEST,recursive=True,include_folder=False); meshes=[]; materials=[]
for p in assets:
    a=unreal.load_asset(p)
    if isinstance(a,unreal.StaticMesh):
        try: a.set_editor_property('nanite_settings',unreal.MeshNaniteSettings(enabled=False))
        except Exception: pass
        lib.save_loaded_asset(a,only_if_is_dirty=False); meshes.append(p)
    elif isinstance(a,(unreal.Material,unreal.MaterialInstance,unreal.MaterialInstanceConstant)): materials.append(p)
if len(meshes)!=1 or len(materials)!=7: raise RuntimeError(f'Unexpected import meshes={len(meshes)} materials={len(materials)}')
mesh=unreal.load_asset(meshes[0]); box=mesh.get_bounding_box(); size=box.max-box.min
if not (675<=size.x<=705 and 625<=size.y<=665 and 430<=size.z<=455): raise RuntimeError(f'Bad S07 envelope cm={size}')
if sha()!=EXPECTED: raise RuntimeError('Protected v438 changed during import')
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'revision':'v950','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__BLENDER_VALIDATED_S07_PORTAL_IMPORT','source':str(SOURCE),'destination':DEST,'assets':assets,'static_mesh':meshes[0],'materials':materials,'bounds_cm':[size.x,size.y,size.z],'nanite':False,'protected_sha256':sha(),'meshy_credits_used_by_codex':0},indent=2),encoding='utf-8')
unreal.log('LINE_BOSS_S07_NEW_PORTAL_IMPORT_V950_PASS')
