import json,unreal
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir());DEST='/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound';OUT=ROOT/r'Saved\Audits\PressShopIntegration\clean_inbound_material_visibility_v20260809_v006.json';mel=unreal.MaterialEditingLibrary;lib=unreal.EditorAssetLibrary
records=[]
for label,ver in (('Lorry','v006'),('Stand','v005')):
 p=DEST+f'/M_CA_MW_{label}_MeshyPBR_{ver}';m=lib.load_asset(p)
 if not isinstance(m,unreal.Material):raise RuntimeError(p)
 samples=[x for x in mel.get_material_expressions(m) if isinstance(x,unreal.MaterialExpressionTextureSample)]
 base=next((x for x in samples if x.texture and 'BaseColor' in x.texture.get_name()),None)
 if not base:raise RuntimeError(label+' base sample')
 mul=mel.create_material_expression(m,unreal.MaterialExpressionMultiply,-160,-10);strength=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-350,-10);strength.set_editor_property('r',0.08);mel.connect_material_expressions(base,'RGB',mul,'A');mel.connect_material_expressions(strength,'',mul,'B');mel.connect_material_property(mul,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR);mel.recompile_material(m);lib.save_loaded_asset(m,False);records.append({'material':p,'low_emissive_visibility_gain':0.08})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_LOW_EMISSIVE_VISIBILITY_CALIBRATION__VISUAL_REVIEW_REQUIRED','records':records,'reason':'Preserve readable Meshy base colour under the large dark press-hall roof without replacing the PBR texture.','meshy_credits_used':0},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_CLEAN_INBOUND_VISIBILITY_V006_PASS')
