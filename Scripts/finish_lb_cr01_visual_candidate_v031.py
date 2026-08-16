"""Create a non-destructive, exposure-stable visual iteration from CR01 v030."""
import json
from pathlib import Path
import unreal

ROOT=Path(unreal.Paths.project_dir())
SOURCE_MAP="/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v030"
MAP="/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_Candidate_v031"
MAT_DIR="/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v031/Materials"
AUDIT=ROOT/"Saved/Audits/lb_cr01_candidate_v031_visual.json"
lib=unreal.EditorAssetLibrary; tools=unreal.AssetToolsHelpers.get_asset_tools(); edit=unreal.MaterialEditingLibrary; factory=unreal.MaterialFactoryNew()
if lib.does_asset_exist(MAP): raise RuntimeError("v031 map already exists; preserve evidence")
if not lib.duplicate_asset(SOURCE_MAP,MAP): raise RuntimeError("Could not duplicate v030 map")
levels=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem); levels.load_level(MAP)

def material(name,colour,metallic,roughness):
    asset=tools.create_asset(f"M_LB_CR01_{name}_v031",MAT_DIR,unreal.Material,factory)
    edit.delete_all_material_expressions(asset)
    base=edit.create_material_expression(asset,unreal.MaterialExpressionConstant3Vector,-400,-20); base.set_editor_property("constant",unreal.LinearColor(*colour,1))
    metal=edit.create_material_expression(asset,unreal.MaterialExpressionConstant,-400,120); metal.set_editor_property("r",metallic)
    rough=edit.create_material_expression(asset,unreal.MaterialExpressionConstant,-400,210); rough.set_editor_property("r",roughness)
    edit.connect_material_property(base,"",unreal.MaterialProperty.MP_BASE_COLOR); edit.connect_material_property(metal,"",unreal.MaterialProperty.MP_METALLIC); edit.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS)
    edit.recompile_material(asset); lib.save_loaded_asset(asset,only_if_is_dirty=False); return asset

mats={
 "BodyCharcoal":material("BodyCharcoal",(0.032,0.042,0.050),0.32,0.62),
 "FrameAnthracite":material("FrameAnthracite",(0.014,0.020,0.025),0.48,0.60),
 "SafetyYellow":material("SafetyYellow",(0.54,0.22,0.006),0.28,0.54),
 "BrushedSteel":material("BrushedSteel",(0.18,0.20,0.22),0.70,0.48),
 "RubberBlack":material("RubberBlack",(0.008,0.010,0.011),0.02,0.86),
 "Floor":material("Floor",(0.055,0.052,0.048),0.0,0.94),
}
def classify(name):
    lower=name.lower()
    for key in ("BodyCharcoal","FrameAnthracite","SafetyYellow","BrushedSteel","RubberBlack"):
        if key.lower() in lower: return key
    return None

overrides=0
for actor in actors.get_all_level_actors():
    label=actor.get_actor_label()
    if label=="LB_CR01_V030_ValidationFloor": actor.set_actor_label("LB_CR01_V031_ValidationFloor"); actor.get_editor_property("static_mesh_component").set_material(0,mats["Floor"]); continue
    component=actor.get_component_by_class(unreal.StaticMeshComponent)
    if not component: continue
    for index in range(component.get_num_materials()):
        current=component.get_material(index); key=classify(current.get_name() if current else "")
        if key: component.set_material(index,mats[key]); overrides+=1

for actor in actors.get_all_level_actors():
    label=actor.get_actor_label()
    if label=="LB_CR01_V030_KeyLight": actor.set_actor_label("LB_CR01_V031_KeyLight"); actor.get_editor_property("directional_light_component").set_editor_property("intensity",0.40)
    elif label=="LB_CR01_V030_SkyLight": actor.set_actor_label("LB_CR01_V031_SkyLight"); actor.get_editor_property("light_component").set_editor_property("intensity",0.22)
    elif label.startswith("LB_CR01_V030_Fill"):
        actor.set_actor_label(label.replace("V030","V031")); actor.get_editor_property("point_light_component").set_editor_property("intensity",75.0)
    elif label.startswith("LB_CR01_V030_CAM_"): actor.set_actor_label(label.replace("V030","V031"))

pp=actors.spawn_actor_from_class(unreal.PostProcessVolume,unreal.Vector(),unreal.Rotator()); pp.set_actor_label("LB_CR01_V031_ExposureLock"); pp.set_editor_property("unbound",True)
settings=pp.get_editor_property("settings")
settings.set_editor_properties({"override_auto_exposure_method":True,"auto_exposure_method":unreal.AutoExposureMethod.AEM_BASIC,"override_auto_exposure_min_brightness":True,"override_auto_exposure_max_brightness":True,"auto_exposure_min_brightness":1.0,"auto_exposure_max_brightness":1.0,"override_auto_exposure_bias":True,"auto_exposure_bias":-1.2})
pp.set_editor_property("settings",settings)
if not levels.save_current_level(): raise RuntimeError("Could not save v031")
result={"status":"CANDIDATE_NOT_PROMOTED__FRESH_SCREENSHOTS_REQUIRED","source_map":SOURCE_MAP,"map":MAP,"material_override_slots":overrides,"exposure_locked":True,"exposure_bias":-1.2}
AUDIT.parent.mkdir(parents=True,exist_ok=True); AUDIT.write_text(json.dumps(result,indent=2),encoding="utf-8")
unreal.log(f"LINE_BOSS_LB_CR01_V031_VISUAL_BUILD_PASS overrides={overrides}")
