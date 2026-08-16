"""Calibrate the Meshy atlases to match the accepted Blender review under factory light."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();DEST='/Game/LineBoss/Candidates/PressShop/PR009_PR010_UserMeshy_v864';OUT=ROOT/r'Saved\Audits\PressShopIntegration\pr009_pr010_material_calibration_v873.json';P=ROOT/r'Content\LineBoss\Maps\LB_PressShop_BuilderAuthorityCandidate_v438.umap';E='5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest().upper();before=sha(P)
if before!=E or OUT.exists():raise RuntimeError('fresh/protected invariant')
lib=unreal.EditorAssetLibrary;mel=unreal.MaterialEditingLibrary;rows=[]
for station in ('PR009','PR010'):
 folder=f'{DEST}/{station}/Materials';m=lib.load_asset(f'{folder}/M_{station}_MeshyAtlas_v864');base=lib.load_asset(f'{folder}/T_{station}_BaseColor_v864');mel.delete_all_material_expressions(m)
 tex=mel.create_material_expression(m,unreal.MaterialExpressionTextureSample,-650,-100);tex.texture=base
 tint=mel.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-650,80);tint.constant=unreal.LinearColor(1.32,1.32,1.32,1)
 mult=mel.create_material_expression(m,unreal.MaterialExpressionMultiply,-390,-80);mel.connect_material_expressions(tex,'RGB',mult,'A');mel.connect_material_expressions(tint,'',mult,'B');mel.connect_material_property(mult,'',unreal.MaterialProperty.MP_BASE_COLOR)
 # Small colour-preservation term prevents black-sky validation and deep shop
 # shadows from destroying the Cairnwell green/yellow separation.
 e_amt=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-650,240);e_amt.r=.035
 em=mel.create_material_expression(m,unreal.MaterialExpressionMultiply,-390,180);mel.connect_material_expressions(tex,'RGB',em,'A');mel.connect_material_expressions(e_amt,'',em,'B');mel.connect_material_property(em,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
 rough=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-180,80);rough.r=.58;mel.connect_material_property(rough,'',unreal.MaterialProperty.MP_ROUGHNESS)
 metal=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-180,150);metal.r=.10;mel.connect_material_property(metal,'',unreal.MaterialProperty.MP_METALLIC)
 mel.recompile_material(m);lib.save_loaded_asset(m,False);rows.append({'station':station,'material':m.get_path_name(),'base_boost':1.32,'roughness':.58,'metallic':.10,'emissive_preservation':.035,'normal_map':'disabled after isolated mismatch'})
after=sha(P)
if after!=before:raise RuntimeError('protected changed')
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_CALIBRATED_MATERIALS__RECAPTURE_REQUIRED','generated_utc':datetime.now(timezone.utc).isoformat(),'records':rows,'protected_v438_before':before,'protected_v438_after':after},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_PR009_PR010_MATERIAL_CALIBRATION_V873_PASS')
