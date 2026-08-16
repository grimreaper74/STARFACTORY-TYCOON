"""Create and bind controlled PBR materials for isolated inbound candidate v001."""
from pathlib import Path
import json, unreal
DEST="/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001"
MAT=DEST+"/Materials_v001"
OUT=Path(unreal.Paths.project_saved_dir())/"Audits/PressShopIntegration/inbound_candidate_materials_v491.json"
library=unreal.EditorAssetLibrary; tools=unreal.AssetToolsHelpers.get_asset_tools(); mel=unreal.MaterialEditingLibrary
SPECS={
 "MI_CA_Inbound_Charcoal":((0.018,0.024,0.028),0.38,0.72,None),
 "MI_CA_Inbound_CairnwellGreen":((0.025,0.19,0.12),0.36,0.54,None),
 "MI_CA_Inbound_BrushedSteel":((0.48,0.54,0.59),0.24,0.92,None),
 "MI_CA_Inbound_SafetyYellow":((0.95,0.48,0.015),0.34,0.16,None),
 "MI_CA_Inbound_Rubber":((0.006,0.008,0.010),0.82,0.0,None),
 "MI_CA_Inbound_Glass":((0.012,0.055,0.070),0.13,0.18,(0.005,0.025,0.035)),
 "MI_CA_Inbound_White":((0.72,0.76,0.73),0.45,0.04,None),
 "MI_CA_Inbound_Red":((0.70,0.018,0.010),0.28,0.02,(1.5,0.02,0.01)),
 "MI_CA_Inbound_Amber":((1.0,0.22,0.005),0.22,0.02,(2.8,0.35,0.005)),
 "MI_CA_Inbound_GreenLamp":((0.008,0.46,0.08),0.20,0.02,(0.01,2.3,0.12)),
}
created=[]; mats={}
for name,(colour,roughness,metallic,emission) in SPECS.items():
    path=f"{MAT}/{name}_v001"
    if library.does_asset_exist(path): raise RuntimeError(f"Refusing overwrite: {path}")
    m=tools.create_asset(name+"_v001",MAT,unreal.Material,unreal.MaterialFactoryNew())
    base=mel.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-420,0); base.set_editor_property("constant",unreal.LinearColor(*colour,1))
    rough=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-420,140); rough.set_editor_property("r",roughness)
    metal=mel.create_material_expression(m,unreal.MaterialExpressionConstant,-420,250); metal.set_editor_property("r",metallic)
    mel.connect_material_property(base,"",unreal.MaterialProperty.MP_BASE_COLOR); mel.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS); mel.connect_material_property(metal,"",unreal.MaterialProperty.MP_METALLIC)
    if emission:
        emit=mel.create_material_expression(m,unreal.MaterialExpressionConstant3Vector,-420,370); emit.set_editor_property("constant",unreal.LinearColor(*emission,1)); mel.connect_material_property(emit,"",unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(m); library.save_loaded_asset(m,only_if_is_dirty=False); mats[name]=m; created.append(path)

bound={}
for path in library.list_assets(DEST,recursive=False,include_folder=False):
    mesh=library.load_asset(path)
    if not isinstance(mesh,unreal.StaticMesh): continue
    names=[]
    for index,slot in enumerate(mesh.get_editor_property("static_materials")):
        slotname=str(slot.get_editor_property("material_slot_name"))
        if slotname not in mats: raise RuntimeError(f"Unknown inbound material slot {slotname} on {path}")
        mesh.set_material(index,mats[slotname]); names.append(slotname)
    library.save_loaded_asset(mesh,only_if_is_dirty=False); bound[path]=names
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps({"status":"PASS_ISOLATED_CANDIDATE_NOT_PROMOTED","created":created,"bound":bound},indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_MATERIALS_V491_PASS "+str(OUT))
