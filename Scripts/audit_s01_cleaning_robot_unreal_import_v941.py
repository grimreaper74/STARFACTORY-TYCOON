from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal

ROOT=Path(unreal.Paths.project_dir()); BASE='/Game/LineBoss/Developer/Validation/BlenderApproved_v940'
PROTECTED=ROOT/'Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap'; EXPECTED='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8'
OUT=ROOT/'Saved/Audits/PressShopIntegration/blender_approved_s01_cleaning_robot_import_v941.json'; lib=unreal.EditorAssetLibrary
sha=hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if sha!=EXPECTED: raise RuntimeError('Protected v438 mismatch')
records=[]
for label,folder in [('S01',BASE+'/S01'),('CLEANING_ROBOT',BASE+'/CleaningRobot')]:
 assets=lib.list_assets(folder,recursive=True,include_folder=False); rows=[]
 for p in assets:
  a=unreal.load_asset(p); cls=a.get_class().get_name() if a else 'LOAD_FAILED'; row={'path':p,'class':cls}
  if isinstance(a,unreal.StaticMesh):
   try:
    settings=a.get_editor_property('nanite_settings'); settings.enabled=False; a.set_editor_property('nanite_settings',settings); lib.save_loaded_asset(a,only_if_is_dirty=False); row['nanite_enabled']=a.get_editor_property('nanite_settings').enabled
   except Exception as e: row['nanite_error']=str(e)
   row['material_slots']=[str(s.material_interface.get_path_name()) if s.material_interface else None for s in a.static_materials]
  rows.append(row)
 records.append({'label':label,'folder':folder,'asset_count':len(rows),'class_counts':{c:sum(1 for r in rows if r['class']==c) for c in sorted(set(r['class'] for r in rows))},'assets':rows})
fail=[]
if not records[0]['asset_count']: fail.append('S01 assets missing')
if not records[1]['asset_count']: fail.append('cleaning robot assets missing')
for rec in records:
 for row in rec['assets']:
  if row.get('nanite_enabled') is True: fail.append('Nanite still enabled '+row['path'])
if hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()!=EXPECTED: fail.append('protected map changed')
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps({'revision':'v941','generated_utc':datetime.now(timezone.utc).isoformat(),'status':'PASS__ISOLATED_ASSETS_NANITE_DISABLED' if not fail else 'FAIL__V941','records':records,'failures':fail,'protected_sha256':EXPECTED,'map_placement_performed':False,'meshy_credits_used_by_codex':0},indent=2),encoding='utf-8')
if fail: raise RuntimeError('; '.join(fail))
unreal.log('LINE_BOSS_S01_CLEANING_ROBOT_IMPORT_AUDIT_V941_PASS')
