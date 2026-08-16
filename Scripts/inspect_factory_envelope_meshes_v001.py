import json
import os
import unreal

PROJECT = unreal.Paths.project_dir().replace('\\', '/')
OUT = os.path.join(PROJECT, 'Saved', 'Audits', 'VisualTuning', 'factory_envelope_mesh_bounds_v001.json')
ASSETS = [
    '/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Column_02.SM_Column_02',
    '/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_MetalBeam01.SM_MetalBeam01',
    '/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_CableSet_01.SM_CableSet_01',
    '/Game/LineBoss/Vendor/FactoryEnvironment/Meshes/SM_Lamp01.SM_Lamp01',
    '/Game/LineBoss/IndustrialKit/PressShop/FrontEndDressing/SM_LB_ServiceCabinet_1800_v001.SM_LB_ServiceCabinet_1800_v001',
]
rows=[]
for path in ASSETS:
    mesh=unreal.load_asset(path)
    if not mesh:
        raise RuntimeError('missing '+path)
    b=mesh.get_bounds()
    rows.append({'path':path,'dimensions_cm':[b.box_extent.x*2,b.box_extent.y*2,b.box_extent.z*2],'materials':[s.material_interface.get_path_name() if s.material_interface else None for s in mesh.get_editor_property('static_materials')]})
os.makedirs(os.path.dirname(OUT),exist_ok=True)
with open(OUT,'w',encoding='utf-8') as h: json.dump(rows,h,indent=2)
unreal.log('LINE_BOSS_ENVELOPE_MESHES '+json.dumps(rows))
