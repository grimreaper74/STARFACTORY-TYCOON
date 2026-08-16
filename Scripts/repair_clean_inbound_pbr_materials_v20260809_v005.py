from pathlib import Path
from datetime import datetime,timezone
import json,unreal
ROOT=Path(unreal.Paths.project_dir()).resolve();DEST='/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound';OUT=ROOT/r'Saved\Audits\PressShopIntegration\clean_inbound_pbr_material_repair_v20260809_v005.json'
lib=unreal.EditorAssetLibrary;tools=unreal.AssetToolsHelpers.get_asset_tools();mel=unreal.MaterialEditingLibrary
jobs=[('Lorry',ROOT/r'SourceAssets\Candidate\PressShop\InboundCoilDelivery\LorryLoadedWrappedCoils_v20260809_v006\Textures','v006',DEST+'/SM_CA_MW_InboundLorry_Approved_v006'),('Stand',ROOT/r'SourceAssets\Candidate\PressShop\InboundCoilDelivery\MeshyAdjustableCoilStand_v20260809_v005\Textures','v005',DEST+'/SM_CA_MW_AdjustableCoilStand_Approved_v005')]
records=[]
for label,src,ver,mesh_path in jobs:
 files={'BaseColor':src/f'T_{label}_BaseColor_{ver}.png','MetalRough':src/f'T_{label}_MetalRough_{ver}.png','Normal':src/f'T_{label}_Normal_{ver}.png'};tasks=[]
 for role,f in files.items():
  t=unreal.AssetImportTask();t.set_editor_properties({'filename':str(f),'destination_path':DEST,'destination_name':f.stem,'automated':True,'replace_existing':True,'replace_existing_settings':True,'save':True});tasks.append(t)
 tools.import_asset_tasks(tasks);unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
 tex={k:lib.load_asset(DEST+'/'+v.stem) for k,v in files.items()}
 if not all(tex.values()):raise RuntimeError(label+' texture import')
 for role in ('MetalRough','Normal'):tex[role].set_editor_property('srgb',False)
 tex['Normal'].set_editor_property('compression_settings',unreal.TextureCompressionSettings.TC_NORMALMAP)
 for x in tex.values():lib.save_loaded_asset(x,False)
 mat_path=DEST+f'/M_CA_MW_{label}_MeshyPBR_{ver}'
 if lib.does_asset_exist(mat_path):lib.delete_asset(mat_path)
 mat=tools.create_asset(mat_path.rsplit('/',1)[1],DEST,unreal.Material,unreal.MaterialFactoryNew())
 bc=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-500,-100);bc.texture=tex['BaseColor'];mr=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-500,120);mr.texture=tex['MetalRough'];no=mel.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-500,340);no.texture=tex['Normal'];no.sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
 mel.connect_material_property(bc,'RGB',unreal.MaterialProperty.MP_BASE_COLOR);mel.connect_material_property(mr,'B',unreal.MaterialProperty.MP_METALLIC);mel.connect_material_property(mr,'G',unreal.MaterialProperty.MP_ROUGHNESS);mel.connect_material_property(no,'RGB',unreal.MaterialProperty.MP_NORMAL);mel.recompile_material(mat);lib.save_loaded_asset(mat,False)
 mesh=lib.load_asset(mesh_path)
 if not isinstance(mesh,unreal.StaticMesh):raise RuntimeError(mesh_path)
 mesh.set_material(0,mat);lib.save_loaded_asset(mesh,False);records.append({'mesh':mesh_path,'material':mat_path,'textures':{k:DEST+'/'+v.stem for k,v in files.items()}})
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_PBR_REBIND__VISUAL_REVIEW_REQUIRED','generated_utc':datetime.now(timezone.utc).isoformat(),'records':records,'meshy_credits_used':0},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_CLEAN_INBOUND_PBR_REPAIR_V005_PASS')
