import json
import os
import unreal

PROJECT = unreal.Paths.project_dir().replace('\\', '/')
ASSET_PATH = '/Game/LineBoss/Candidates/WeldShop/PanelStillageRuntime_v001/SM_LB_PanelStillage_Runtime_v001.SM_LB_PanelStillage_Runtime_v001'
RECEIPT = os.path.join(PROJECT, 'Saved', 'Audits', 'WeldShop', 'PanelStillageRuntime_v001', 'validation_receipt_v001.json')

mesh = unreal.load_asset(ASSET_PATH)
if not mesh:
    raise RuntimeError('Missing stillage mesh: {}'.format(ASSET_PATH))

materials = []
for slot in mesh.get_editor_property('static_materials'):
    interface = slot.material_interface
    materials.append(interface.get_path_name() if interface else None)

bounds = mesh.get_bounds()
payload = {
    'status': 'PASS' if materials and all(materials) and mesh.get_num_lods() == 1 else 'FAIL',
    'asset': ASSET_PATH,
    'lods': mesh.get_num_lods(),
    'materials': materials,
    'bounds_cm': {
        'x': bounds.box_extent.x * 2.0,
        'y': bounds.box_extent.y * 2.0,
        'z': bounds.box_extent.z * 2.0,
    },
    'nanite_enabled': bool(mesh.get_editor_property('nanite_settings').enabled),
}
os.makedirs(os.path.dirname(RECEIPT), exist_ok=True)
with open(RECEIPT, 'w', encoding='utf-8') as handle:
    json.dump(payload, handle, indent=2, sort_keys=True)
if payload['status'] != 'PASS':
    raise RuntimeError('Panel stillage asset failed validation: {}'.format(payload))
unreal.log('LINE_BOSS_PANEL_STILLAGE_VALIDATION PASS {}'.format(json.dumps(payload)))
