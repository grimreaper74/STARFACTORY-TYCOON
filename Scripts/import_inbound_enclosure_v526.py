"""Isolated Unreal intake for additive inbound installed enclosure v001."""
from pathlib import Path
import hashlib, json
import unreal

project=Path(unreal.Paths.project_dir())
source=project/'SourceAssets/Candidate/PressShop/InboundCoilDelivery/Enclosure_v001/SM_CA_MW_Inbound_InstalledEnclosure_v001.fbx'
dest='/Game/LineBoss/IndustrialKit/InboundCoilDelivery/EnclosureCandidate_v001'
name='SM_CA_MW_Inbound_InstalledEnclosure_v001'
if not source.exists(): raise RuntimeError(f'Missing enclosure FBX {source}')

task=unreal.AssetImportTask()
task.set_editor_properties({'filename':str(source),'destination_path':dest,'destination_name':name,
    'automated':True,'replace_existing':True,'save':True})
options=unreal.FbxImportUI()
options.set_editor_properties({'import_mesh':True,'import_as_skeletal':False,'import_materials':True,
    'import_textures':False,'create_physics_asset':False,'automated_import_should_detect_type':False})
options.static_mesh_import_data.set_editor_properties({'combine_meshes':True,'generate_lightmap_u_vs':True,
    'auto_generate_collision':True,'convert_scene':True,'convert_scene_unit':True})
task.options=options
unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
asset_path=f'{dest}/{name}'
mesh=unreal.EditorAssetLibrary.load_asset(asset_path)
if not isinstance(mesh,unreal.StaticMesh): raise RuntimeError(f'Enclosure import failed {asset_path}')
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
size=mesh.get_bounds().box_extent*2
bounds=[float(size.x),float(size.y),float(size.z)]
gates=((790,840),(610,690),(300,360))
for axis,value,gate in zip('XYZ',bounds,gates):
    if not gate[0] <= value <= gate[1]: raise RuntimeError(f'Enclosure {axis}={value:.2f} outside {gate}')
slots=len(mesh.get_editor_property('static_materials'))
if slots < 4: raise RuntimeError(f'Enclosure material separation lost: {slots} slots')
unreal.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False)
audit=project/'Saved/Audits/PressShopIntegration/inbound_enclosure_import_v526.json'
audit.parent.mkdir(parents=True,exist_ok=True)
audit.write_text(json.dumps({'status':'PASS__TECHNICAL_INTAKE_ONLY__NOT_PROMOTED','asset':asset_path,
    'bounds_cm':[round(v,3) for v in bounds],'material_slots':slots,
    'has_body_setup':mesh.get_editor_property('body_setup') is not None,
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'engineering_values':'TBC'},indent=2),encoding='utf-8')
unreal.log('LINE_BOSS_INBOUND_ENCLOSURE_V526_IMPORT_PASS')
