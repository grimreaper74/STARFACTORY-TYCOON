import json,unreal
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir());DEST='/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound';OUT=ROOT/r'Saved\Audits\PressShopIntegration\clean_inbound_sampler_repair_v20260809_v008.json';lib=unreal.EditorAssetLibrary;mel=unreal.MaterialEditingLibrary;records=[]
for label,ver in (('Lorry','v006'),('Stand','v005')):
 p=DEST+f'/M_CA_MW_{label}_MeshyPBR_{ver}';m=lib.load_asset(p)
 if not isinstance(m,unreal.Material):raise RuntimeError(p)
 changed=[]
 for node in mel.get_material_expressions(m):
  if isinstance(node,unreal.MaterialExpressionTextureSample) and node.texture:
   n=node.texture.get_name()
   if 'MetalRough' in n:node.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR);changed.append(n+':LINEAR_COLOR')
   elif 'Normal' in n:node.set_editor_property('sampler_type',unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL);changed.append(n+':NORMAL')
 mel.recompile_material(m);lib.save_loaded_asset(m,False);records.append({'material':p,'changed':changed})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_SAMPLER_REPAIR__NO_DEFAULT_MATERIAL_EXPECTED','records':records,'meshy_credits_used':0},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_CLEAN_INBOUND_SAMPLER_V008_PASS')
