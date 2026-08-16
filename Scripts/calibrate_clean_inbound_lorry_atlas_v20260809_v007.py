import json,unreal
from pathlib import Path
ROOT=Path(unreal.Paths.project_dir());DEST='/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound';MAT=DEST+'/M_CA_MW_Lorry_MeshyPBR_v006';OUT=ROOT/r'Saved\Audits\PressShopIntegration\clean_inbound_lorry_atlas_calibration_v20260809_v007.json';lib=unreal.EditorAssetLibrary;mel=unreal.MaterialEditingLibrary
m=lib.load_asset(MAT)
if not isinstance(m,unreal.Material):raise RuntimeError(MAT)
samples=[x for x in mel.get_material_expressions(m) if isinstance(x,unreal.MaterialExpressionTextureSample)]
base=next((x for x in samples if x.texture and 'BaseColor' in x.texture.get_name()),None)
if not base:raise RuntimeError('base texture sample missing')
# Meshy atlas values are roughly 2 stops darker than the Blender review under
# the same neutral illumination. Apply exposure only; retain all colour/UV detail.
gain=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-350,-190);gain.set_editor_property('r',2.35)
bright=mel.create_material_expression(m,unreal.MaterialExpressionMultiply,-120,-170);mel.connect_material_expressions(base,'RGB',bright,'A');mel.connect_material_expressions(gain,'',bright,'B');mel.connect_material_property(bright,'',unreal.MaterialProperty.MP_BASE_COLOR)
# Replace any prior low emissive link with a restrained contribution from the
# calibrated atlas, preserving readability in the 16.5 m high hall.
emit_gain=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-350,20);emit_gain.set_editor_property('r',0.035)
emit=mel.create_material_expression(m,unreal.MaterialExpressionMultiply,-120,20);mel.connect_material_expressions(bright,'',emit,'A');mel.connect_material_expressions(emit_gain,'',emit,'B');mel.connect_material_property(emit,'',unreal.MaterialProperty.MP_EMISSIVE_COLOR)
mel.recompile_material(m);lib.save_loaded_asset(m,False)
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps({'status':'PASS_ATLAS_EXPOSURE_CALIBRATION__VISUAL_REVIEW_REQUIRED','material':MAT,'base_colour_gain':2.35,'emissive_gain':0.035,'texture_replaced':False,'uvs_changed':False,'meshy_credits_used':0},indent=2),encoding='utf-8');unreal.log('LINE_BOSS_CLEAN_INBOUND_LORRY_ATLAS_V007_PASS')
